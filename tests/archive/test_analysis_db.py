from scripts.database import (
    create_dataset,
    save_customer_analysis
)


customer = {
    "CustomerID": "TEST002",
    "tenure": 10,
    "city_tier": 1,
    "order_count": 8,
    "days_since_last_order": 15,
    "cashback_amount": 350,
    "satisfaction_score": 4,
    "preferred_order_category": "Laptop & Accessory",
    "preferred_payment_mode": "Debit Card",
    "preferred_login_device": "Mobile Phone",
    "gender": "Male",
    "marital_status": "Single",
    "complain": 0
}


result = {
    "probability": 0.78,
    "prediction": 1,
    "risk_level": "High Risk",
    "recommendation":
        "Immediate retention intervention recommended.",

    "risk_factors": [
        {
            "feature":
                "days_since_last_order",
            "value": 15,
            "impact": 0.42
        }
    ],

    "protective_factors": [
        {
            "feature":
                "satisfaction_score",
            "value": 4,
            "impact": -0.21
        }
    ]
}


dataset_id = create_dataset(
    "Database Test",
    "MANUAL"
)


saved = save_customer_analysis(
    customer,
    result,
    dataset_id
)


print(
    "Dataset ID:",
    dataset_id
)

print(
    "Complete analysis saved:",
    saved
)