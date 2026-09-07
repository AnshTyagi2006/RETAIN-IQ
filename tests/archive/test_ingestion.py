from scripts.data_ingestion import prepare_dataset


file_path = r"Data\raw\E Commerce Dataset.xlsx"

result = prepare_dataset(file_path)

print("\n===== DATA INGESTION TEST =====")

print("Success:", result["success"])

if result["success"]:

    print("Rows:", result["rows"])
    print("Columns:", result["columns"])

    print("\nModel-ready columns:")
    print(result["data"].columns.tolist())

    print("\nMapped columns:")
    print(result["mapped_columns"])

else:

    print("Error:", result["error"])

    print("\nMissing columns:")
    print(result["missing_columns"])