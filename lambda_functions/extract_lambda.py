import boto3
import os
import uuid
import json
import base64
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import unquote_plus
from lambda_functions.prompt import prompt

load_dotenv()

s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")
bedrock = boto3.client("bedrock-runtime")

LEDGER_TABLE = os.environ.get("DDB_TABLE_NAME")
ARCHIVE_FOLDER = "processed/"

def lambda_handler(event, context):
    try:
        bucket = event["bucket"]
        key = unquote_plus(event["key"])
        tmp_path = f"/tmp/{uuid.uuid4()}.jpg"
        s3.download_file(bucket, key, tmp_path)
        
        with open(tmp_path, "rb") as f:
            image_data = f.read()
            
        encoded_image = base64.b64encode(image_data).decode("utf-8")
            
        body = {
            "anthropic_version": "2023-05-14",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": encoded_image
                            }
                        }
                    ]
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId="anthropic.claude-sonnet-4-20250514-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        result = json.loads(response["body"].read().decode("utf-8"))
        bill_id = str(uuid.uuid4())
        
        table = ddb.Table(LEDGER_TABLE)
        table.put_item(
            Item={
            "bill_id": bill_id,
            "timestamp": datetime.utcnow().isoformat(),
            "s3_key": key,
            "data": result
        })
        
        new_key = key.replace("uploads/", ARCHIVE_FOLDER)
        s3.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": key},
            Key=new_key
        )
        s3.delete_object(Bucket=bucket, Key=key)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Receipt processed successfully",
                "bill_id": bill_id
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }