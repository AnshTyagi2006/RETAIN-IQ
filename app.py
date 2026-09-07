# ============================================================
# RETAIN IQ - FLASK APPLICATION
# ============================================================

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)
import shap
from pathlib import Path
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.datastructures import FileStorage
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import re
import hashlib
import pandas as pd


# ============================================================
# PROJECT MODULES
# ============================================================

from scripts.data_ingestion import prepare_dataset
from scripts.prediction_engine import get_customer_prediction, model
from scripts.bulk_prediction import predict_bulk
from scripts.global_analytics import get_global_report
from scripts.retention_engine import generate_retention_action

from scripts.database import (
    save_customer_analysis,
    ensure_dataset_ownership_schema,
    create_dataset,
    get_dataset,
    get_all_datasets,
    get_customers_by_dataset,
    ensure_users_table,
    ensure_retention_columns,
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_last_login,
    test_connection
)


# ============================================================
# FLASK APP
# ============================================================
load_dotenv()
app = Flask(__name__)

# Local-development secret. For deployment, set RETAINIQ_SECRET_KEY.
app.secret_key = os.environ.get(
    "RETAINIQ_SECRET_KEY",
    "retainiq-local-session-key-change-this"
)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get(
        "SESSION_COOKIE_SECURE", "0"
    ).lower() in ("1", "true", "yes"),
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    MAX_CONTENT_LENGTH=int(
        os.environ.get("MAX_CONTENT_LENGTH", 25 * 1024 * 1024)
    )
)


# INITIALIZE AUTHENTICATION TABLE
# The table is created automatically; no manual SQL migration is required.
ensure_users_table()
ensure_dataset_ownership_schema()
ensure_retention_columns()


# ============================================================
# CURRENT SESSION STATE
# ============================================================

# Current Upload dataset
active_dataset_id = None

# Current Sample session
# Sample data is regenerated per authenticated request; no shared user cache.

# Current bulk predictions
latest_predictions = []


# ============================================================
# JSON SERIALIZATION
# ============================================================

def make_json_safe(obj):

    if isinstance(obj, pd.DataFrame):

        return obj.to_dict(
            orient="records"
        )

    if isinstance(obj, pd.Series):

        return obj.to_dict()

    if hasattr(obj, "item"):

        try:
            return obj.item()

        except Exception:
            pass

    if isinstance(obj, dict):

        return {
            key: make_json_safe(value)
            for key, value in obj.items()
        }

    if isinstance(obj, (list, tuple)):

        return [
            make_json_safe(value)
            for value in obj
        ]

    return obj


# ============================================================
# AUTHENTICATION HELPERS
# ============================================================

def normalize_email(email):
    return str(email or "").strip().lower()


def is_authenticated():
    return bool(session.get("user_id"))


