import os
import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *
from datetime import datetime, timezone

# --- CONFIGURATION ---
LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
CALENDAR_ID = os.getenv('LARK_CALENDAR_ID', 'primary') # Default to user's primary calendar if not set

# Use explicit URL for Lark (Global)
client = lark.Client.builder() \
    .app_id(LARK_APP_ID) \
    .app_secret(LARK_APP_SECRET) \
    .domain("https://open.larksuite.com") \
    .build()

def get_calendar_events(start_dt, end_dt):
    """
    Larkカレンダーから指定期間の予定を取得する
    start_dt, end_dt: datetime objects
    """
    # Lark API requires timestamp in strings or integers depending on endpoint, 
    # List events usually takes start_time and end_time as unix timestamp string
    
    req = ListCalendarEventRequest.builder() \
        .calendar_id(CALENDAR_ID) \
        .start_time(str(int(start_dt.timestamp()))) \
        .end_time(str(int(end_dt.timestamp()))) \
        .build()

    resp = client.calendar.v4.calendar_event.list(req)
    
    if not resp.success():
        print(f"Error fetching events: {resp.code}, {resp.msg}")
        return []

    events = []
    if resp.data and resp.data.items:
        for item in resp.data.items:
            # Timestamp to datetime
            start_ts = int(item.start_time.timestamp)
            end_ts = int(item.end_time.timestamp)
            events.append({
                "start": datetime.fromtimestamp(start_ts),
                "end": datetime.fromtimestamp(end_ts),
                "summary": item.summary
            })
            
    return events

def create_calendar_event(summary, start_dt, end_dt, description=""):
    """
    Larkカレンダーに予約を登録する
    """
    event_info = CalendarEvent.builder() \
        .summary(summary) \
        .start_time(TimeInfo.builder().timestamp(str(int(start_dt.timestamp()))).build()) \
        .end_time(TimeInfo.builder().timestamp(str(int(end_dt.timestamp()))).build()) \
        .description(description) \
        .build()

    req = CreateCalendarEventRequest.builder() \
        .calendar_id(CALENDAR_ID) \
        .request_body(event_info) \
        .build()

    resp = client.calendar.v4.calendar_event.create(req)
    
    if resp.success():
        print(f"✅ Created Lark Calendar event: {summary} at {start_dt}")
        return True
    else:
        print(f"❌ Failed to create event: {resp.code}, {resp.msg}, {resp.error}")
        return False
    return True
