import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier


# ============================================================
# 1. LOAD CLEAN DATA
# ============================================================

df = pd.read_csv(
    "data/processed/ecommerce_churn_clean.csv"
)


# ============================================================
# 2. DEFINE X AND y
# ============================================================

X = df.drop(
    columns=["customer_id", "churn"]
)

y = df["churn"]


# ============================================================
# 3. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# ============================================================
# 4. FEATURE GROUPS
# ============================================================

numerical_columns = [
    "tenure",
    "warehouse_to_home",
    "hour_spend_on_app",
    "number_of_device_registered",
    "number_of_address",
    "order_amount_hike_from_last_year",
    "coupon_used",
    "order_count",
    "days_since_last_order",
    "cashback_amount"
]

categorical_columns = [
    "preferred_login_device",
    "preferred_payment_mode",
    "gender",
    "preferred_order_category",
    "marital_status"
]


# ============================================================
# 5. NUMERICAL PIPELINE
# ============================================================

numerical_pipeline = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),
    (
        "scaler",
        StandardScaler()
    )
])


# ============================================================
# 6. CATEGORICAL PIPELINE
# ============================================================

categorical_pipeline = Pipeline([
    (
        "encoder",
        OneHotEncoder(
            handle_unknown="ignore"
        )
    )
])


# ============================================================
# 7. PREPROCESSOR
# ============================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            numerical_pipeline,
            numerical_columns
        ),
        (
            "cat",
            categorical_pipeline,
            categorical_columns
        )
    ],
    remainder="passthrough"
)


# ============================================================
# 8. FINAL MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    class_weight="balanced",
    random_state=42
)


# ============================================================
# 9. FINAL PIPELINE
# ============================================================

final_pipeline = Pipeline([
    (
        "preprocessor",
        preprocessor
    ),
    (
        "model",
        model
    )
])


# ============================================================
# 10. TRAIN
# ============================================================

final_pipeline.fit(
    X_train,
    y_train
)


# ============================================================
# 11. SAVE MODEL
# ============================================================

joblib.dump(
    final_pipeline,
    "models/retainiq_model.joblib"
)

print("Final RetainIQ model saved successfully.")
























