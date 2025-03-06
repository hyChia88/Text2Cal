import streamlit as st
from datetime import datetime, timedelta
import re
from ics import Calendar, Event
import openai
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Calendar API setup
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = r"D:\ahYen's Workspace\ahYen's Work\Side projects\Text2Cal\service_account.json"

# 使用服务账号凭据
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# 创建Calendar API客户端
service = build("calendar", "v3", credentials=credentials)
st.title("📅 Schedule to iCal & Google Calendar")

# Initialize session state for edit mode
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# Default text input
default_text = """@03/04/25 
- 0930am-1030am Project Meeting
- 0200pm-0400pm Design Review

@15/05/25 
- 1000am-0900pm Overnight Hackathon
"""

# Toggle edit mode
if st.button("✏️ Edit Schedule" if not st.session_state.edit_mode else "✅ Done Editing"):
    st.session_state.edit_mode = not st.session_state.edit_mode

# Read-only text area unless in edit mode
if st.session_state.edit_mode:
    text = st.text_area("Enter your schedule:", default_text, height=300)
else:
    # Assign to text variable even in read-only mode
    text = st.text_area("Your Schedule (Read-Only)", default_text, height=300, disabled=True)

# Parsing function
def parse_input(text):
    day_schedules = [x.strip() for x in text.split("@") if x.strip()]
    parsed_events = []
    
    for schedule in day_schedules:
        lines = schedule.split("\n")
        date_str = lines[0].strip()
        events = [line.strip() for line in lines[1:] if line.strip()]
        
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%y").date()
        except ValueError:
            st.warning(f"⚠ Invalid date: {date_str}")
            continue

        for event in events:
            match = re.match(r"-\s*(\d{3,4}(am|pm))-(\d{3,4}(am|pm))?\s*(.+)", event)
            if not match:
                st.warning(f"⚠ Cannot parse: {event}")
                continue
            
            start_time, _, end_time, _, content = match.groups()
            start_dt = datetime.strptime(start_time, "%I%M%p").time()
            end_dt = datetime.strptime(end_time, "%I%M%p").time() if end_time else (datetime.combine(date_obj, start_dt) + timedelta(hours=1)).time()
            
            parsed_events.append({"date": date_obj, "start": start_dt, "end": end_dt, "content": content})

    return parsed_events

# Generate ICS function
def generate_ics(events):
    c = Calendar()
    for event in events:
        e = Event()
        e.name = event["content"]
        e.begin = datetime.combine(event["date"], event["start"])
        e.end = datetime.combine(event["date"], event["end"])
        c.events.add(e)

    filename = "schedule.ics"
    with open(filename, "w") as f:
        f.writelines(c)
    return filename

# Google Calendar Integration
def add_to_google_calendar(events):
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("calendar", "v3", credentials=creds)

    for event in events:
        event_body = {
            "summary": event["content"],
            "start": {"dateTime": datetime.combine(event["date"], event["start"]).isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": datetime.combine(event["date"], event["end"]).isoformat(), "timeZone": "UTC"},
        }
        service.events().insert(calendarId="primary", body=event_body).execute()

    st.success("✅ Events added to Google Calendar!")

# Generate & Auto-Sync ICS + Google Calendar
if st.button("📅 Generate & Sync Calendar"):
    parsed_events = parse_input(text)
    if parsed_events:
        ics_file = generate_ics(parsed_events)
        add_to_google_calendar(parsed_events)
        st.success("✅ ICS generated & events synced to Google Calendar!")
        with open(ics_file, "rb") as f:
            st.download_button("Download ICS", f, "schedule.ics")

# OpenAI Analysis
if st.button("🤖 Ask AI for Advice"):
    parsed_events = parse_input(text)
    if parsed_events:
        client = openai.OpenAI(api_key="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")  # Replace with your API key
        schedule_text = "\n".join([f"{e['date']} {e['start']}-{e['end']}: {e['content']}" for e in parsed_events])
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Here is my past week's schedule: {schedule_text}. Any advice?"}]
        )
        st.subheader("📌 AI Advice:")
        st.write(response.choices[0].message.content)