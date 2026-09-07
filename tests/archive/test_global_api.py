import requests


url = "http://127.0.0.1:5000/analyze"

file_path = r"Data\raw\E Commerce Dataset.xlsx"

with open(file_path, "rb") as file:

    response = requests.post(
        url,
        files={"file": file}
    )


print("Status:", response.status_code)

print(response.json())