import pandas as pd
import joblib
import shap

from scripts.retention_engine import generate_retention_action, retention_action_to_recommendation


MODEL_PATH = "models/retainiq_model.joblib"


model = joblib.load(MODEL_PATH)

rf_model = model.named_steps["model"]
preprocessor = model.named_steps["preprocessor"]

explainer = shap.TreeExplainer(rf_model)


def get_risk_level(probability):

    if probability >= 0.70:
        return "High Risk"

    if probability >= 0.40:
        return "Medium Risk"

    return "Low Risk"


def clean_feature_name(feature):

    feature = feature.replace("num__", "")
    feature = feature.replace("remainder__", "")
    feature = feature.replace("cat__", "")

    parts = feature.split("_")

    return " ".join(parts).title()

def format_feature(feature, customer):

    feature = feature.replace("num__", "")
    feature = feature.replace("remainder__", "")

    if feature.startswith("cat__"):

        feature = feature.replace("cat__", "", 1)

        for column in [
            "preferred_login_device",
            "preferred_payment_mode",
            "gender",
            "preferred_order_category",
            "marital_status"
        ]:

            prefix = column + "_"

            if feature.startswith(prefix):

                value = feature[len(prefix):]

                return {
                    "feature": column.replace("_", " ").title(),
                    "value": value,
                }

    return {
        "feature": feature.replace("_", " ").title(),
        "value": customer.get(feature)
    }


def get_customer_prediction(customer):

    customer_df = pd.DataFrame([customer])

    prediction = model.predict(customer_df)[0]
    probability = model.predict_proba(customer_df)[0][1]

    risk_level = get_risk_level(probability)

    customer_transformed = preprocessor.transform(customer_df)

    shap_values = explainer.shap_values(customer_transformed)

    feature_names = preprocessor.get_feature_names_out()
    customer_shap = shap_values[0, :, 1]

    shap_df = pd.DataFrame({
        "feature": feature_names,
        "shap_value": customer_shap
    })

    categorical_columns = [
    "preferred_login_device",
    "preferred_payment_mode",
    "gender",
    "preferred_order_category",
    "marital_status"
    ]

    valid_features = []

    for feature in feature_names:

        if feature.startswith(("num__", "remainder__")):
            valid_features.append(feature)

        elif feature.startswith("cat__"):
            encoded = feature.replace("cat__", "", 1)

            for column in categorical_columns:
                prefix = column + "_"

                if encoded.startswith(prefix):
                    value = encoded[len(prefix):]

                    if value == str(customer[column]):
                        valid_features.append(feature)

                    break

    shap_df = shap_df[
        shap_df["feature"].isin(valid_features)
    ]

    risk_factors = (
        shap_df[shap_df["shap_value"] > 0]
        .sort_values("shap_value", ascending=False)
        .head(5)
    )

    protective_factors = (
        shap_df[shap_df["shap_value"] < 0]
        .sort_values("shap_value")
        .head(5)
    )

    risk_results = []

    for _, row in risk_factors.iterrows():

        info = format_feature(row["feature"], customer)

        risk_results.append({
            **info,
            "impact": float(row["shap_value"])
        })


    protective_results = []

    for _, row in protective_factors.iterrows():

        info = format_feature(row["feature"], customer)

        protective_results.append({
            **info,
            "impact": float(row["shap_value"])
    })


    retention_action = generate_retention_action(
        customer,
        risk_level
    )

    return {
        "prediction": int(prediction),
        "probability": float(probability),
        "risk_level": risk_level,
        "risk_factors": risk_results,
        "protective_factors": protective_results,
        "retention_action": retention_action,
        "recommendation": retention_action_to_recommendation(
            retention_action
        )
    }


