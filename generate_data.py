import json
import uuid
import random
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

ddb = boto3.resource("dynamodb")
LEDGER_TABLE = os.environ.get("DDB_TABLE_NAME")

def lambda_handler(event, context):
    try:
        locations = [
            "Nasi Kandar Line Clear", "Starbucks Pavilion", "Grab", "Mr DIY", "Popular Bookstore",
            "Sunway Pharmacy", "Pizza Hut", "Guardian", "Pos Malaysia", "Rakuten Trade"
        ]
        
        categories = [
            "FOOD", "COFFEE_AND_CAFE", "TRANSPORTATION", "SHOPPING", "EDUCATION",
            "MEDICAL", "FOOD", "MEDICAL", "OTHERS", "INVESTMENT"
        ]
        
        payment_methods = ["Cash", "Credit Card", "Debit Card", "QR Pay", "Bank Transfer"]
        
        item_examples = {
            "FOOD": [("Nasi Goreng", 12.5), ("Roti Canai", 1.5), ("Teh O Ais", 2.0)],
            "COFFEE_AND_CAFE": [("Latte", 12.0), ("Muffin", 6.5)],
            "TRANSPORTATION": [("Grab Ride", 15.0)],
            "SHOPPING": [("Screwdriver Set", 20.0), ("Hooks", 5.0)],
            "EDUCATION": [("Workbook", 35.0), ("Pens", 10.0)],
            "MEDICAL": [("Panadol", 10.0), ("Mask", 5.0)],
            "OTHERS": [("Postage", 10.5)],
            "INVESTMENT": [("MYEG Shares", 500.0)],
            "RENT": [("Apartment Rent", 1200.0)]
        }
        
        data = []
        today = datetime.today()
        table = ddb.Table(LEDGER_TABLE)

        for i in range(10):
            category = categories[i]
            location = locations[i]
            bill_id = str(uuid.uuid4())
            bill_date = (today - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
            payment_method = random.choice(payment_methods)

            items = []
            total = 0.0

            for item_name, price in random.sample(item_examples[category], k=1 if len(item_examples[category]) == 1 else 2):
                quantity = random.randint(1, 2)
                total_price = round(price * quantity, 2)
                items.append({
                    "itemName": item_name,
                    "quantity": str(quantity),
                    "price": f"{price:.2f}",
                    "totalPrice": f"{total_price:.2f}"
                })
                total += total_price

            tax = round(total * 0.06, 2) if random.choice([True, False]) else ""
            total_with_tax = round(total + float(tax) if tax else total, 2)

            receipt = {
                "bill_id": bill_id,
                "billDate": bill_date,
                "spendingLocation": location,
                "totalAmount": f"{total_with_tax:.2f}",
                "taxAmount": f"{tax:.2f}" if tax != "" else "",
                "paymentMethod": payment_method,
                "item_table": items,
                "category": category
            }

            table.put_item(Item=receipt)

            data.append(receipt)

        return {
            "statusCode": 200,
            "body": json.dumps(data, indent=2)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }

if __name__ == "__main__":
    result = lambda_handler({}, {})
    print("Uploaded to DynamoDB")
    print(result["body"])