from scripts.database import save_customer


customer = {
    "CustomerID": "TEST001",
    "tenure": 12,
    "city_tier": 1,
    "order_count": 5,
    "days_since_last_order": 20,
    "cashback_amount": 500,
    "satisfaction_score": 4,
    "preferred_order_category": "Laptop & Accessory",
    "preferred_payment_mode": "Debit Card",
    "preferred_login_device": "Mobile Phone",
    "gender": "Male",
    "marital_status": "Single",
    "complain": 0
}


success = save_customer(customer)


print(
    "Customer saved:",
    success
)