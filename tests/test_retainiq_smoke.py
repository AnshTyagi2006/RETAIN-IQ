"""
RetainIQ - Final Smoke Test Suite

Run from the RetainIQ project root:

    python -m pytest tests/test_retainiq_smoke.py -v

These tests are intentionally non-destructive.
They do not create, update, or delete customer records.
"""

import io
import pandas as pd
import pytest


# Import the Flask app.
# The local project must have its normal dependencies installed.
from app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def login_session(client, user_id=1):
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["user_name"] = "Test User"
        session["user_email"] = "test@example.com"


# ============================================================
# AUTH / ACCESS CONTROL
# ============================================================

def test_home_is_public(client):
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "route",
    [
        "/dashboard",
        "/manual",
        "/upload",
        "/sample",
        "/bulk_dashboard",
        "/customers",
        "/customer",
    ],
)
def test_protected_pages_require_login(client, route):
    response = client.get(route)
    assert response.status_code in (302, 303)


@pytest.mark.parametrize(
    "route, method",
    [
        ("/predict", "post"),
        ("/analyze", "post"),
        ("/sample-data", "get"),
        ("/explain-customer", "post"),
        ("/customers/data", "get"),
        ("/datasets", "get"),
    ],
)
def test_protected_apis_require_login(client, route, method):
    # Use the endpoint's actual HTTP method. Otherwise Flask can return
    # 405 Method Not Allowed before the protected route is executed.
    if method == "post":
        response = client.post(route)
    else:
        response = client.get(route)

    assert response.status_code == 401


def test_auth_me_without_login(client):
    response = client.get("/auth/me")

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["authenticated"] is False


def test_invalid_login_is_rejected(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "invalid@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code in (401, 500)

    data = response.get_json()

    assert data["success"] is False


# ============================================================
# AUTHENTICATED ROUTES
# ============================================================

def test_authenticated_pages_are_reachable(client):
    login_session(client)

    for route in [
        "/dashboard",
        "/manual",
        "/upload",
        "/sample",
        "/bulk_dashboard",
        "/customers",
        "/customer",
    ]:
        response = client.get(route)
        assert response.status_code == 200, route


def test_authenticated_customer_api_is_reachable(client):
    login_session(client)

    response = client.get("/customers/data")

    assert response.status_code in (200, 400)

    data = response.get_json()

    assert isinstance(data, dict)
    assert "success" in data


# ============================================================
# JSON SERIALIZATION
# ============================================================

def test_make_json_safe_handles_pandas_values():
    from app import make_json_safe

    frame = pd.DataFrame(
        [
            {
                "count": 3,
                "probability": 0.75,
            }
        ]
    )

    result = make_json_safe(frame)

    assert isinstance(result, list)
    assert result[0]["count"] == 3
    assert result[0]["probability"] == 0.75


# ============================================================
# GLOBAL BUSINESS ANALYTICS
# ============================================================

def test_global_analytics_segments():
    from scripts.global_analytics import get_global_report

    predictions = pd.DataFrame(
        [
            {
                "tenure": 3,
                "satisfaction_score": 1,
                "complain": 1,
                "preferred_order_category": "Laptop & Accessory",
                "churn_probability": 0.90,
                "prediction": 1,
                "risk_level": "High Risk",
            },
            {
                "tenure": 15,
                "satisfaction_score": 4,
                "complain": 0,
                "preferred_order_category": "Mobile Phone",
                "churn_probability": 0.20,
                "prediction": 0,
                "risk_level": "Low Risk",
            },
        ]
    )

    report = get_global_report(predictions)

    assert report["total_customers"] == 2
    assert "segments" in report
    assert "satisfaction" in report["segments"]
    assert "complaint" in report["segments"]
    assert "tenure" in report["segments"]
    assert "order_category" in report["segments"]

    assert len(report["segments"]["satisfaction"]) > 0
    assert len(report["segments"]["complaint"]) > 0
    assert len(report["segments"]["tenure"]) > 0
    assert len(report["segments"]["order_category"]) > 0

    assert isinstance(
        report["business_insights"],
        list,
    )


# ============================================================
# RETENTION ENGINE
# ============================================================

def test_retention_engine_returns_action():
    from scripts.retention_engine import generate_retention_action

    customer = {
        "satisfaction_score": 1,
        "complain": 1,
        "days_since_last_order": 40,
    }

    action = generate_retention_action(
        customer,
        "High Risk",
    )

    assert isinstance(action, dict)
    assert action.get("action")
    assert action.get("priority")


# ============================================================
# ROUTE REGISTRATION
# ============================================================

def test_core_routes_exist():
    routes = {
        rule.rule
        for rule in app.url_map.iter_rules()
    }

    expected = {
        "/",
        "/dashboard",
        "/manual",
        "/upload",
        "/sample",
        "/bulk_dashboard",
        "/customers",
        "/customer",
        "/predict",
        "/analyze",
        "/sample-data",
        "/customers/data",
        "/explain-customer",
        "/auth/login",
        "/auth/register",
        "/auth/logout",
        "/auth/me",
    }

    missing = expected - routes

    assert not missing, (
        "Missing RetainIQ routes: "
        + ", ".join(sorted(missing))
    )
