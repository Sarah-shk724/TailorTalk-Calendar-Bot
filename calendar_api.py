from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import streamlit as st
import json

SCOPES = ['https://www.googleapis.com/auth/calendar']

# ✅ Securely load credentials from Streamlit secrets
SERVICE_ACCOUNT_INFO = json.loads(st.secrets["GOOGLE_CREDENTIALS"])

credentials = service_account.Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES
)

# Build the Google Calendar service
service = build('calendar', 'v3', credentials=credentials)

# ✅ Function to get calendar events
def get_calendar_events():
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

# ✅ Function to book a calendar event
def book_calendar_event(summary, start_time, end_time):
    event = {
        'summary': summary,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'}
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event
