import pandas as pd

from scripts.prediction_engine import model
from scripts.retention_engine import generate_retention_action, retention_action_to_recommendation


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(probability):
    if probability >= 0.70:
        return "High Risk"

    if probability >= 0.40:
        return "Medium Risk"

    return "Low Risk"


# ============================================================
# BULK PREDICTION
# ============================================================

def predict_bulk(customers_df):
    """
    Generate fast bulk churn predictions.

    SHAP explanations are intentionally NOT calculated here.

    SHAP is calculated later for the individual customer
    selected by the user.
    """

    if customers_df is None:
        raise ValueError("customers_df cannot be None.")

    if not isinstance(customers_df, pd.DataFrame):
        raise TypeError(
            "customers_df must be a pandas DataFrame."
        )

    if customers_df.empty:
        return customers_df.copy()

    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    predictions = model.predict(
        customers_df
    )

    # --------------------------------------------------------
    # CHURN PROBABILITY
    # --------------------------------------------------------

    probabilities = model.predict_proba(
        customers_df
    )[:, 1]

    # --------------------------------------------------------
    # RESULT DATAFRAME
    # --------------------------------------------------------

    results = customers_df.copy()

    results["prediction"] = predictions

    results["churn_probability"] = probabilities

    results["risk_level"] = [
        get_risk_level(probability)
        for probability in probabilities
    ]

    # --------------------------------------------------------
    # DEFAULT VALUES
    #
    # These will be populated when an individual customer
    # is opened and SHAP analysis is requested.
    # --------------------------------------------------------

    results["risk_factors"] = [
        []
        for _ in range(len(results))
    ]

    results["protective_factors"] = [
        []
        for _ in range(len(results))
    ]

    retention_actions = []
    recommendations = []

    for _, row in results.iterrows():
        action = generate_retention_action(
            row.to_dict(),
            row["risk_level"]
        )
        retention_actions.append(action)
        recommendations.append(
            retention_action_to_recommendation(action)
        )

    results["retention_action"] = retention_actions
    results["recommendation"] = recommendations

    return results