def login_required(view):
    """Protect application pages and APIs behind authentication."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if is_authenticated():
            return view(*args, **kwargs)

        if request.path.startswith("/auth/") or request.path == "/":
            return view(*args, **kwargs)

        if request.path.startswith(("/predict", "/analyze", "/sample-data", "/explain-customer", "/customers/", "/datasets")):
            return jsonify({
                "success": False,
                "error": "Authentication required.",
                "authenticated": False
            }), 401

        return redirect(url_for("home"))

    return wrapped


# ============================================================
# AUTHENTICATION API
# ============================================================

@app.route("/auth/register", methods=["POST"])
def auth_register():
    try:
        data = request.get_json(silent=True) or {}

        name = str(data.get("name", "")).strip()
        email = normalize_email(data.get("email"))
        password = str(data.get("password", ""))
        remember = bool(data.get("remember", False))

        if not name:
            return jsonify({"success": False, "message": "Name is required."}), 400

        if len(name) > 120:
            return jsonify({"success": False, "message": "Name is too long."}), 400

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            return jsonify({"success": False, "message": "Enter a valid email address."}), 400

        if len(password) < 8:
            return jsonify({"success": False, "message": "Password must contain at least 8 characters."}), 400

        if len(password) > 128:
            return jsonify({"success": False, "message": "Password is too long."}), 400

        if get_user_by_email(email):
            return jsonify({
                "success": False,
                "message": "An account with this email already exists. Please sign in."
            }), 409

        password_hash = generate_password_hash(password)
        user_id = create_user(name, email, password_hash)

        if not user_id:
            # Covers database errors and a possible duplicate created concurrently.
            if get_user_by_email(email):
                return jsonify({
                    "success": False,
                    "message": "An account with this email already exists. Please sign in."
                }), 409

            return jsonify({
                "success": False,
                "message": "Unable to create your account right now."
            }), 500

        session.clear()
        session.permanent = remember
        session["user_id"] = int(user_id)
        session["user_name"] = name
        session["user_email"] = email

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "authenticated": True,
            "redirect": "/dashboard",
            "user": {
                "id": int(user_id),
                "name": name,
                "email": email
            }
        }), 201

    except Exception as e:
        app.logger.exception("Registration error")
        return jsonify({
            "success": False,
            "message": "Unable to create your account right now."
        }), 500


@app.route("/auth/login", methods=["POST"])
def auth_login():
    try:
        data = request.get_json(silent=True) or {}

        email = normalize_email(data.get("email"))
        password = str(data.get("password", ""))
        remember = bool(data.get("remember", False))

        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required."
            }), 400

        user = get_user_by_email(email)

        # Keep the error generic so the endpoint does not reveal
        # whether an email address is registered.
        if not user or not check_password_hash(
            user["password_hash"],
            password
        ):
            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        session.clear()
        session.permanent = remember
        session["user_id"] = int(user["id"])
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        update_user_last_login(user["id"])

        return jsonify({
            "success": True,
            "message": "Signed in successfully.",
            "authenticated": True,
            "redirect": "/dashboard",
            "user": {
                "id": int(user["id"]),
                "name": user["name"],
                "email": user["email"]
            }
        })

    except Exception as e:
        app.logger.exception("Login error")
        return jsonify({
            "success": False,
            "message": "Unable to sign in right now."
        }), 500


@app.route("/auth/logout", methods=["POST", "GET"])
def auth_logout():
    session.clear()
    return jsonify({
        "success": True,
        "message": "Signed out successfully.",
        "authenticated": False,
        "redirect": "/"
    })


@app.route("/auth/me", methods=["GET"])
def auth_me():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": True,
            "authenticated": False,
            "user": None
        })

    user = get_user_by_id(user_id)

    if not user:
        session.clear()
        return jsonify({
            "success": True,
            "authenticated": False,
            "user": None
        })

    return jsonify({
        "success": True,
        "authenticated": True,
        "user": make_json_safe(user)
    })


# ============================================================
# DEPLOYMENT HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    """Return 200 only when the app and database are ready."""
    try:
        database_ready = test_connection()

        if not database_ready:
            return jsonify({
                "status": "degraded",
                "database": "unavailable"
            }), 503

        return jsonify({
            "status": "ok",
            "database": "ok"
        }), 200

    except Exception:
        app.logger.exception("Health check failed")
        return jsonify({
            "status": "degraded"
        }), 503


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


@app.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html"
    )


@app.route("/manual")
@login_required
def manual():

    return render_template(
        "manual.html"
    )


@app.route("/upload")
@login_required
def upload():

    return render_template(
        "upload.html"
    )


@app.route("/sample")
@login_required
def sample():

    return render_template(
        "sample.html"
    )


@app.route("/bulk_dashboard")
@login_required
def bulk_dashboard():

    return render_template(
        "bulk_dashboard.html"
    )


@app.route("/customers")
@login_required
def customers_page():

    return render_template(
        "customers.html"
    )


@app.route("/customer")
@login_required
def customer():

    return render_template(
        "customer.html"
    )


# ============================================================
# MANUAL CUSTOMER PREDICTION
# ============================================================

@app.route(
    "/predict",
    methods=["POST"]
)
@login_required
def predict():

    try:

        customer = request.get_json()

        if not customer:

            return jsonify({
                "success": False,
                "error":
                    "No customer data received."
            }), 400

        # ----------------------------------------------------
        # CREATE UNIQUE MANUAL CUSTOMER ID
        # ----------------------------------------------------

        if not customer.get(
            "CustomerID"
        ):

            customer["CustomerID"] = (
                "MANUAL_"
                + datetime.now().strftime(
                    "%Y%m%d%H%M%S%f"
                )
            )

        # ----------------------------------------------------
        # ML PREDICTION
        # ----------------------------------------------------

        result = get_customer_prediction(
            customer
        )

        # ----------------------------------------------------
        # CREATE MANUAL DATASET
        # ----------------------------------------------------

        user_id = int(session["user_id"])

        dataset_id = create_dataset(
            dataset_name=("Manual - " + customer["CustomerID"]),
            source_type="MANUAL",
            original_filename=None,
            user_id=user_id
        )

        database_saved = False

        if dataset_id:
            database_saved = save_customer_analysis(
                customer,
                result,
                dataset_id,
                user_id
            )

        session["active_dataset_id"] = dataset_id
        session["analysis_type"] = "manual"

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "customer":
                make_json_safe(
                    customer
                ),

            "result":
                make_json_safe(
                    result
                ),

            "database_saved":
                database_saved,

            "dataset_id":
                dataset_id,

            "source_type":
                "MANUAL"
        })

    except Exception as e:

        app.logger.exception("Manual prediction error")

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# UPLOAD DATASET ANALYSIS
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
@login_required
def analyze():

    global active_dataset_id
    global latest_predictions

    try:

        # ----------------------------------------------------
        # VALIDATE FILE
        # ----------------------------------------------------

        if "file" not in request.files:

            return jsonify({

                "success": False,

                "error":
                    "No file uploaded."

            }), 400

        file = request.files["file"]

        if not file.filename:

            return jsonify({

                "success": False,

                "error":
                    "No file selected."

            }), 400

        # ----------------------------------------------------
        # READ UPLOAD AND CALCULATE FILE HASH
        # ----------------------------------------------------

        file_bytes = file.read()

        if not file_bytes:
            return jsonify({
                "success": False,
                "error": "Uploaded file is empty."
            }), 400

        file_hash = hashlib.sha256(
            file_bytes
        ).hexdigest()

        app.logger.debug("Upload file hash: %s", file_hash)

        # Rebuild FileStorage because the original stream was consumed.
        file = FileStorage(
            stream=BytesIO(file_bytes),
            filename=file.filename,
            content_type=file.content_type
        )

        # ----------------------------------------------------
        # PREPARE DATASET
        # ----------------------------------------------------

        prepared = prepare_dataset(file)

        if not isinstance(prepared, dict):
            return jsonify({
                "success": False,
                "error": "Invalid dataset preparation result."
            }), 500

        if not prepared.get("success"):
            return jsonify({
                "success": False,
                "error": prepared.get(
                    "error",
                    "Unable to prepare dataset."
                )
            }), 400

        customers = prepared["data"]

        app.logger.info("Customers prepared: %s", len(customers))

        # ----------------------------------------------------
        # BULK PREDICTION
        # ----------------------------------------------------

        predictions = predict_bulk(customers)
        latest_predictions = predictions

        app.logger.info("Predictions generated: %s", len(predictions))

        # ----------------------------------------------------
        # CREATE OR REUSE UPLOAD DATASET
        # ----------------------------------------------------

        user_id = int(session["user_id"])

        dataset_id = create_dataset(
            dataset_name="Upload - " + file.filename,
            source_type="UPLOAD",
            original_filename=file.filename,
            file_hash=file_hash,
            user_id=user_id
        )

        if not dataset_id:
            return jsonify({
                "success": False,
                "error": "Unable to create or reuse upload dataset."
            }), 500

        # Store the selected dataset in the user's Flask session.
        session["active_dataset_id"] = dataset_id
        session["analysis_type"] = "upload"

        # ----------------------------------------------------
        # SAVE UPLOADED CUSTOMERS
        # ----------------------------------------------------

        database_saved = 0
        database_failed = 0

        for customer, result in zip(
            customers,
            predictions
        ):

            try:

                saved = (
                    save_customer_analysis(
                        customer,
                        result,
                        dataset_id,
                        user_id
                    )
                )

                if saved:

                    database_saved += 1

                else:

                    database_failed += 1

            except Exception as db_error:

                database_failed += 1

                app.logger.exception("Database save error")

        app.logger.info(
            "MySQL: %s saved, %s failed",
            database_saved,
            database_failed,
        )

        # ----------------------------------------------------
        # GLOBAL ANALYTICS
        # ----------------------------------------------------

        report = get_global_report(
            predictions
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "report":
                make_json_safe(
                    report
                ),

            "customers":
                make_json_safe(
                    predictions
                ),

            "database": {

                "saved":
                    database_saved,

                "failed":
                    database_failed
            },

            "dataset_id":
                dataset_id,

            "source_type":
                "UPLOAD"
        })

    except Exception as e:

        app.logger.exception("Bulk analysis error")

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# SAMPLE DATASET
# ============================================================

@app.route(
    "/sample-data",
    methods=["GET"]
)
@login_required
def sample_data():

    global latest_predictions

    try:

        # ----------------------------------------------------
        # SAMPLE CSV PATH
        # ----------------------------------------------------

        base_dir = (
            Path(__file__).resolve().parent
        )

        file_path = (
            base_dir
            / "Data"
            / "processed"
            / "ecommerce_churn_clean.csv"
        )

        if not file_path.exists():

            return jsonify({

                "success": False,

                "error":
                    "Sample dataset not found: "
                    + str(file_path)

            }), 404

        app.logger.info("Sample dataset found: %s", file_path)

        # ----------------------------------------------------
        # CREATE FILE OBJECT
        # ----------------------------------------------------

        with open(
            file_path,
            "rb"
        ) as f:

            file_data = BytesIO(
                f.read()
            )

        sample_file = FileStorage(

            stream=file_data,

            filename=(
                "ecommerce_churn_clean.csv"
            ),

            content_type="text/csv"
        )

        # ----------------------------------------------------
        # PREPARE DATASET
        # ----------------------------------------------------

        prepared = prepare_dataset(
            sample_file
        )

        if not isinstance(
            prepared,
            dict
        ):

            return jsonify({

                "success": False,

                "error":
                    "Invalid sample dataset result."

            }), 500

        if not prepared.get(
            "success"
        ):

            return jsonify({

                "success": False,

                "error":
                    prepared.get(
                        "error",
                        "Unable to prepare "
                        "sample dataset."
                    )

            }), 400

        customers = prepared[
            "data"
        ]

        app.logger.info("Sample customers prepared: %s", len(customers))

        # ----------------------------------------------------
        # PREDICT SAMPLE DATA
        # ----------------------------------------------------

        predictions = predict_bulk(
            customers
        )

        # ----------------------------------------------------
        # KEEP SAMPLE COMPLETELY SEPARATE
        # ----------------------------------------------------

        latest_predictions = predictions

        # Sample is intentionally never stored in MySQL.
        session["active_dataset_id"] = None
        session["analysis_type"] = "sample"

        app.logger.info("Sample predictions generated: %s", len(predictions))

        # ----------------------------------------------------
        # GLOBAL ANALYTICS
        # ----------------------------------------------------

        report = get_global_report(
            predictions
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "report":
                make_json_safe(
                    report
                ),

            "customers":
                make_json_safe(
                    predictions
                ),

            "database": {

                "saved": 0,

                "failed": 0,

                "message":
                    "Sample data is kept "
                    "separate from MySQL."
            },

            "source_type":
                "SAMPLE"
        })

    except Exception as e:

        app.logger.exception("Sample analysis error")

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# INDIVIDUAL CUSTOMER SHAP ANALYSIS
# ============================================================

@app.route("/explain-customer", methods=["POST"])
@login_required
def explain_customer():

    try:
        customer = request.get_json()

        if not customer:
            return jsonify({
                "success": False,
                "error": "No customer data received."
            }), 400

        # ----------------------------------------------------
        # GET ORIGINAL MODEL INPUT FEATURES
        # ----------------------------------------------------

        try:
            model_features = list(
                model.feature_names_in_
            )
        except AttributeError:

            model_features = [
                "tenure",
                "preferred_login_device",
                "city_tier",
                "warehouse_to_home",
                "preferred_payment_mode",
                "gender",
                "hour_spend_on_app",
                "number_of_device_registered",
                "preferred_order_category",
                "satisfaction_score",
                "marital_status",
                "number_of_address",
                "complain",
                "order_amount_hike_from_last_year",
                "coupon_used",
                "order_count",
                "days_since_last_order",
                "cashback_amount"
            ]

        # ----------------------------------------------------
        # BUILD CLEAN MODEL INPUT
        # ----------------------------------------------------

        clean_customer = {}

        for feature in model_features:

            if feature not in customer:
                clean_customer[feature] = None
            else:
                clean_customer[feature] = customer[feature]

        customer_df = pd.DataFrame(
            [clean_customer],
            columns=model_features
        )

        # ----------------------------------------------------
        # NUMERIC TYPE CONVERSION
        # ----------------------------------------------------

        numeric_features = [
            "tenure",
            "city_tier",
            "warehouse_to_home",
            "hour_spend_on_app",
            "number_of_device_registered",
            "satisfaction_score",
            "number_of_address",
            "complain",
            "order_amount_hike_from_last_year",
            "coupon_used",
            "order_count",
            "days_since_last_order",
            "cashback_amount"
        ]

        for column in numeric_features:

            if column in customer_df.columns:

                customer_df[column] = pd.to_numeric(
                    customer_df[column],
                    errors="coerce"
                )

        # ----------------------------------------------------
        # MODEL COMPONENTS
        # ----------------------------------------------------

        preprocessor = model.named_steps["preprocessor"]
        trained_model = model.named_steps["model"]

        # ----------------------------------------------------
        # TRANSFORM ONE CUSTOMER
        # ----------------------------------------------------

        transformed = preprocessor.transform(
            customer_df
        )

        # ----------------------------------------------------
        # SHAP
        # ----------------------------------------------------

        explainer = shap.TreeExplainer(
            trained_model
        )

        shap_values = explainer.shap_values(
            transformed
        )

        # ----------------------------------------------------
        # GET CHURN CLASS SHAP VALUES
        # ----------------------------------------------------

        if isinstance(shap_values, list):

            customer_shap = shap_values[1][0]

        elif len(shap_values.shape) == 3:

            customer_shap = shap_values[0, :, 1]

        else:

            customer_shap = shap_values[0]

        # ----------------------------------------------------
        # FEATURE NAMES
        # ----------------------------------------------------

        feature_names = (
            preprocessor
            .get_feature_names_out()
        )

        # ----------------------------------------------------
        # VALIDATE SHAP OUTPUT
        # ----------------------------------------------------

        if len(customer_shap) != len(feature_names):

            raise RuntimeError(
                "SHAP output does not match the model feature count."
            )

        # ----------------------------------------------------
        # CATEGORICAL FEATURES
        # ----------------------------------------------------

        categorical_columns = [
            "preferred_login_device",
            "preferred_payment_mode",
            "gender",
            "preferred_order_category",
            "marital_status"
        ]

        valid_features = []

        for feature in feature_names:

            # Numerical features
            if feature.startswith("num__"):

                valid_features.append(feature)
                continue

            # Passthrough features
            if feature.startswith("remainder__"):

                valid_features.append(feature)
                continue

            # One-hot categorical features
            if feature.startswith("cat__"):

                encoded_feature = feature.replace(
                    "cat__",
                    "",
                    1
                )

                for column in categorical_columns:

                    prefix = column + "_"

                    if encoded_feature.startswith(prefix):

                        encoded_value = encoded_feature[
                            len(prefix):
                        ]

                        actual_value = str(
                            customer.get(
                                column,
                                ""
                            )
                        )

                        if encoded_value == actual_value:

                            valid_features.append(
                                feature
                            )

                        break

        # ----------------------------------------------------
        # SHAP DATAFRAME
        # ----------------------------------------------------

        shap_df = pd.DataFrame({
            "feature": feature_names,
            "shap_value": customer_shap
        })

        shap_df = shap_df[
            shap_df["feature"].isin(
                valid_features
            )
        ]

        # ----------------------------------------------------
        # POSITIVE = INCREASES CHURN
        # ----------------------------------------------------

        risk_df = (
            shap_df[
                shap_df["shap_value"] > 0
            ]
            .sort_values(
                "shap_value",
                ascending=False
            )
            .head(5)
        )

        # ----------------------------------------------------
        # NEGATIVE = REDUCES CHURN
        # ----------------------------------------------------

        protective_df = (
            shap_df[
                shap_df["shap_value"] < 0
            ]
            .sort_values(
                "shap_value",
                ascending=True
            )
            .head(5)
        )

        # ----------------------------------------------------
        # FEATURE NAME
        # ----------------------------------------------------

        def clean_feature_name(feature):

            return (
                str(feature)
                .replace("num__", "")
                .replace("cat__", "")
                .replace("remainder__", "")
                .replace("_", " ")
            )

        # ----------------------------------------------------
        # GET ORIGINAL VALUE
        # ----------------------------------------------------

        def get_feature_value(feature):

            feature = str(feature)

            if feature.startswith("num__"):

                column = feature.replace(
                    "num__",
                    "",
                    1
                )

                return customer.get(
                    column
                )

            if feature.startswith("remainder__"):

                column = feature.replace(
                    "remainder__",
                    "",
                    1
                )

                return customer.get(
                    column
                )

            if feature.startswith("cat__"):

                encoded = feature.replace(
                    "cat__",
                    "",
                    1
                )

                for column in categorical_columns:

                    prefix = column + "_"

                    if encoded.startswith(prefix):

                        return customer.get(
                            column
                        )

            return None

        # ----------------------------------------------------
        # EXPLANATION TEXT
        # ----------------------------------------------------

        def make_explanation(
            feature,
            impact
        ):

            positive = impact > 0

            explanations = {

                "num__tenure":
                    (
                        "Customer tenure is contributing "
                        "to higher churn risk."
                        if positive
                        else
                        "Customer tenure is supporting retention."
                    ),

                "num__warehouse_to_home":
                    (
                        "Warehouse-to-home distance is "
                        "contributing to higher churn risk."
                        if positive
                        else
                        "Warehouse-to-home distance is "
                        "supporting retention."
                    ),

                "num__number_of_device_registered":
                    (
                        "Registered device behavior is "
                        "contributing to higher churn risk."
                        if positive
                        else
                        "Registered device behavior is "
                        "supporting retention."
                    ),

                "num__satisfaction_score":
                    (
                        "Customer satisfaction is contributing "
                        "to higher churn risk."
                        if positive
                        else
                        "Customer satisfaction is supporting retention."
                    ),

                "num__number_of_address":
                    (
                        "Customer address information is "
                        "contributing to higher churn risk."
                        if positive
                        else
                        "Customer address information is "
                        "supporting retention."
                    ),

                "num__days_since_last_order":
                    (
                        "Longer time since the last order is "
                        "contributing to higher churn risk."
                        if positive
                        else
                        "Recent ordering behavior is supporting retention."
                    ),

                "num__cashback_amount":
                    (
                        "Cashback behavior is contributing "
                        "to higher churn risk."
                        if positive
                        else
                        "Cashback behavior is supporting retention."
                    ),

                "num__order_count":
                    (
                        "Order activity is contributing "
                        "to higher churn risk."
                        if positive
                        else
                        "Order activity is supporting retention."
                    )
            }

            if feature in explanations:

                return explanations[feature]

            return (
                f"{clean_feature_name(feature)} is "
                f"contributing to "
                f"{'higher' if positive else 'lower'} "
                f"predicted churn risk."
            )

        # ----------------------------------------------------
        # RISK FACTORS
        # ----------------------------------------------------

        risk_factors = []

        for _, row in risk_df.iterrows():

            feature = str(
                row["feature"]
            )

            impact = float(
                row["shap_value"]
            )

            risk_factors.append({

                "feature":
                    clean_feature_name(
                        feature
                    ),

                "value":
                    get_feature_value(
                        feature
                    ),

                "impact":
                    impact,

                "explanation":
                    make_explanation(
                        feature,
                        impact
                    )

            })

        # ----------------------------------------------------
        # PROTECTIVE FACTORS
        # ----------------------------------------------------

        protective_factors = []

        for _, row in protective_df.iterrows():

            feature = str(
                row["feature"]
            )

            impact = float(
                row["shap_value"]
            )

            protective_factors.append({

                "feature":
                    clean_feature_name(
                        feature
                    ),

                "value":
                    get_feature_value(
                        feature
                    ),

                "impact":
                    impact,

                "explanation":
                    make_explanation(
                        feature,
                        impact
                    )

            })

        # ----------------------------------------------------
        # PREDICTION
        # ----------------------------------------------------

        probability = float(
            model.predict_proba(
                customer_df
            )[0][1]
        )

        prediction = int(
            model.predict(
                customer_df
            )[0]
        )

        # ----------------------------------------------------
        # RISK LEVEL
        # ----------------------------------------------------

        if probability >= 0.70:

            risk_level = "High Risk"

        elif probability >= 0.40:

            risk_level = "Medium Risk"

        else:

            risk_level = "Low Risk"

        # ----------------------------------------------------
        # RETENTION INTELLIGENCE
        # ----------------------------------------------------

        retention_action = generate_retention_action(
            customer,
            risk_level
        )

        recommendation = retention_action.get(
            "recommendation",
            ""
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "probability":
                probability,

            "risk_level":
                risk_level,

            "prediction":
                prediction,

            "risk_factors":
                make_json_safe(
                    risk_factors
                ),

            "protective_factors":
                make_json_safe(
                    protective_factors
                ),

            "recommendation":
                recommendation,

            "retention_action":
                make_json_safe(
                    retention_action
                )

        })

    except Exception as e:

        app.logger.exception("Customer explanation error")

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# CUSTOMERS DATA API
# ============================================================

@app.route("/customers/data")
@login_required
def customers_data():
    try:
        source = request.args.get("source", "").lower()

        # ----------------------------------------------------
        # SAMPLE DATA
        # ----------------------------------------------------

        if source == "sample" or session.get("analysis_type") == "sample":
            base_dir = Path(__file__).resolve().parent
            file_path = (
                base_dir
                / "Data"
                / "processed"
                / "ecommerce_churn_clean.csv"
            )

            if not file_path.exists():
                return jsonify({
                    "success": False,
                    "error": "Sample dataset not found: " + str(file_path)
                }), 404

            with open(file_path, "rb") as f:
                sample_file = FileStorage(
                    stream=BytesIO(f.read()),
                    filename="ecommerce_churn_clean.csv",
                    content_type="text/csv"
                )

            prepared = prepare_dataset(sample_file)

            if not prepared.get("success"):
                return jsonify({
                    "success": False,
                    "error": prepared.get(
                        "error",
                        "Unable to prepare sample dataset."
                    )
                }), 400

            predictions = predict_bulk(
                prepared["data"]
            )

            return jsonify({
                "success": True,
                "source_type": "SAMPLE",
                "customers": make_json_safe(predictions)
            })

        # ----------------------------------------------------
        # EXPLICIT DATABASE DATASET
        # ----------------------------------------------------

        dataset_id = request.args.get(
            "dataset_id",
            type=int
        )

        if dataset_id:
            customers = get_customers_by_dataset(
                dataset_id,
                int(session["user_id"])
            )

            return jsonify({
                "success": True,
                "source_type": "DATABASE",
                "dataset_id": dataset_id,
                "customers": make_json_safe(customers)
            })

        # ----------------------------------------------------
        # SESSION DATABASE DATASET
        # ----------------------------------------------------

        session_dataset_id = session.get(
            "active_dataset_id"
        )

        if session_dataset_id:
            customers = get_customers_by_dataset(
                int(session_dataset_id),
                int(session["user_id"])
            )

            return jsonify({
                "success": True,
                "source_type": "DATABASE",
                "dataset_id": int(session_dataset_id),
                "customers": make_json_safe(customers)
            })

        return jsonify({
            "success": True,
            "source_type": "DATABASE",
            "customers": []
        })

    except Exception as e:
        app.logger.exception("Customers data error")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# DATASET INFORMATION
# ============================================================

@app.route(
    "/datasets/<int:dataset_id>"
)
@login_required
def dataset_info(dataset_id):

    try:

        dataset = get_dataset(
            dataset_id,
            int(session["user_id"])
        )

        if not dataset:

            return jsonify({

                "success": False,

                "error":
                    "Dataset not found."

            }), 404

        return jsonify({

            "success": True,

            "dataset":
                make_json_safe(
                    dataset
                )
        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# ALL DATASETS
# ============================================================

@app.route(
    "/datasets"
)
@login_required
def datasets():

    try:

        data = get_all_datasets(int(session["user_id"]))

        return jsonify({

            "success": True,

            "datasets":
                make_json_safe(
                    data
                )

        })

    except Exception as e:

        app.logger.exception("Dataset list error")

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    ensure_users_table()
    ensure_retention_columns()

    debug = os.environ.get("FLASK_DEBUG", "0").lower() in (
        "1", "true", "yes"
    )

    app.run(debug=debug)