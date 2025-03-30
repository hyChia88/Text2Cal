# Notion Calendar Auto-Importer Script
import os
import requests
import re
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# Load environment variables
NOTION_API_TOKEN = 'ntn_h72840704006oMsex3XAi8SMP9AbMipmtM42hvvalVm5as'
NOTION_DATABASE_ID = '17b1b22a180080caa0d5c2a1bd062d88'

print(f"Token: {NOTION_API_TOKEN}")

# Notion API endpoint
NOTION_API_URL = f'https://api.notion.com/v1/pages'
HEADERS = {
    'Authorization': f'Bearer {NOTION_API_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}


def parse_event(input_text):
    pattern = r'@([A-Za-z]+ \d{1,2}, \d{4})\s+(\d{1,2})(am|pm)-(\d{1,2})(am|pm)\s+(.*)'
    match = re.match(pattern, input_text)
    if match:
        date_str, start_hour, start_ampm, end_hour, end_ampm, content = match.groups()

        start_time = f"{start_hour}:00 {start_ampm}"
        end_time = f"{end_hour}:00 {end_ampm}"

        start_datetime = datetime.strptime(f"{date_str} {start_time}", "%B %d, %Y %I:%M %p")
        end_datetime = datetime.strptime(f"{date_str} {end_time}", "%B %d, %Y %I:%M %p")

        return {
            'start': start_datetime.isoformat(),
            'end': end_datetime.isoformat(),
            'content': content
        }
    else:
        raise ValueError("Invalid input format")


def create_notion_event(event):
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "To-do": {
                "title": [
                    {
                        "text": {
                            "content": event['content']
                        }
                    }
                ]
            },
            "Dates": {
                "date": {
                    "start": event['start'],
                    "end": event['end']
                }
            }
        }
    }

    response = requests.post(NOTION_API_URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"Event '{event['content']}' added successfully!")
    else:
        print(f"Failed to add event: {response.status_code}, {response.text}")


def main():
    input_text = input("Enter event (e.g., @March 11, 2025 12pm-2pm Prethesis assign): ")
    try:
        event = parse_event(input_text)
        create_notion_event(event)
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
