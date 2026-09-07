# ============================================================
# RETAIN IQ - MYSQL DATABASE
# ============================================================

import mysql.connector
from mysql.connector import Error


import os
import logging

logger = logging.getLogger(__name__)

# Supports both local development variables (DB_*) and
# Railway's native MySQL variables (MYSQL*).
DB_CONFIG = {
    "host": os.environ.get(
        "DB_HOST",
        os.environ.get("MYSQLHOST", "localhost")
    ),
    "port": int(os.environ.get(
        "DB_PORT",
        os.environ.get("MYSQLPORT", "3306")
    )),
    "user": os.environ.get(
        "DB_USER",
        os.environ.get("MYSQLUSER", "root")
    ),
    "password": os.environ.get(
        "DB_PASSWORD",
        os.environ.get("MYSQLPASSWORD", "mysql")
    ),
    "database": os.environ.get(
        "DB_NAME",
        os.environ.get("MYSQLDATABASE", "retainiq")
    )
}


# ============================================================
# CONNECTION
# ============================================================

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            port=DB_CONFIG["port"]
        )

        if connection.is_connected():
            return connection

    except Error as e:
        logger.exception("MySQL connection error")

    return None


def test_connection():
    connection = get_connection()

    if connection:
        logger.info("MySQL connection successful.")
        connection.close()
        return True

    logger.warning("MySQL connection failed.")
    return False


# ============================================================
# USER AUTHENTICATION
# ============================================================

def ensure_users_table():
    """Create the authentication table if it does not exist."""
    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL DEFAULT NULL
            ) ENGINE=InnoDB
        """)

        connection.commit()
        return True

    except Error as e:
        connection.rollback()
        logger.exception("Users table error")
        return False

    finally:
        cursor.close()
        connection.close()


def create_user(name, email, password_hash):
    """Create a user and return the new user ID, or None on failure."""
    connection = get_connection()

    if not connection:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
        """, (name, email, password_hash))

        connection.commit()
        return cursor.lastrowid

    except Error as e:
        connection.rollback()
        logger.exception("User creation error")
        return None

    finally:
        cursor.close()
        connection.close()


def get_user_by_email(email):
    """Return one user by normalized email."""
    connection = get_connection()

    if not connection:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                name,
                email,
                password_hash,
                created_at,
                last_login
            FROM users
            WHERE email = %s
            LIMIT 1
        """, (email,))

        return cursor.fetchone()

    except Error as e:
        logger.exception("User lookup error")
        return None

    finally:
        cursor.close()
        connection.close()


def get_user_by_id(user_id):
    """Return a user without exposing the password hash."""
    connection = get_connection()

    if not connection:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                name,
                email,
                created_at,
                last_login
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))

        return cursor.fetchone()

    except Error as e:
        logger.exception("User ID lookup error")
        return None

    finally:
        cursor.close()
        connection.close()


def update_user_last_login(user_id):
    """Update the last successful login timestamp."""
    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (user_id,))

        connection.commit()
        return True

    except Error as e:
        connection.rollback()
        logger.exception("Last login update error")
        return False

    finally:
        cursor.close()
        connection.close()



# ============================================================
# DATASET OWNERSHIP SCHEMA
# ============================================================

def ensure_dataset_ownership_schema():
    """Add per-user dataset ownership and user-scoped upload reuse."""
    connection = get_connection()
    if not connection:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'datasets'
              AND COLUMN_NAME = 'user_id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE datasets ADD COLUMN user_id INT NULL
            """)

        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'datasets'
              AND INDEX_NAME = 'idx_datasets_user_id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE datasets
                ADD INDEX idx_datasets_user_id (user_id)
            """)

        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'datasets'
              AND INDEX_NAME = 'uq_datasets_file_hash'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                ALTER TABLE datasets DROP INDEX uq_datasets_file_hash
            """)

        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'datasets'
              AND INDEX_NAME = 'uq_datasets_user_file_hash'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE datasets
                ADD UNIQUE INDEX uq_datasets_user_file_hash
                (user_id, file_hash)
            """)

        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE CONSTRAINT_SCHEMA = DATABASE()
              AND TABLE_NAME = 'datasets'
              AND COLUMN_NAME = 'user_id'
              AND REFERENCED_TABLE_NAME = 'users'
              AND REFERENCED_COLUMN_NAME = 'id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE datasets
                ADD CONSTRAINT fk_datasets_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE ON UPDATE CASCADE
            """)

        connection.commit()
        return True

    except Error as e:
        connection.rollback()
        logger.exception("Dataset ownership schema error")
        return False

    finally:
        cursor.close()
        connection.close()


