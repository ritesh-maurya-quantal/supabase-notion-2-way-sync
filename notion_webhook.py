from fastapi import FastAPI, Request, Header
from utils import insert_into_supabase, update_supabase_row
import hmac, hashlib, os, json
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

    for event in payload.get("events", []):
        if event["type"] == "page.updated":
            page = event["payload"]

            props = page.get("properties", {})
            name = props.get("name", {}).get("title", [{}])[0].get("plain_text", "")
            content = props.get("content", {}).get("rich_text", [{}])[0].get("plain_text", "")
            notion_id = page["id"]

            # You can check Supabase to see if it exists or not
            # For now, assume insert (can add conflict handling later)
            insert_into_supabase(name, content, notion_id)

    return {"status": "success"}