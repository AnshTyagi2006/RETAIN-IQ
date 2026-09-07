from scripts.data_ingestion import prepare_dataset
from scripts.bulk_prediction import predict_bulk


file_path = r"Data\raw\E Commerce Dataset.xlsx"

result = prepare_dataset(file_path)

if not result["success"]:

    print("Data ingestion failed.")
    print(result["error"])
    print(result["missing_columns"])

else:

    customers = result["data"]

    predictions = predict_bulk(customers)

    print("\n===== BULK PREDICTION TEST =====")

    print("Customers analyzed:", len(predictions))

    print("\nRisk distribution:")
    print(predictions["risk_level"].value_counts())

    print("\nAverage churn probability:")
    print(predictions["churn_probability"].mean())

    print("\nSample predictions:")
    print(
        predictions[
            ["prediction", "churn_probability", "risk_level"]
        ].head(10)
    )