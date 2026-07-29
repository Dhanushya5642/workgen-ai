import requests
import json
import os
from dotenv import load_dotenv

# ======================
# LOAD ENV VARIABLES
# ======================

load_dotenv()

NOTION_JOURNAL_TOKEN = os.getenv("NOTION_JOURNAL_TOKEN")
DATABASE_ID = "27e61e92-5a94-81c6-a160-ed144b73e771"

headers = {
    "Authorization": f"Bearer {NOTION_JOURNAL_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# ======================
# GET PAGE CONTENT
# ======================

def get_page_content(page_id):

    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    res = requests.get(url, headers=headers)
    data = res.json()

    text = []

    for block in data.get("results", []):

        if block["type"] == "paragraph":

            for t in block["paragraph"]["rich_text"]:
                text.append(t["plain_text"])

    return "\n".join(text)


# ======================
# QUERY DATABASE
# ======================

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

response = requests.post(url, headers=headers)

data = response.json()

journals = []

for page in data.get("results", []):

    page_id = page["id"]

    title = "Untitled"

    props = page.get("properties", {})

    for p in props.values():

        if p["type"] == "title" and p["title"]:
            title = p["title"][0]["plain_text"]

    content = get_page_content(page_id)

    journals.append({
        "title": title,
        "content": content
    })


# ======================
# SAVE FILE
# ======================

with open("knowledge_base.json", "w", encoding="utf-8") as f:
    json.dump(journals, f, indent=4, ensure_ascii=False)

print("Extracted", len(journals), "full journal entries")