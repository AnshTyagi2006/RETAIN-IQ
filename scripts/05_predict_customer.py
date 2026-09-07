import pandas as pd
import joblib
import shap


# Load model
model = joblib.load("models/retainiq_model.joblib")
print("Model loaded successfully.")


# Customer data
customer = {
    "tenure": 5,
    "preferred_login_device": "Mobile Phone",
    "city_tier": 1,
    "warehouse_to_home": 15,
    "preferred_payment_mode": "UPI",
    "gender": "Male",
    "hour_spend_on_app": 3,
    "number_of_device_registered": 4,
    "preferred_order_category": "Mobile Phone",
    "satisfaction_score": 3,
    "marital_status": "Single",
    "number_of_address": 2,
    "complain": 0,
    "order_amount_hike_from_last_year": 10,
    "coupon_used": 2,
    "order_count": 3,
    "days_since_last_order": 10,
    "cashback_amount": 200
}


# Prediction
def predict_customer(customer):
    customer_df = pd.DataFrame([customer])

    prediction = model.predict(customer_df)[0]
    probability = model.predict_proba(customer_df)[0][1]

    if probability >= 0.70:
        risk = "High Risk"
    elif probability >= 0.40:
        risk = "Medium Risk"
    else:
        risk = "Low Risk"

    return prediction, probability, risk


prediction, probability, risk = predict_customer(customer)

print("\n===== CUSTOMER PREDICTION =====")
print("Prediction:", prediction)
print(f"Churn Probability: {probability:.4f}")
print(f"Churn Probability: {probability * 100:.2f}%")
print("Risk Level:", risk)


# SHAP explanation
customer_df = pd.DataFrame([customer])

rf_model = model.named_steps["model"]
preprocessor = model.named_steps["preprocessor"]

customer_transformed = preprocessor.transform(customer_df)

explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(customer_transformed)

feature_names = preprocessor.get_feature_names_out()
customer_shap = shap_values[0, :, 1]

shap_df = pd.DataFrame({
    "feature": feature_names,
    "shap_value": customer_shap
})


# Keep only features that apply to this customer
categorical_columns = [
    "preferred_login_device",
    "preferred_payment_mode",
    "gender",
    "preferred_order_category",
    "marital_status"
]

valid_features = []

for feature in feature_names:

    if feature.startswith("num__"):
        valid_features.append(feature)

    elif feature.startswith("remainder__"):
        valid_features.append(feature)

    elif feature.startswith("cat__"):
        encoded_feature = feature.replace("cat__", "", 1)

        for column in categorical_columns:
            prefix = column + "_"

            if encoded_feature.startswith(prefix):
                encoded_value = encoded_feature[len(prefix):]

                if encoded_value == str(customer[column]):
                    valid_features.append(feature)

                break


shap_df = shap_df[shap_df["feature"].isin(valid_features)]


# Risk and protective factors
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


print("\n===== TOP CHURN RISK FACTORS =====")

for _, row in risk_factors.iterrows():
    print(f"{row['feature']}: +{row['shap_value']:.4f}")


print("\n===== TOP PROTECTIVE FACTORS =====")

for _, row in protective_factors.iterrows():
    print(f"{row['feature']}: {row['shap_value']:.4f}")


# Convert feature names to readable names
def clean_feature_name(feature):
    feature = feature.replace("num__", "")
    feature = feature.replace("remainder__", "")
    feature = feature.replace("cat__", "")
    return feature.replace("_", " ")


print("\n===== HUMAN READABLE FACTORS =====")

for _, row in risk_factors.iterrows():
    print(
        f"{clean_feature_name(row['feature'])}: "
        f"+{row['shap_value']:.4f}"
    )


# Generate explanations
def generate_explanation(feature, shap_value):

    direction = "higher" if shap_value > 0 else "lower"

    explanations = {
        "num__tenure": (
            "Customer tenure is reducing the predicted churn risk."
        ),
        "num__days_since_last_order": (
            "Recent ordering activity is reducing churn risk."
            if shap_value < 0
            else "A longer time since the last order is increasing churn risk."
        ),
        "remainder__complain": (
            "The absence of a complaint is reducing predicted churn risk."
            if shap_value < 0
            else "A customer complaint is contributing toward higher churn risk."
        ),
        "num__cashback_amount": (
            "Cashback amount is contributing toward lower churn risk."
            if shap_value < 0
            else "Cashback amount is contributing toward higher churn risk."
        ),
        "num__order_count": (
            "Ordering activity is supporting customer retention."
            if shap_value < 0
            else "Lower ordering activity is contributing toward higher churn risk."
        ),
        "num__number_of_address": (
            "The customer's address activity is contributing toward lower churn risk."
            if shap_value < 0
            else "The customer's address activity is contributing toward higher churn risk."
        ),
        "num__order_amount_hike_from_last_year": (
            "The change in order amount is supporting customer retention."
            if shap_value < 0
            else "The change in order amount is contributing toward higher churn risk."
        ),
        "num__number_of_device_registered": (
            "The number of registered devices is supporting customer retention."
            if shap_value < 0
            else "The number of registered devices is contributing slightly toward higher churn risk."
        )
    }

    if feature in explanations:
        return explanations[feature]

    if feature.startswith("cat__preferred_order_category_"):
        value = feature.replace(
            "cat__preferred_order_category_", ""
        )
        return (
            f"{value} order category is contributing "
            f"toward {direction} predicted churn risk."
        )

    if feature.startswith("cat__marital_status_"):
        value = feature.replace("cat__marital_status_", "")
        return (
            f"Marital status ({value}) is contributing "
            f"toward {direction} predicted churn risk."
        )

    if feature.startswith("cat__preferred_payment_mode_"):
        value = feature.replace(
            "cat__preferred_payment_mode_", ""
        )
        return (
            f"Preferred payment mode ({value}) is contributing "
            f"toward {direction} predicted churn risk."
        )

    if feature.startswith("cat__preferred_login_device_"):
        value = feature.replace(
            "cat__preferred_login_device_", ""
        )
        return (
            f"Preferred login device ({value}) is contributing "
            f"toward {direction} predicted churn risk."
        )

    if feature.startswith("cat__gender_"):
        value = feature.replace("cat__gender_", "")
        return (
            f"Gender ({value}) is contributing slightly "
            f"toward {direction} predicted churn risk."
        )

    return (
        f"{clean_feature_name(feature)} is contributing "
        f"toward {direction} predicted churn risk."
    )


# Retention strategy
def generate_retention_strategy(probability):

    if probability < 0.40:
        return (
            "No immediate retention intervention. "
            "Continue regular customer engagement."
        )

    if probability < 0.70:
        return (
            "Monitor the customer and consider "
            "a targeted engagement campaign."
        )

    return (
        "Prioritize this customer for a retention "
        "intervention."
    )


print("\n===== RETENTION STRATEGY =====")
print(generate_retention_strategy(probability))


print("\n===== CUSTOMER INSIGHTS =====")

for _, row in risk_factors.iterrows():
    print(
        "•",
        generate_explanation(
            row["feature"],
            row["shap_value"]
        )
    )


print("\n===== PROTECTIVE INSIGHTS =====")

for _, row in protective_factors.iterrows():
    print(
        "•",
        generate_explanation(
            row["feature"],
            row["shap_value"]
        )
    )
    
    