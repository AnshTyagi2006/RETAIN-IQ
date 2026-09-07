import requests

url = "http://127.0.0.1:5000/bulk_predict"

with open(r"Data\processed\ecommerce_churn_clean.csv", "rb") as file:

    response = requests.post(
        url,
        files={"file": file}
    )

print("Status:", response.status_code)
print(response.json())