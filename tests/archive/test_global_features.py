from scripts.data_ingestion import prepare_dataset
from scripts.bulk_prediction import predict_bulk
from scripts.global_analytics import get_global_feature_importance


file_path = r"Data\raw\E Commerce Dataset.xlsx"

ingestion = prepare_dataset(file_path)

if not ingestion["success"]:

    print("Data ingestion failed.")
    print(ingestion["error"])

else:

    customers = ingestion["data"]

    predictions = predict_bulk(customers)

    importance = get_global_feature_importance()

    print("\n===== GLOBAL FEATURE IMPORTANCE =====")

    print(
        importance.head(15).to_string(index=False)
    )