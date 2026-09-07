"""
RetainIQ - Cross-User Dataset Ownership Security Tests

Run:
    python -m pytest tests/security.py -v

These tests use the real Flask application and MySQL database.
They create temporary test users/datasets and clean them up afterward.
"""

import uuid

import pytest

from app import app
from scripts.database import (
    create_user,
    create_dataset,
    get_dataset,
    get_all_datasets,
    get_customers_by_dataset,
    get_connection,
)


@pytest.fixture(scope="module")
def test_data():
    suffix = uuid.uuid4().hex[:12]

    user_a_email = f"security_a_{suffix}@test.local"
    user_b_email = f"security_b_{suffix}@test.local"

    user_a = create_user(
        f"Security Test A {suffix}",
        user_a_email,
        "SecurityTestHashA"
    )
    user_b = create_user(
        f"Security Test B {suffix}",
        user_b_email,
        "SecurityTestHashB"
    )

    assert user_a
    assert user_b

    dataset_a = create_dataset(
        dataset_name=f"Security Test Dataset {suffix}",
        source_type="UPLOAD",
        original_filename="security_test.csv",
        file_hash=uuid.uuid4().hex * 2,
        user_id=user_a
    )

    assert dataset_a

    yield {
        "user_a": user_a,
        "user_b": user_b,
        "dataset_a": dataset_a,
        "email_a": user_a_email,
        "email_b": user_b_email,
    }

    # Cleanup all test rows.
    connection = get_connection()

    if connection:
        cursor = connection.cursor()

        try:
            cursor.execute(
                "DELETE FROM users WHERE id IN (%s, %s)",
                (user_a, user_b)
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        yield client


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = int(user_id)
        session["user_name"] = "Security Test User"
        session["user_email"] = f"security_{user_id}@test.local"


def test_owner_can_access_own_dataset(test_data):
    dataset = get_dataset(
        test_data["dataset_a"],
        test_data["user_a"]
    )

    assert dataset is not None
    assert dataset["id"] == test_data["dataset_a"]
    assert dataset["user_id"] == test_data["user_a"]


def test_other_user_cannot_access_dataset(test_data):
    dataset = get_dataset(
        test_data["dataset_a"],
        test_data["user_b"]
    )

    assert dataset is None


def test_dataset_list_is_user_scoped(test_data):
    owner_datasets = get_all_datasets(test_data["user_a"])
    other_user_datasets = get_all_datasets(test_data["user_b"])

    owner_ids = {row["id"] for row in owner_datasets}
    other_ids = {row["id"] for row in other_user_datasets}

    assert test_data["dataset_a"] in owner_ids
    assert test_data["dataset_a"] not in other_ids


def test_customer_query_is_user_scoped(test_data):
    owner_customers = get_customers_by_dataset(
        test_data["dataset_a"],
        test_data["user_a"]
    )
    other_customers = get_customers_by_dataset(
        test_data["dataset_a"],
        test_data["user_b"]
    )

    # The test dataset has no customer rows, but both calls must
    # remain valid and the non-owner must not receive anything.
    assert isinstance(owner_customers, list)
    assert isinstance(other_customers, list)
    assert other_customers == []


def test_dataset_endpoint_owner_access(client, test_data):
    login_as(client, test_data["user_a"])

    response = client.get(
        f"/datasets/{test_data['dataset_a']}"
    )

    assert response.status_code == 200

    body = response.get_json()
    assert body["success"] is True
    assert body["dataset"]["id"] == test_data["dataset_a"]


def test_dataset_endpoint_blocks_other_user(client, test_data):
    login_as(client, test_data["user_b"])

    response = client.get(
        f"/datasets/{test_data['dataset_a']}"
    )

    assert response.status_code == 404

    body = response.get_json()
    assert body["success"] is False


def test_customers_endpoint_blocks_other_user_dataset(client, test_data):
    login_as(client, test_data["user_b"])

    response = client.get(
        f"/customers/data?dataset_id={test_data['dataset_a']}"
    )

    assert response.status_code == 200

    body = response.get_json()
    assert body["success"] is True
    assert body["customers"] == []


def test_datasets_endpoint_only_returns_owner_datasets(client, test_data):
    login_as(client, test_data["user_b"])

    response = client.get("/datasets")

    assert response.status_code == 200

    body = response.get_json()
    assert body["success"] is True

    returned_ids = {
        dataset["id"]
        for dataset in body["datasets"]
    }

    assert test_data["dataset_a"] not in returned_ids
