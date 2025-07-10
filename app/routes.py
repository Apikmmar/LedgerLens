import boto3
import uuid
import os
import json
from dotenv import load_dotenv
from flask import Blueprint, render_template, request, jsonify
from lambda_functions.extract_lambda import lambda_handler as extract_lambda_handler

load_dotenv()

main = Blueprint("main", __name__)
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

@main.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == "POST":
            if 'file' not in request.files:
                return "No file uploaded", 400
            
            file = request.files['file']
            
            if file.filename == '':
                return "No selected file", 400
            
            filename = f"{uuid.uuid4()}_{file.filename}"
            bucket =  os.environ.get("S3_BUCKET_NAME")
            key = f"uploads/{filename}"
            
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=file,
                ContentType=file.content_type
            )
            
            result = extract_lambda_handler({
                "bucket": bucket,
                "key": key
            }, None)
            
            return "Receipt uploaded and processed successfully", 200
        return render_template("upload.html")
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
    
@main.route('/presign', methods=['POST'])
def presign():
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_type = data.get('type')
        
        if not filename:
            return jsonify({"error": "Filename is required"}), 400
        
        bucket = os.environ.get("S3_BUCKET_NAME")
        key = f"uploads/{uuid.uuid4()}_{filename}"
        
        url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ContentType': file_type
            },
            ExpiresIn=3600
        )
        
        return jsonify({
            "url": url,
            "key": key
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@main.route('/receipts', methods=['GET'])
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
        
        return render_template("receipts.html", receipts=items)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500