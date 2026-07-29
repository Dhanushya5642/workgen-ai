import json
from datetime import datetime

DB_FILE = "knowledge_base.json"


def store_meeting(meeting_data):

    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
    except:
        data = []

    entry = {
        "type": "meeting",
        "date": str(datetime.now()),
        "data": meeting_data
    }

    data.append(entry)

    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print("✅ Meeting stored in Knowledge Hub")