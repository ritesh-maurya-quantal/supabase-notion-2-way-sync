from fastapi import FastAPI, Request, Header
from utils import update_supabase_row, insert_into_supabase
import hmac
import hashlib
import os
import json
from dotenv import load_dotenv

load_dotenv()
NOTION_SIGNING_SECRET = os.getenv("NOTION_SIGNING_SECRET")

app = FastAPI()

def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        key=secret.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

@app.post("/notion-webhook")
async def notion_webhook(request: Request, notion_signature: str = Header(None)):
    body = await request.body()
    if not verify_signature(body, notion_signature, NOTION_SIGNING_SECRET):
        return {"status": "invalid signature"}

    payload = await request.json()
    print("Received webhook payload:", json.dumps(payload, indent=2))

    for event in payload.get("events", []):
        if event["type"] == "page.updated":
            title = event["payload"]["properties"]["Name"]["title"][0]["plain_text"]
            notion_id = event["payload"]["id"]
            # Update or insert in Supabase
            update_or_insert_in_supabase(notion_id, title)

    return {"status": "success"}
