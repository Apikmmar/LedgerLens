import boto3
import uuid
import os
import json
from flask import Blueprint, render_template, request, jsonify
from lambda_functions.extract_lambda import lambda_handler as extract_lambda_handler

main = Blueprint("main", __name__)
s3 = boto3.client('s3')

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