# ============================================================
# RETENTION INTELLIGENCE SCHEMA
# ============================================================

def ensure_retention_columns():
    connection = get_connection()
    if not connection:
        return False

    cursor = connection.cursor()
    columns = {
        "retention_action": "TEXT NULL",
        "retention_priority": "VARCHAR(30) NULL",
        "retention_reason": "TEXT NULL",
        "retention_recommendation": "TEXT NULL"
    }

    try:
        for column, definition in columns.items():
            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'predictions'
                  AND COLUMN_NAME = %s
            """, (column,))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    f"ALTER TABLE predictions ADD COLUMN {column} {definition}"
                )

        connection.commit()
        return True
    except Error as e:
        connection.rollback()
        logger.exception("Retention schema error")
        return False
    finally:
        cursor.close()
        connection.close()


# ============================================================
# DATASET MANAGEMENT
# ============================================================

def create_dataset(
    dataset_name,
    source_type,
    original_filename=None,
    file_hash=None,
    user_id=None
):
    """
    Create a dataset.

    For UPLOAD datasets:
    - If the same file hash already exists, reuse its dataset_id.
    - Otherwise create a new dataset.

    MANUAL datasets always create a new dataset.
    """

    connection = get_connection()

    if not connection:
        return None

    if user_id is None:
        connection.close()
        logger.warning("Dataset creation rejected: user_id is required.")
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        # ----------------------------------------------------
        # REUSE EXISTING UPLOAD DATASET
        # ----------------------------------------------------

        if (
            source_type == "UPLOAD"
            and file_hash
        ):
            cursor.execute(
                """
                SELECT id
                FROM datasets
                WHERE user_id = %s
                  AND file_hash = %s
                LIMIT 1
                """,
                (user_id, file_hash)
            )

            existing = cursor.fetchone()

            if existing:
                logger.info("Existing dataset reused: %s", existing["id"])

                return existing["id"]

        # ----------------------------------------------------
        # CREATE NEW DATASET
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO datasets (
                user_id,
                dataset_name,
                source_type,
                original_filename,
                file_hash
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                dataset_name,
                source_type,
                original_filename,
                file_hash
            )
        )

        connection.commit()

        dataset_id = cursor.lastrowid

        logger.info("New dataset created: %s", dataset_id)

        return dataset_id

    except Error as e:
        connection.rollback()

        logger.exception("Dataset save error")

        # ----------------------------------------------------
        # HANDLE UNIQUE HASH RACE SAFELY
        # ----------------------------------------------------

        if (
            source_type == "UPLOAD"
            and file_hash
        ):
            try:
                cursor.execute(
                    """
                    SELECT id
                    FROM datasets
                    WHERE user_id = %s
                      AND file_hash = %s
                    LIMIT 1
                    """,
                    (user_id, file_hash)
                )

                existing = cursor.fetchone()

                if existing:
                    return existing["id"]

            except Error:
                pass

        return None

    finally:
        cursor.close()
        connection.close()


def get_dataset(dataset_id, user_id):
    connection = get_connection()
    if not connection:
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, user_id, dataset_name, source_type,
                   original_filename, file_hash, created_at
            FROM datasets
            WHERE id = %s AND user_id = %s
        """, (dataset_id, user_id))
        return cursor.fetchone()
    except Error as e:
        logger.exception("Dataset retrieval error")
        return None
    finally:
        cursor.close()
        connection.close()


