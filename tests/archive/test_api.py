import requests


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


response = requests.post(
    "http://127.0.0.1:5000/predict",
    json=customer
)

print("Status:", response.status_code)
print(response.json())