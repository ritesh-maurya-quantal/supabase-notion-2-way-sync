from notion_client import Client as NotionClient
from supabase import create_client
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# Notion Setup
notion = NotionClient(auth=os.getenv("NOTION_TOKEN"))
NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID")

# Supabase Setup
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE")


def fetch_notion_data():
    results = notion.databases.query(database_id=NOTION_DB_ID)["results"]
    data = []
    for page in results:
        props = page["properties"]
        row = {
            "id": page["id"],
            "title": props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else "",
            "last_updated": page["last_edited_time"]
        }
        data.append(row)
    return pd.DataFrame(data)


def fetch_supabase_data():
    data = supabase.table(SUPABASE_TABLE).select("*").execute().data
    return pd.DataFrame(data)


def update_notion_row(notion_id, title):
    notion.pages.update(
        page_id=notion_id,
        properties={
            "Name": {"title": [{"text": {"content": title}}]}
        }
    )


def update_supabase_row(supa_id, title):
    supabase.table(SUPABASE_TABLE).update({"title": title}).eq("id", supa_id).execute()


def insert_into_notion(title):
    notion.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties={
            "Name": {"title": [{"text": {"content": title}}]}
        }
    )


def insert_into_supabase(title):
    supabase.table(SUPABASE_TABLE).insert({"title": title}).execute()
