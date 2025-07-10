prompt = """
    You are an expert in extracting information from receipts. I will provide you with a receipt from various vendors. Your task is to extract the following fields accurately:

    "BillDate": The date of bill in the format YYYY-MM-DD.
    "SpendingLocation": The location/store/restaurant of the bill.
    "TotalAmount": The paid amount in the format 123.45 (also known as 'Total', 'Total Paid', 'Net Total').
    "TaxAmount": The tax amount in the format 123.45 (also known as 'Tax', 'Tax Amount', 'SST Charges'). Only extract if it is present.
    "PaymentMethod": The payment method used, such as 'Cash', 'Credit Card', 'Debit Card', 'QR Pay' and etc. Only extract if it is present.

    Create an "item_table" that includes the following fields:
    "ItemName": The name of the item purchased.
    "Quantity": The quantity of the item purchased.
    "Price": The price of the item in the format 123.45.
    "TotalPrice": The total price for the item in the format 123.45.

    Please include all the information in the item table in the JSON object as an array of objects.

    After you extract all those information, please determine if the extracted data is from which category below:
    FOOD,
    TRANSPORTATION,
    EDUCATION,
    SHOPPING,
    COFFEE_AND_CAFE,
    RENT,
    MEDICAL,
    INVESTMENT,
    OTHERS

    Return only a valid JSON object with exactly these keys and no extra text. If a field is not found, output an empty string.

    Example format:
    {
        BillDate": "2024-01-15",
        "SpendingLocation": "ABC Restaurant",
        "TotalAmount": "45.60",
        "TaxAmount": "2.74",
        "PaymentMethod": "Credit Card",
        "item_table": [
            {
                "ItemName": "Burger",
                "Quantity": "1",
                "Price": "15.90",
                "TotalPrice": "15.90"
            }
        ],
        "Category": "FOOD"
    }
"""