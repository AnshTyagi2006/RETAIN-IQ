from scripts.data_ingestion import prepare_dataset
from scripts.bulk_prediction import predict_bulk
from scripts.global_analytics import get_global_report


file_path = r"Data\raw\E Commerce Dataset.xlsx"

ingestion = prepare_dataset(file_path)

if not ingestion["success"]:
    print("Data ingestion failed.")
    print(ingestion["error"])

else:
    customers = ingestion["data"]

    predictions = predict_bulk(customers)

    report = get_global_report(predictions)

    print("\n===== GLOBAL REPORT =====")

    print("Total Customers:", report["total_customers"])
    print("High Risk:", report["high_risk"])
    print("Medium Risk:", report["medium_risk"])
    print("Low Risk:", report["low_risk"])

    print(
        "Average Churn Probability:",
        f"{report['average_churn_probability']:.2%}"
    )

    print("\nTop Global Features:")

    for feature in report["top_features"]:
        print(
            f"{feature['feature']}: "
            f"{feature['importance']:.4f}"
        )