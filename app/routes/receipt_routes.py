import boto3
import uuid
import os
import json
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
from flask import Blueprint, render_template, request
from lambda_functions.extract_lambda import lambda_handler as extract_lambda_handler

load_dotenv()

receipt_routes = Blueprint("receipt", __name__)
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
bucket_name = os.environ.get("S3_BUCKET_NAME")


@receipt_routes.route('/receipts', methods=['GET'])
def receipts():
    try:
        table = dynamodb.Table(os.environ.get("DDB_TABLE_NAME"))

        if not table:
            return "DynamoDB table not found", 404

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        response = table.scan()
        items = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
            
        preprocessed_receipts(items)

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
            key=lambda x: parse_date(x[0]) or datetime.min,
            reverse=True
        ))

        total_receipts = len(items)
        total_amount = round(total_amount, 2)
        unique_locations_count = len(unique_locations)

        return render_template("receipts.html",
                               grouped_receipts=grouped_sorted,
                               total_receipts=total_receipts,
                               total_amount=total_amount,
                               unique_locations=unique_locations_count)

    except Exception as e:
        return f"An error occurred: {str(e)}", 500
    
def preprocessed_receipts(items):
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
            dt = parse_date(r["billDate"])
            if dt:
                r["billDate"] = dt.strftime("%d-%m-%Y")
            else:
                r["billDate"] = "Unknown Date"
                
        if r.get("s3_key"):
            r["download_url"] = generate_url(r["s3_key"])
        else:
            r["download_url"] = None
                
                    
def generate_url(s3_key):
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": s3_key,
                "ResponseContentDisposition": f'attachment; filename="{os.path.basename(s3_key)}"',
            },
            ExpiresIn=3600,
        )
    except Exception:
        return None

def parse_date(date_str):
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def is_date_in_range(date_str, start_dt, end_dt):
    dt = parse_date(date_str)
    if not dt:
        return False
    return start_dt <= dt <= end_dt
