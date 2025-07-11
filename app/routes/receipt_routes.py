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
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                items = [r for r in items if is_date_in_range(r.get("billDate", ""), start_dt, end_dt)]
            except ValueError:
                pass

        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        for r in items:
            try:
                r["totalAmount"] = float(r.get("totalAmount", 0.0))
            except (ValueError, TypeError):
                r["totalAmount"] = 0.0
                
            for item in r.get("item_table", []):
                try:
                    item["price"] = float(item.get("price", 0.0))
                except (ValueError, TypeError):
                    item["price"] = 0.0
                try:
                    item["quantity"] = int(item.get("quantity", 0))
                except (ValueError, TypeError):
                    item["quantity"] = 0

            if "billDate" in r and isinstance(r["billDate"], str):
                date_parts = r["billDate"].split('-')
                if len(date_parts) == 3:
                    r["billDate"] = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                    
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                items = [r for r in items if is_date_in_range(r.get("billDate", ""), start_dt, end_dt)]
            except ValueError:
                pass
                        
        grouped = defaultdict(list)
        total_amount = 0.0
        unique_locations = set()
        
        for r in items:
            grouped[r.get("billDate", "Unknown Date")].append(r)
            total_amount += r.get("totalAmount", 0.0)
            
            if "spendingLocation" in r:
                unique_locations.add(r["spendingLocation"])
            
        grouped_sorted = dict(sorted(
            grouped.items(),
            key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"),
            reverse=True
        ))
        
        total_receipts = len(items)
        total_amount = round(total_amount, 2)
        unique_locations_count =  len(unique_locations)
        
        return render_template("receipts.html", grouped_receipts=grouped_sorted,
                                                total_receipts=total_receipts,
                                                total_amount=total_amount,
                                                unique_locations=unique_locations_count)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
    
def parse_date(date_str, fmt="%d/%m/%Y"):
    try:
        return datetime.strptime(date_str, fmt)
    except ValueError:
        return None
    
def is_date_in_range(date, start_dt, end_dt):
    receipt_dt = parse_date(date)
    if not receipt_dt:
        return False
    
    return start_dt <= receipt_dt <= end_dt