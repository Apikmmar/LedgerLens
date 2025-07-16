import boto3
import os
import uuid
import json
import base64
import time
import botocore.exceptions
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
        filename = os.path.basename(key)
        ext = os.path.splitext(filename)[1] or ".png"

        tmp_dir = "/tmp" if os.name != "nt" else os.getenv("TEMP", "C:\\Temp")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4()}{ext}")

        s3.download_file(bucket, key, tmp_path)

        with open(tmp_path, "rb") as f:
            image_data = f.read()

        encoded_image = base64.b64encode(image_data).decode("utf-8")

        body = {
            "anthropic_version": "bedrock-2023-05-31",
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
                                "media_type": "image/png",
                                "data": encoded_image
                            }
                        }
                    ]
                }
            ]
        }

        response = call_bedrock_retry(body)

        raw_text = response["body"].read().decode("utf-8")
        parsed_response = json.loads(raw_text)

        structured_text = parsed_response["content"][0]["text"]
        usage = parsed_response.get("usage", {})

        raw_result = json.loads(structured_text)
        bill_id = str(uuid.uuid4())
        result = preprocess_result(raw_result, bill_id)

        new_filename = f"{bill_id}{ext}"
        new_key = os.path.join(ARCHIVE_FOLDER, new_filename).replace("\\", "/")

        s3.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": key},
            Key=new_key
        )
        s3.delete_object(Bucket=bucket, Key=key)

        table = ddb.Table(LEDGER_TABLE)
        table.put_item(
            Item={
                **result,
                "s3_key": new_key,
                "timestamp": datetime.utcnow().isoformat(),
                "token_usage": {
                    "input": usage.get("input_tokens", 0),
                    "output": usage.get("output_tokens", 0),
                    "total": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                }
            }
        )

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
        
def call_bedrock_retry(payload, max_retries=5, base_delay=1):
    for attempt in range(max_retries):
        try:
            return bedrock.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json"
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "ThrottlingException" and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"[RETRY] Throttled. Waiting {delay}s before retrying...")
                time.sleep(delay)
            else:
                raise
        
def preprocess_billDate(date_str):
    """Covert date string to dd-mm-yyyy format."""
    
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return date_str

def preprocess_result(raw, bill_id):
    normalized = {k.lower(): v for k, v in raw.items()}
    
    processed = {
        "bill_id": bill_id,
        "billDate": preprocess_billDate(normalized.get("billdate", "")),
        "category": normalized.get("category", "").upper(),
        "paymentMethod": normalized.get("paymentmethod", "").title(),
        "spendingLocation": normalized.get("spendinglocation", ""),
        "taxAmount": str(normalized.get("taxamount", "0.00") or "0.00"),
        "totalAmount": str(normalized.get("totalamount", "0.00") or "0.00"),
        "item_table": []
    }
    
    items = normalized.get("item_table", [])
    for item in items:
        item_normalized = {k.lower(): v for k, v in item.items()}
        processed["item_table"].append({
            "itemName": item_normalized.get("itemname", ""),
            "quantity": str(item_normalized.get("quantity", "0")),
            "price": str(item_normalized.get("price", "0.00") or "0.00"),
            "totalPrice": str(item_normalized.get("totalprice", "0.00") or "0.00")
        })
    
    return processed
