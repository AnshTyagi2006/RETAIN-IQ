import pandas as pd

from scripts.prediction_engine import model


def _clean_category(value):
    if pd.isna(value):
        return "Unknown"

    value = str(value).strip()

    return value if value else "Unknown"


def _segment_analysis(predictions_df, column):
    """
    Build business-level churn segmentation for a categorical/binary
    customer feature.

    The prepared RetainIQ dataset uses normalized lowercase column names.
    """

    if column not in predictions_df.columns:
        return []

    df = predictions_df.copy()

    df[column] = df[column].apply(_clean_category)

    grouped = (
        df.groupby(column, dropna=False)
        .agg(
            customers=("churn_probability", "size"),
            predicted_churners=("prediction", "sum"),
            average_churn_probability=(
                "churn_probability",
                "mean"
            )
        )
        .reset_index()
    )

    grouped["churn_rate"] = (
        grouped["predicted_churners"]
        / grouped["customers"]
    ).fillna(0)

    grouped["segment"] = grouped[column].astype(str)

    return grouped[
        [
            "segment",
            "customers",
            "predicted_churners",
            "churn_rate",
            "average_churn_probability"
        ]
    ].sort_values(
        ["churn_rate", "customers"],
        ascending=[False, False]
    ).to_dict(
        orient="records"
    )


