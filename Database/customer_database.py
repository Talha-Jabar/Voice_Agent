import json
import random

DATABASE_FILE = "customer_database.json"

def create_dummy_database():
    customers = [
        {
            "customer_id": "CUST001",
            "name": "Alice Johnson",
            "product(s)": ["Organic Apples", "Whole Wheat Bread"],
            "order_id": "ORD1001",
            "location": "New York, NY",
            "price": 35.50,
            "paid_status": "paid",
            "payment_method": "credit_card",
            "complain": "",
            "complain_id": "",
            "status": "delivered",
            "sentiment": "",
            "review": "",
            "conversation_history": []
        },
        {
            "customer_id": "CUST002",
            "name": "Bob Williams",
            "product(s)": ["Almond Milk", "Granola Bars"],
            "order_id": "ORD1002",
            "location": "Los Angeles, CA",
            "price": 22.00,
            "paid_status": "pending",
            "payment_method": "paypal",
            "complain": "",
            "complain_id": "",
            "status": "shipped",
            "sentiment": "",
            "review": "",
            "conversation_history": []
        },
        {
            "customer_id": "CUST003",
            "name": "Charlie Brown",
            "product(s)": ["Greek Yogurt", "Fresh Berries"],
            "order_id": "ORD1003",
            "location": "Chicago, IL",
            "price": 15.75,
            "paid_status": "paid",
            "payment_method": "debit_card",
            "complain": "",
            "complain_id": "",
            "status": "delivered",
            "sentiment": "",
            "review": "",
            "conversation_history": []
        },
        {
            "customer_id": "CUST004",
            "name": "Diana Miller",
            "product(s)": ["Chicken Breast", "Organic Broccoli"],
            "order_id": "ORD1004",
            "location": "Houston, TX",
            "price": 45.00,
            "paid_status": "paid",
            "payment_method": "credit_card",
            "complain": "",
            "complain_id": "",
            "status": "delivered",
            "sentiment": "",
            "review": "",
            "conversation_history": []
        },
        {
            "customer_id": "CUST005",
            "name": "Ethan Davis",
            "product(s)": ["Pasta", "Tomato Sauce", "Parmesan Cheese"],
            "order_id": "ORD1005",
            "location": "Phoenix, AZ",
            "price": 12.50,
            "paid_status": "pending",
            "payment_method": "cash_on_delivery",
            "complain": "",
            "complain_id": "",
            "status": "processing",
            "sentiment": "",
            "review": "",
            "conversation_history": []
        }
    ]
    with open(DATABASE_FILE, "w") as f:
        json.dump(customers, f, indent=4)

def get_customers():
    try:
        with open(DATABASE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_customer_by_id(customer_id):
    customers = get_customers()
    for customer in customers:
        if customer["customer_id"] == customer_id:
            return customer
    return None

def update_customer_data(customer_id, updated_data):
    customers = get_customers()
    found = False
    for i, customer in enumerate(customers):
        if customer["customer_id"] == customer_id:
            customers[i].update(updated_data)
            found = True
            break
    if found:
        with open(DATABASE_FILE, "w") as f:
            json.dump(customers, f, indent=4)
        return True
    return False

def get_random_customer():
    customers = get_customers()
    if customers:
        return random.choice(customers)
    return None

# Create the dummy database if it doesn't exist
if not get_customers():
    create_dummy_database()


