from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import hmac
import hashlib
import json
import os
from dotenv import load_dotenv
from utils import insert_into_supabase  # update_supabase_row if needed

load_dotenv()

# Notion verification token (not a secret key)
NOTION_VERIFICATION_TOKEN = os.getenv("NOTION_VERIFICATION_TOKEN")

app = FastAPI()


def verify_signature(body: bytes, signature: str, token: str) -> bool:
    body_str = body.decode("utf-8")
    body_json = json.loads(body_str)
    body_minified = json.dumps(body_json, separators=(",", ":"))

    hmac_obj = hmac.new(
        token.encode("utf-8"),
        body_minified.encode("utf-8"),
        hashlib.sha256
    )
    calculated_signature = "sha256=" + hmac_obj.hexdigest()
    return hmac.compare_digest(calculated_signature, signature)


@app.post("/notion-webhook")
async def notion_webhook(
    request: Request,
    x_notion_signature: str = Header(None)
):
    body_bytes = await request.body()

    # Verify Notion webhook signature
    if not verify_signature(body_bytes, x_notion_signature, NOTION_VERIFICATION_TOKEN):
        return JSONResponse(status_code=401, content={"error": "Invalid signature"})

    body = json.loads(body_bytes)

    # Handle subscription verification
    if "challenge" in body:
        return JSONResponse(content={"challenge": body["challenge"]})

    # Handle events
    events = body.get("events", [])
    for event in events:
        if event["type"] == "page.updated":
            page = event["payload"]
            props = page.get("properties", {})

            name = props.get("name", {}).get("title", [{}])[0].get("plain_text", "")
            content = props.get("content", {}).get("rich_text", [{}])[0].get("plain_text", "")
            notion_id = page.get("id")

            # Push to Supabase
            insert_into_supabase(name, content, notion_id)

    return {"status": "success"}
