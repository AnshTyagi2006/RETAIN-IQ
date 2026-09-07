import pandas as pd


# ============================================================
# 1. LOAD RAW DATASET
# ============================================================

file_path = "data/raw/E Commerce Dataset.xlsx"

df = pd.read_excel(
    file_path,
    sheet_name="E Comm"
)


# ============================================================
# 2. CREATE CLEAN COPY
# ============================================================

df_clean = df.copy()


# ============================================================
# 3. STANDARDIZE COLUMN NAMES
# ============================================================

df_clean = df_clean.rename(columns={

    "CustomerID": "customer_id",

    "Churn": "churn",

    "Tenure": "tenure",

    "PreferredLoginDevice":
        "preferred_login_device",

    "CityTier":
        "city_tier",

    "WarehouseToHome":
        "warehouse_to_home",

    "PreferredPaymentMode":
        "preferred_payment_mode",

    "Gender":
        "gender",

    "HourSpendOnApp":
        "hour_spend_on_app",

    "NumberOfDeviceRegistered":
        "number_of_device_registered",

    "PreferedOrderCat":
        "preferred_order_category",

    "SatisfactionScore":
        "satisfaction_score",

    "MaritalStatus":
        "marital_status",

    "NumberOfAddress":
        "number_of_address",

    "Complain":
        "complain",

    "OrderAmountHikeFromlastYear":
        "order_amount_hike_from_last_year",

    "CouponUsed":
        "coupon_used",

    "OrderCount":
        "order_count",

    "DaySinceLastOrder":
        "days_since_last_order",

    "CashbackAmount":
        "cashback_amount"
})


# ============================================================
# 4. STANDARDIZE CATEGORICAL VALUES
# ============================================================

# Preferred Payment Mode

df_clean["preferred_payment_mode"] = (
    df_clean["preferred_payment_mode"]
    .replace({

        "CC": "Credit Card",

        "COD": "Cash on Delivery"

    })
)


# Preferred Login Device

df_clean["preferred_login_device"] = (
    df_clean["preferred_login_device"]
    .replace({

        "Phone": "Mobile Phone"

    })
)


# Preferred Order Category

df_clean["preferred_order_category"] = (
    df_clean["preferred_order_category"]
    .replace({

        "Mobile": "Mobile Phone"

    })
)


# ============================================================
# 5. FEATURE GROUPS
# ============================================================

categorical_columns = [

    "preferred_login_device",

    "preferred_payment_mode",

    "gender",

    "preferred_order_category",

    "marital_status"
]

binary_columns = [

    "complain"
]

ordinal_columns = [

    "city_tier",

    "satisfaction_score"
]

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


# ============================================================
# 6. MISSING VALUE INVESTIGATION
# ============================================================

missing_summary = pd.DataFrame({

    "Datatype": df_clean.dtypes,

    "missing_count":
        df_clean.isnull().sum(),

    "missing_percentage": (
        df_clean.isnull().sum()
        / len(df_clean)
        * 100
    ).round(2)

})

missing_summary = missing_summary[
    missing_summary["missing_count"] > 0
].sort_values(
    "missing_percentage",
    ascending=False
)

print("\n===== MISSING VALUE SUMMARY =====")

print(missing_summary)


# ============================================================
# 7. MISSINGNESS VS CHURN
# ============================================================

missing_columns = (
    missing_summary.index.tolist()
)

print("\n===== MISSINGNESS VS CHURN =====")

for col in missing_columns:

    missing_churn = df_clean.loc[
        df_clean[col].isnull(),
        "churn"
    ].mean()

    present_churn = df_clean.loc[
        df_clean[col].notnull(),
        "churn"
    ].mean()

    print(f"\n{col}")

    print(
        f"Missing    : "
        f"{missing_churn * 100:.2f}% churn"
    )

    print(
        f"Not Missing: "
        f"{present_churn * 100:.2f}% churn"
    )


# ============================================================
# 8. MISSING VALUES PER CUSTOMER
# ============================================================

missing_count_per_customer = (
    df_clean
    .isnull()
    .sum(axis=1)
)

print(
    "\n===== MISSING VALUES PER CUSTOMER ====="
)

print(
    missing_count_per_customer
    .value_counts()
    .sort_index()
)


# ============================================================
# 9. SEPARATE FEATURES AND TARGET
# ============================================================

target_column = "churn"

identifier_columns = [
    "customer_id"
]

X = df_clean.drop(
    columns=identifier_columns + [target_column]
)

y = df_clean[target_column]


print("\n===== FEATURES AND TARGET =====")

print(
    "X shape:",
    X.shape
)

print(
    "y shape:",
    y.shape
)

print("\nX columns:")

print(
    X.columns.tolist()
)

print("\ny distribution:")

print(
    y.value_counts()
)


# ============================================================
# 10. SAVE STRUCTURALLY CLEAN DATASET
# ============================================================

output_path = (
    "data/processed/"
    "ecommerce_churn_clean.csv"
)

df_clean.to_csv(
    output_path,
    index=False
)

print(
    "\nClean dataset saved to:"
)

print(output_path)