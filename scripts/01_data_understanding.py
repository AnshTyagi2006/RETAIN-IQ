import pandas as pd


# ============================================================
# 1. LOAD DATASET
# ============================================================

file_path = "data/raw/E Commerce Dataset.xlsx"

df = pd.read_excel(
    file_path,
    sheet_name="E Comm"
)


# ============================================================
# 2. BASIC DATASET INFORMATION
# ============================================================

print("\n===== FIRST 5 ROWS =====")
print(df.head())

print("\n===== DATASET INFO =====")
print(df.info())

print("\n===== DATASET SHAPE =====")
print(df.shape)

print("\n===== COLUMN NAMES =====")
print(df.columns)

print("\n===== DATA TYPES =====")
print(df.dtypes)

print("\n===== DESCRIPTIVE STATISTICS =====")
print(df.describe().T)


# ============================================================
# 3. MISSING VALUE ANALYSIS
# ============================================================

print("\n===== MISSING VALUES =====")
print(df.isnull().sum())

missing = pd.DataFrame({
    "missing_count": df.isnull().sum(),
    "missing_percentage": (
        df.isnull().sum() / len(df) * 100
    ).round(2)
})

missing = missing[
    missing["missing_count"] > 0
]

missing = missing.sort_values(
    "missing_percentage",
    ascending=False
)

print("\n===== MISSING VALUE SUMMARY =====")
print(missing)


# ============================================================
# 4. DUPLICATE ANALYSIS
# ============================================================

print("\n===== DUPLICATE ANALYSIS =====")

print(
    "Duplicate rows:",
    df.duplicated().sum()
)

print(
    "Unique Customer IDs:",
    df["CustomerID"].nunique()
)

print(
    "Duplicate Customer IDs:",
    df["CustomerID"].duplicated().sum()
)


# ============================================================
# 5. TARGET DISTRIBUTION
# ============================================================

print("\n===== CHURN DISTRIBUTION =====")

print(df["Churn"].value_counts())

print("\n===== CHURN PERCENTAGE =====")

print(
    df["Churn"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ============================================================
# 6. CATEGORICAL FEATURE ANALYSIS
# ============================================================

categorical_columns = [
    "PreferredLoginDevice",
    "PreferredPaymentMode",
    "Gender",
    "PreferedOrderCat",
    "MaritalStatus"
]

for col in categorical_columns:

    print(f"\n===== {col} =====")

    counts = df[col].value_counts(
        dropna=False
    )

    print(counts)


# ============================================================
# 7. BINARY / ORDINAL FEATURE ANALYSIS
# ============================================================

binary_ordinal_columns = [
    "Complain",
    "CityTier",
    "SatisfactionScore"
]

for col in binary_ordinal_columns:

    print(f"\n===== {col} =====")

    print(
        df[col]
        .value_counts(dropna=False)
        .sort_index()
    )


# ============================================================
# 8. NUMERICAL FEATURE ANALYSIS
# ============================================================

numerical_columns = [
    "Tenure",
    "WarehouseToHome",
    "HourSpendOnApp",
    "NumberOfDeviceRegistered",
    "NumberOfAddress",
    "OrderAmountHikeFromlastYear",
    "CouponUsed",
    "OrderCount",
    "DaySinceLastOrder",
    "CashbackAmount"
]

print("\n===== NUMERICAL STATISTICS =====")

print(
    df[numerical_columns]
    .describe()
    .T
)


# ============================================================
# 9. NUMERICAL FEATURE RANGES
# ============================================================

print("\n===== NUMERICAL FEATURE RANGES =====")

for col in numerical_columns:

    print(
        f"{col}: "
        f"min={df[col].min()}, "
        f"max={df[col].max()}"
    )


# ============================================================
# 10. UNIQUE CATEGORICAL VALUES
# ============================================================

print("\n===== UNIQUE CATEGORICAL VALUES =====")

for col in categorical_columns:

    print(f"\n{col}:")

    print(
        df[col].unique()
    )


# ============================================================
# 11. DATA QUALITY SUMMARY
# ============================================================

data_quality = pd.DataFrame({

    "Data_Type": df.dtypes,

    "Missing_Count": df.isnull().sum(),

    "Missing_%": (
        df.isnull().sum() / len(df) * 100
    ).round(2),

    "Unique_Values": df.nunique()
})

print("\n===== DATA QUALITY SUMMARY =====")

print(data_quality)


# ============================================================
# 12. CHURN BY CATEGORICAL FEATURES
# ============================================================

print("\n===== CHURN BY PAYMENT MODE =====")

print(
    df.groupby("PreferredPaymentMode")["Churn"]
    .agg(["count", "mean"])
    .sort_values("mean", ascending=False)
)


print("\n===== CHURN BY LOGIN DEVICE =====")

print(
    df.groupby("PreferredLoginDevice")["Churn"]
    .agg(["count", "mean"])
    .sort_values("mean", ascending=False)
)


# ============================================================
# 13. FEATURE VALIDITY CHECKS
# ============================================================

print("\n===== CHURN VALIDITY =====")

print(
    "Unique values:",
    df["Churn"].unique()
)

invalid_churn = ~df["Churn"].isin([0, 1])

print(
    "Invalid churn values:",
    invalid_churn.sum()
)


print("\n===== COMPLAIN VALIDITY =====")

print(
    "Unique values:",
    df["Complain"].unique()
)

invalid_complain = ~df["Complain"].isin([0, 1])

print(
    "Invalid complain values:",
    invalid_complain.sum()
)


print("\n===== SATISFACTION SCORE VALIDITY =====")

print(
    "Unique values:",
    sorted(df["SatisfactionScore"].dropna().unique())
)

invalid_satisfaction = ~df["SatisfactionScore"].isin(
    [1, 2, 3, 4, 5]
)

print(
    "Invalid satisfaction_score values:",
    invalid_satisfaction.sum()
)


print("\n===== CITY TIER VALIDITY =====")

print(
    "Unique values:",
    sorted(df["CityTier"].dropna().unique())
)

invalid_city_tier = ~df["CityTier"].isin(
    [1, 2, 3]
)

print(
    "Invalid city_tier values:",
    invalid_city_tier.sum()
)


# ============================================================
# 14. NEGATIVE VALUE CHECK
# ============================================================

print("\n===== NEGATIVE VALUE CHECK =====")

for col in numerical_columns:

    negative_count = (
        (df[col] < 0)
        .sum()
    )

    print(
        f"{col}: "
        f"{negative_count} negative values"
    )


# ============================================================
# 15. ORDER AMOUNT HIKE RANGE
# ============================================================

print("\n===== ORDER AMOUNT HIKE RANGE =====")

print(
    df["OrderAmountHikeFromlastYear"]
    .describe()
)


# ============================================================
# 16. ORDER CATEGORY ANALYSIS
# ============================================================

print("\n===== ORDER CATEGORY =====")

print(
    df["PreferedOrderCat"]
    .value_counts()
)

print(
    "\nUnique values:",
    df["PreferedOrderCat"].unique()
)