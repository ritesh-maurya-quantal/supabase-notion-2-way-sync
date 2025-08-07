from utils import (
    fetch_notion_data, fetch_supabase_data,
    update_notion_row, update_supabase_row,
    insert_into_notion, insert_into_supabase
)
import pandas as pd

def sync():
    notion_df = fetch_notion_data()
    supa_df = fetch_supabase_data()

    # Convert timestamps to datetime
    notion_df["last_updated"] = pd.to_datetime(notion_df["last_updated"])
    supa_df["last_updated"] = pd.to_datetime(supa_df["last_updated"])

    # Match by title for simplicity (add more robust matching in production)
    for _, supa_row in supa_df.iterrows():
        match = notion_df[notion_df["title"] == supa_row["title"]]
        if not match.empty:
            notion_row = match.iloc[0]
            if supa_row["last_updated"] > notion_row["last_updated"]:
                update_notion_row(notion_row["id"], supa_row["title"])
            elif notion_row["last_updated"] > supa_row["last_updated"]:
                update_supabase_row(supa_row["id"], notion_row["title"])
        else:
            insert_into_notion(supa_row["title"])

    for _, notion_row in notion_df.iterrows():
        match = supa_df[supa_df["title"] == notion_row["title"]]
        if match.empty:
            insert_into_supabase(notion_row["title"])


if __name__ == "__main__":
    sync()