def _satisfaction_segments(predictions_df):
    if "satisfaction_score" not in predictions_df.columns:
        return []

    df = predictions_df.copy()

    df["satisfaction_score"] = pd.to_numeric(
        df["satisfaction_score"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["satisfaction_score"]
    )

    grouped = (
        df.groupby("satisfaction_score")
        .agg(
            customers=("churn_probability", "size"),
            predicted_churners=("prediction", "sum"),
            average_churn_probability=(
                "churn_probability",
                "mean"
            )
        )
        .reset_index()
    )

    grouped["churn_rate"] = (
        grouped["predicted_churners"]
        / grouped["customers"]
    ).fillna(0)

    grouped["segment"] = (
        "Score "
        + grouped["satisfaction_score"]
        .astype(int)
        .astype(str)
    )

    return grouped[
        [
            "segment",
            "customers",
            "predicted_churners",
            "churn_rate",
            "average_churn_probability"
        ]
    ].sort_values(
        "segment"
    ).to_dict(
        orient="records"
    )


def _tenure_segments(predictions_df):
    if "tenure" not in predictions_df.columns:
        return []

    df = predictions_df.copy()

    tenure = pd.to_numeric(
        df["tenure"],
        errors="coerce"
    )

    df["tenure_segment"] = pd.cut(
        tenure,
        bins=[
            -float("inf"),
            6,
            12,
            24,
            float("inf")
        ],
        labels=[
            "0-6 months",
            "7-12 months",
            "13-24 months",
            "25+ months"
        ]
    )

    df = df.dropna(
        subset=["tenure_segment"]
    )

    grouped = (
        df.groupby(
            "tenure_segment",
            observed=False
        )
        .agg(
            customers=("churn_probability", "size"),
            predicted_churners=("prediction", "sum"),
            average_churn_probability=(
                "churn_probability",
                "mean"
            )
        )
        .reset_index()
    )

    grouped["churn_rate"] = (
        grouped["predicted_churners"]
        / grouped["customers"]
    ).fillna(0)

    grouped["segment"] = (
        grouped["tenure_segment"].astype(str)
    )

    return grouped[
        [
            "segment",
            "customers",
            "predicted_churners",
            "churn_rate",
            "average_churn_probability"
        ]
    ].to_dict(
        orient="records"
    )


def _complaint_segments(predictions_df):
    if "complain" not in predictions_df.columns:
        return []

    df = predictions_df.copy()

    complaint = pd.to_numeric(
        df["complain"],
        errors="coerce"
    ).fillna(0)

    df["complaint_segment"] = complaint.apply(
        lambda value:
            "Complained"
            if value == 1
            else "No Complaint"
    )

    grouped = (
        df.groupby("complaint_segment")
        .agg(
            customers=("churn_probability", "size"),
            predicted_churners=("prediction", "sum"),
            average_churn_probability=(
                "churn_probability",
                "mean"
            )
        )
        .reset_index()
    )

    grouped["churn_rate"] = (
        grouped["predicted_churners"]
        / grouped["customers"]
    ).fillna(0)

    grouped["segment"] = grouped[
        "complaint_segment"
    ]

    return grouped[
        [
            "segment",
            "customers",
            "predicted_churners",
            "churn_rate",
            "average_churn_probability"
        ]
    ].to_dict(
        orient="records"
    )


def _business_insights(predictions_df, segments):
    insights = []

    total = len(predictions_df)

    if total == 0:
        return insights

    high_risk = int(
        (
            predictions_df["risk_level"]
            == "High Risk"
        ).sum()
    )

    medium_risk = int(
        (
            predictions_df["risk_level"]
            == "Medium Risk"
        ).sum()
    )

    if high_risk:
        insights.append(
            f"{high_risk:,} customers are classified as high risk "
            "and should receive immediate retention attention."
        )

    if medium_risk:
        insights.append(
            f"{medium_risk:,} customers are classified as medium risk "
            "and are suitable for targeted engagement."
        )

    satisfaction = segments.get(
        "satisfaction",
        []
    )

    if satisfaction:
        highest = max(
            satisfaction,
            key=lambda row: row["churn_rate"]
        )

        lowest = min(
            satisfaction,
            key=lambda row: row["churn_rate"]
        )

        if (
            highest["churn_rate"]
            > lowest["churn_rate"]
        ):
            insights.append(
                f'{highest["segment"]} has the highest predicted churn '
                f'rate ({highest["churn_rate"] * 100:.1f}%), making '
                "customer satisfaction an important retention signal."
            )

    complaint = segments.get(
        "complaint",
        []
    )

    complained = next(
        (
            row
            for row in complaint
            if row["segment"] == "Complained"
        ),
        None
    )

    no_complaint = next(
        (
            row
            for row in complaint
            if row["segment"] == "No Complaint"
        ),
        None
    )

    if complained and no_complaint:
        difference = (
            complained["churn_rate"]
            - no_complaint["churn_rate"]
        )

        if difference > 0:
            insights.append(
                f"Customers with complaints show a "
                f"{difference * 100:.1f} percentage-point higher "
                "predicted churn rate than customers without complaints."
            )

    tenure = segments.get(
        "tenure",
        []
    )

    if tenure:
        highest = max(
            tenure,
            key=lambda row: row["churn_rate"]
        )

        insights.append(
            f'{highest["segment"]} is the tenure segment with the '
            f'highest predicted churn rate '
            f'({highest["churn_rate"] * 100:.1f}%).'
        )

    category = segments.get(
        "order_category",
        []
    )

    if category:
        highest = max(
            category,
            key=lambda row: row["churn_rate"]
        )

        insights.append(
            f'{highest["segment"]} is the highest-risk order category '
            f'({highest["churn_rate"] * 100:.1f}% predicted churn rate).'
        )

    return insights


def get_global_analytics(predictions_df):

    risk_counts = (
        predictions_df["risk_level"]
        .value_counts()
        .to_dict()
    )

    return {
        "total_customers":
            len(predictions_df),

        "high_risk":
            risk_counts.get(
                "High Risk",
                0
            ),

        "medium_risk":
            risk_counts.get(
                "Medium Risk",
                0
            ),

        "low_risk":
            risk_counts.get(
                "Low Risk",
                0
            ),

        "average_churn_probability":
            predictions_df[
                "churn_probability"
            ].mean()
    }


def get_global_feature_importance():

    rf_model = model.named_steps[
        "model"
    ]

    preprocessor = model.named_steps[
        "preprocessor"
    ]

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

    importance_df = pd.DataFrame({

        "feature":
            feature_names,

        "importance":
            rf_model.feature_importances_

    })

    return importance_df.sort_values(
        "importance",
        ascending=False
    )


def get_global_report(predictions_df):

    analytics = get_global_analytics(
        predictions_df
    )

    importance = (
        get_global_feature_importance()
    )

    analytics["top_features"] = (
        importance
        .head(10)
        .to_dict(
            orient="records"
        )
    )

    # --------------------------------------------------------
    # BUSINESS SEGMENTS
    # --------------------------------------------------------

    segments = {

        "satisfaction":
            _satisfaction_segments(
                predictions_df
            ),

        "complaint":
            _complaint_segments(
                predictions_df
            ),

        "tenure":
            _tenure_segments(
                predictions_df
            ),

        "order_category":
            _segment_analysis(
                predictions_df,
                "preferred_order_category"
            )
    }

    analytics["segments"] = segments

    analytics["business_insights"] = (
        _business_insights(
            predictions_df,
            segments
        )
    )

    return analytics
