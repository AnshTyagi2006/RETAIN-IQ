from scripts.data_ingestion import prepare_dataset
from scripts.bulk_prediction import predict_bulk
from scripts.global_analytics import get_global_analytics


file_path = r"Data\raw\E Commerce Dataset.xlsx"

ingestion = prepare_dataset(file_path)

if not ingestion["success"]:
    print("Data ingestion failed.")
    print(ingestion["error"])

else:
    customers = ingestion["data"]

    predictions = predict_bulk(customers)

    analytics = get_global_analytics(predictions)

    print("\n===== GLOBAL ANALYTICS =====")

    print("Total Customers:", analytics["total_customers"])
    print("High Risk:", analytics["high_risk"])
    print("Medium Risk:", analytics["medium_risk"])
    print("Low Risk:", analytics["low_risk"])

    print(
        "Average Churn Probability:",
        f"{analytics['average_churn_probability']:.2%}"
    )