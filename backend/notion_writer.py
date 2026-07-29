import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_SUMMARY_TOKEN = os.getenv("NOTION_SUMMARY_TOKEN")
DATABASE_ID = os.getenv("MEETING_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_SUMMARY_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def write_summary(summary):

    url = "https://api.notion.com/v1/pages"

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {

            "Name": {
                "title": [
                    {
                        "text": {
                            "content": "Meeting Summary"
                        }
                    }
                ]
            },

            "Date": {
                "date": {
                    "start": datetime.now().strftime("%Y-%m-%d")
                }
            },

            "Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": summary["summary"]
                        }
                    }
                ]
            },

            "Decisions": {
                "rich_text": [
                    {
                        "text": {
                            "content": ", ".join(summary["decisions"])
                        }
                    }
                ]
            },

            "Actions": {
                "rich_text": [
                    {
                        "text": {
                            "content": ", ".join(summary["actions"])
                        }
                    }
                ]
            },

            "Next Steps": {
                "rich_text": [
                    {
                        "text": {
                            "content": ", ".join(
                                        f'{step["responsible"]} - {step["description"]}'
                                        if isinstance(step, dict) else str(step)
                                        for step in summary["next_steps"])
                        }
                    }
                ]
            }

        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("✅ Meeting summary saved to Notion")
    else:
        print("❌ Error writing to Notion")
        print(response.text)