def get_all_datasets(user_id):
    connection = get_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, user_id, dataset_name, source_type,
                   original_filename, created_at
            FROM datasets
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        return cursor.fetchall()
    except Error as e:
        logger.exception("Dataset list error")
        return []
    finally:
        cursor.close()
        connection.close()


def get_dataset_history(user_id):
    connection = get_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT d.id, d.user_id, d.dataset_name, d.source_type,
                   d.original_filename, d.file_hash, d.created_at,
                   COUNT(DISTINCT c.id) AS customer_count,
                   COUNT(DISTINCT p.id) AS prediction_count,
                   COUNT(DISTINCT e.id) AS explanation_count
            FROM datasets d
            LEFT JOIN customers c ON c.dataset_id = d.id
            LEFT JOIN predictions p ON p.dataset_id = d.id
            LEFT JOIN customer_explanations e ON e.dataset_id = d.id
            WHERE d.user_id = %s
            GROUP BY d.id, d.user_id, d.dataset_name, d.source_type,
                     d.original_filename, d.file_hash, d.created_at
            ORDER BY d.created_at DESC
        """, (user_id,))
        return cursor.fetchall()
    except Error as e:
        logger.exception("Dataset history error")
        return []
    finally:
        cursor.close()
        connection.close()


# ============================================================
# SAVE COMPLETE CUSTOMER ANALYSIS
# ============================================================

def save_customer_analysis(
    customer,
    result,
    dataset_id,
    user_id
):
    """
    Save/update one customer, prediction and SHAP explanations.

    Re-running the same dataset is idempotent:
    - customer is updated
    - old prediction is replaced
    - old explanations are replaced
    """

    customer_id = (
        customer.get("CustomerID")
        or customer.get("customer_id")
        or customer.get("customer_index")
    )

    if customer_id is None:
        return False

    if dataset_id is None:
        return False

    customer_id = str(customer_id)

    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:
        # ----------------------------------------------------
        # VERIFY DATASET OWNERSHIP
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id FROM datasets
            WHERE id = %s AND user_id = %s
            LIMIT 1
        """, (dataset_id, user_id))

        if not cursor.fetchone():
            logger.warning("Customer analysis save rejected: dataset does not belong to user.")
            connection.rollback()
            return False

        # ----------------------------------------------------
        # CUSTOMER
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO customers (
                dataset_id,
                customer_id,
                tenure,
                city_tier,
                order_count,
                days_since_last_order,
                cashback_amount,
                satisfaction_score,
                preferred_order_category,
                preferred_payment_mode,
                preferred_login_device,
                gender,
                marital_status,
                complain
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                tenure = VALUES(tenure),
                city_tier = VALUES(city_tier),
                order_count = VALUES(order_count),
                days_since_last_order =
                    VALUES(days_since_last_order),
                cashback_amount =
                    VALUES(cashback_amount),
                satisfaction_score =
                    VALUES(satisfaction_score),
                preferred_order_category =
                    VALUES(preferred_order_category),
                preferred_payment_mode =
                    VALUES(preferred_payment_mode),
                preferred_login_device =
                    VALUES(preferred_login_device),
                gender = VALUES(gender),
                marital_status =
                    VALUES(marital_status),
                complain = VALUES(complain)
            """,
            (
                dataset_id,
                customer_id,
                customer.get("tenure"),
                customer.get("city_tier"),
                customer.get("order_count"),
                customer.get("days_since_last_order"),
                customer.get("cashback_amount"),
                customer.get("satisfaction_score"),
                customer.get("preferred_order_category"),
                customer.get("preferred_payment_mode"),
                customer.get("preferred_login_device"),
                customer.get("gender"),
                customer.get("marital_status"),
                customer.get("complain")
            )
        )

        # ----------------------------------------------------
        # REMOVE OLD PREDICTION
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM predictions
            WHERE dataset_id = %s
              AND customer_id = %s
            """,
            (
                dataset_id,
                customer_id
            )
        )

        # ----------------------------------------------------
        # SAVE CURRENT PREDICTION
        # ----------------------------------------------------

        probability = result.get(
            "probability",
            result.get(
                "churn_probability",
                0
            )
        )

        retention_action = result.get("retention_action", {}) or {}

        cursor.execute(
            """
            INSERT INTO predictions (
                dataset_id,
                customer_id,
                churn_probability,
                prediction,
                risk_level,
                recommendation,
                retention_action,
                retention_priority,
                retention_reason,
                retention_recommendation
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                dataset_id,
                customer_id,
                float(probability),
                int(result.get("prediction", 0)),
                result.get("risk_level", "Unknown"),
                result.get(
                    "recommendation",
                    retention_action.get("recommendation", "")
                ),
                retention_action.get("action", ""),
                retention_action.get("priority", ""),
                retention_action.get("reason", ""),
                retention_action.get("recommendation", "")
            )
        )

        # ----------------------------------------------------
        # REMOVE OLD EXPLANATIONS
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM customer_explanations
            WHERE dataset_id = %s
              AND customer_id = %s
            """,
            (
                dataset_id,
                customer_id
            )
        )

        # ----------------------------------------------------
        # PREPARE SHAP EXPLANATIONS
        # ----------------------------------------------------

        explanation_rows = []

        for factor in result.get(
            "risk_factors",
            []
        ):
            if isinstance(factor, dict):
                explanation_rows.append(
                    (
                        dataset_id,
                        customer_id,
                        str(
                            factor.get(
                                "feature",
                                "Unknown"
                            )
                        ),
                        str(
                            factor.get(
                                "value",
                                ""
                            )
                        ),
                        float(
                            factor.get(
                                "impact",
                                0
                            )
                        ),
                        "risk"
                    )
                )

        for factor in result.get(
            "protective_factors",
            []
        ):
            if isinstance(factor, dict):
                explanation_rows.append(
                    (
                        dataset_id,
                        customer_id,
                        str(
                            factor.get(
                                "feature",
                                "Unknown"
                            )
                        ),
                        str(
                            factor.get(
                                "value",
                                ""
                            )
                        ),
                        float(
                            factor.get(
                                "impact",
                                0
                            )
                        ),
                        "protective"
                    )
                )

        # ----------------------------------------------------
        # SAVE SHAP EXPLANATIONS
        # ----------------------------------------------------

        if explanation_rows:
            cursor.executemany(
                """
                INSERT INTO customer_explanations (
                    dataset_id,
                    customer_id,
                    feature_name,
                    feature_value,
                    impact,
                    explanation_type
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                explanation_rows
            )

        connection.commit()

        return True

    except (
        Error,
        ValueError,
        TypeError
    ) as e:

        connection.rollback()

        logger.exception("Customer analysis save error")

        return False

    finally:
        cursor.close()
        connection.close()


# ============================================================
# CUSTOMERS BY DATASET
# ============================================================

def get_customers_by_dataset(dataset_id, user_id):
    connection = get_connection()

    if not connection:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                c.customer_id,
                c.dataset_id,
                c.tenure,
                c.city_tier,
                c.order_count,
                c.days_since_last_order,
                c.cashback_amount,
                c.satisfaction_score,
                c.preferred_order_category,
                c.preferred_payment_mode,
                c.preferred_login_device,
                c.gender,
                c.marital_status,
                c.complain,

                p.churn_probability,
                p.prediction,
                p.risk_level,
                p.recommendation,
                p.retention_action,
                p.retention_priority,
                p.retention_reason,
                p.retention_recommendation

            FROM customers c

            INNER JOIN datasets d
                ON d.id = c.dataset_id
               AND d.user_id = %s

            LEFT JOIN predictions p
                ON p.id = (
                    SELECT MAX(p2.id)
                    FROM predictions p2
                    WHERE p2.customer_id = c.customer_id
                      AND p2.dataset_id = c.dataset_id
                )

            WHERE c.dataset_id = %s

            ORDER BY c.id ASC
            """,
            (user_id, dataset_id)
        )

        customers = cursor.fetchall()

        # ----------------------------------------------------
        # EXPLANATIONS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                customer_id,
                dataset_id,
                feature_name,
                feature_value,
                impact,
                explanation_type
            FROM customer_explanations e
            INNER JOIN datasets d
                ON d.id = e.dataset_id
               AND d.user_id = %s
            WHERE e.dataset_id = %s
            ORDER BY e.id ASC
            """,
            (user_id, dataset_id)
        )

        explanations = cursor.fetchall()

        explanation_map = {}

        for explanation in explanations:

            customer_id = (
                explanation["customer_id"]
            )

            if customer_id not in explanation_map:
                explanation_map[customer_id] = {
                    "risk_factors": [],
                    "protective_factors": []
                }

            factor = {
                "feature":
                    explanation["feature_name"],

                "value":
                    explanation["feature_value"],

                "impact":
                    float(
                        explanation["impact"] or 0
                    )
            }

            if (
                explanation["explanation_type"]
                == "risk"
            ):
                explanation_map[
                    customer_id
                ]["risk_factors"].append(
                    factor
                )

            elif (
                explanation["explanation_type"]
                == "protective"
            ):
                explanation_map[
                    customer_id
                ]["protective_factors"].append(
                    factor
                )

        # ----------------------------------------------------
        # FRONTEND RECORDS
        # ----------------------------------------------------

        result = []

        for customer in customers:

            customer_id = (
                customer["customer_id"]
            )

            factors = explanation_map.get(
                customer_id,
                {
                    "risk_factors": [],
                    "protective_factors": []
                }
            )

            result.append({
                "CustomerID":
                    customer_id,

                "dataset_id":
                    customer["dataset_id"],

                "tenure":
                    customer["tenure"],

                "city_tier":
                    customer["city_tier"],

                "order_count":
                    customer["order_count"],

                "days_since_last_order":
                    customer[
                        "days_since_last_order"
                    ],

                "cashback_amount":
                    float(
                        customer[
                            "cashback_amount"
                        ] or 0
                    ),

                "satisfaction_score":
                    float(
                        customer[
                            "satisfaction_score"
                        ] or 0
                    ),

                "preferred_order_category":
                    customer[
                        "preferred_order_category"
                    ],

                "preferred_payment_mode":
                    customer[
                        "preferred_payment_mode"
                    ],

                "preferred_login_device":
                    customer[
                        "preferred_login_device"
                    ],

                "gender":
                    customer["gender"],

                "marital_status":
                    customer["marital_status"],

                "complain":
                    customer["complain"],

                "churn_probability":
                    float(
                        customer[
                            "churn_probability"
                        ] or 0
                    ),

                "prediction":
                    int(
                        customer[
                            "prediction"
                        ] or 0
                    ),

                "risk_level":
                    customer["risk_level"],

                "recommendation":
                    customer[
                        "recommendation"
                    ] or "",

                "retention_action": {
                    "action": customer["retention_action"] or "",
                    "priority": customer["retention_priority"] or "",
                    "reason": customer["retention_reason"] or "",
                    "recommendation": customer["retention_recommendation"] or ""
                },

                "risk_factors":
                    factors[
                        "risk_factors"
                    ],

                "protective_factors":
                    factors[
                        "protective_factors"
                    ]
            })

        return result

    except Error as e:

        logger.exception("Error retrieving customers")

        return []

    finally:
        cursor.close()
        connection.close()