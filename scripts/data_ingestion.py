import pandas as pd
import re


# Features required by our trained ML model
REQUIRED_COLUMNS = [
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


# Different names that may represent the same feature
COLUMN_ALIASES = {
    "tenure": [
        "tenure",
        "Tenure"
    ],

    "preferred_login_device": [
        "preferred_login_device",
        "PreferredLoginDevice"
    ],

    "city_tier": [
        "city_tier",
        "CityTier"
    ],

    "warehouse_to_home": [
        "warehouse_to_home",
        "WarehouseToHome"
    ],

    "preferred_payment_mode": [
        "preferred_payment_mode",
        "PreferredPaymentMode"
    ],

    "gender": [
        "gender",
        "Gender"
    ],

    "hour_spend_on_app": [
        "hour_spend_on_app",
        "HourSpendOnApp"
    ],

    "number_of_device_registered": [
        "number_of_device_registered",
        "NumberOfDeviceRegistered"
    ],

    "preferred_order_category": [
        "preferred_order_category",
        "PreferedOrderCat",
        "PreferredOrderCat"
    ],

    "satisfaction_score": [
        "satisfaction_score",
        "SatisfactionScore"
    ],

    "marital_status": [
        "marital_status",
        "MaritalStatus"
    ],

    "number_of_address": [
        "number_of_address",
        "NumberOfAddress"
    ],

    "complain": [
        "complain",
        "Complain"
    ],

    "order_amount_hike_from_last_year": [
        "order_amount_hike_from_last_year",
        "OrderAmountHikeFromlastYear",
        "OrderAmountHikeFromLastYear"
    ],

    "coupon_used": [
        "coupon_used",
        "CouponUsed"
    ],

    "order_count": [
        "order_count",
        "OrderCount"
    ],

    "days_since_last_order": [
        "days_since_last_order",
        "DaySinceLastOrder",
        "DaysSinceLastOrder"
    ],

    "cashback_amount": [
        "cashback_amount",
        "CashbackAmount"
    ]
}


def normalize_column_name(column):
    """
    Converts a column name into a standard format.

    Example:
    'Preferred Login Device'
    becomes
    'preferred_login_device'
    """

    column = str(column).strip().lower()
    column = re.sub(r"[^a-z0-9]+", "_", column)
    column = re.sub(r"_+", "_", column)
    return column.strip("_")


def find_matching_column(columns, aliases):
    """
    Finds a column in the uploaded dataset
    that matches one of the known aliases.
    """

    normalized_columns = {
        normalize_column_name(col): col
        for col in columns
    }

    for alias in aliases:
        normalized_alias = normalize_column_name(alias)

        if normalized_alias in normalized_columns:
            return normalized_columns[normalized_alias]

    return None


def prepare_dataset(file):
    """
    Reads and prepares an uploaded CSV/Excel dataset.
    Works with both Flask uploaded files and local file paths.
    """

    if hasattr(file, "filename"):
        filename = file.filename.lower()
    else:
        filename = str(file).lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(file)

    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file)

    else:
        raise ValueError(
            "Unsupported file format. Please upload CSV or Excel."
        )

    original_columns = list(df.columns)

    column_mapping = {}
    missing_columns = []

    for required_column in REQUIRED_COLUMNS:

        matched_column = find_matching_column(
            df.columns,
            COLUMN_ALIASES[required_column]
        )

        if matched_column:
            column_mapping[matched_column] = required_column
        else:
            missing_columns.append(required_column)

    if missing_columns:
        return {
            "success": False,
            "error": "Required customer features are missing.",
            "missing_columns": missing_columns,
            "original_columns": original_columns
        }

    df = df.rename(columns=column_mapping)

    model_df = df[REQUIRED_COLUMNS].copy()

    model_df = model_df.dropna()

    return {
        "success": True,
        "data": model_df,
        "original_columns": original_columns,
        "mapped_columns": column_mapping,
        "rows": len(model_df),
        "columns": len(model_df.columns)
    }