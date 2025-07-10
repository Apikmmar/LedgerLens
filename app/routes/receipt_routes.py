import boto3
import uuid
import os
import json
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from lambda_functions.extract_lambda import lambda_handler as extract_lambda_handler

load_dotenv()

receipt_routes = Blueprint("receipt", __name__)
dynamodb = boto3.resource('dynamodb')

@receipt_routes.route('/receipts', methods=['GET'])
def receipts():
    try:
        table = dynamodb.Table(os.environ.get("DDB_TABLE_NAME"))

        if not table:
            return "DynamoDB table not found", 404
        
        response = table.scan()
        items = response.get('Items', [])
        
        for r in items:
            if "totalAmount" in r:
                r["totalAmount"] = float(r["totalAmount"])
                
            if "billDate" in r:
                if isinstance(r["billDate"], str):
                    try:
                        date_parts = r["billDate"].split('-')
                        if len(date_parts) == 3:
                            r["billDate"] = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                    except:
                        pass
                else:
                    try:
                        r["billDate"] = r["billDate"].strftime("%d/%m/%Y")
                    except:
                        r["billDate"] = str(r["billDate"])
                        
        grouped = defaultdict(list)
        
        for r in items:
            grouped[r.get("billDate", "Unknown Date")].append(r)
            
        groyped_items = dict(sorted(
            grouped.items(), 
            key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"),, 
            reverse=True)
)
        
        return render_template("receipts.html", receipts=items)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500