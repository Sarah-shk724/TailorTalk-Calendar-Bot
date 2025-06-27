from datetime import timezone
from langgraph.graph import StateGraph
from typing import TypedDict
from calendar_api import get_calendar_events, book_calendar_event
from datetime import datetime, timedelta
import streamlit as st
import re
import dateparser
from dateparser.search import search_dates

class ChatState(TypedDict):
    user_input: str
    next: str
    response: str

def route(state: ChatState) -> dict:
    user_input = state["user_input"].lower().strip()

    # Debug log
    st.write("🔍 Routing input:", user_input)

    if any(kw in user_input for kw in ["hi", "hello", "hey"]):
        return {"next": "greet"}

    if "free" in user_input or "available" in user_input:
        return {"next": "check"}

    elif any(kw in user_input for kw in ["book", "schedule", "meeting", "appointment"]):
        return {"next": "book"}

    elif any(kw in user_input for kw in ["list", "upcoming", "events", "show calendar"]):
        return {"next": "events"}

    elif any(kw in user_input for kw in ["help", "what can you do", "how", "guide"]):
        return {"next": "help"}

    else:
        return {"next": "fallback"}

def greet(state: ChatState) -> ChatState:
    state["response"] = "👋 Hello! I'm TailorTalk — your smart event assistant built by Sarah Shaikh. I can help you schedule, review, and organize meetings. Just say something like 'Am I free tomorrow?' or 'Book a meeting Friday at 2 PM'."
    return state

def help_user(state: ChatState) -> ChatState:
    state["response"] = (
        """🛠️ I can help you with all event planning tasks. Try these:
- 'Am I free tomorrow?'
- 'Book a meeting on Friday at 3 PM called Client Sync'
- 'List my upcoming meetings'
- 'Cancel a meeting on Thursday'
- 'Reschedule my 2 PM meeting to 4 PM'"""
    )
    return state

def check_free(state: ChatState) -> ChatState:
    user_input = state["user_input"]
    results = search_dates(user_input)

    if not results:
        if "tomorrow" in user_input:
            parsed_day = datetime.now() + timedelta(days=1)
        elif "today" in user_input:
            parsed_day = datetime.now()
        else:
            state["response"] = "⚠️ Sorry, I couldn't understand which day you're asking about. Try 'Am I free tomorrow?' or 'next Monday'."
            return state
    else:
        parsed_day = results[0][1]

    st.write("🕒 Parsed date:", parsed_day)

    day_start = parsed_day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    events = get_calendar_events()
    day_events = []

    for event in events:
        start_str = event['start'].get('dateTime')
        end_str = event['end'].get('dateTime')
        if start_str and end_str:
            start = dateparser.parse(start_str)
            end = dateparser.parse(end_str)
            if start and day_start <= start <= day_end:
                day_events.append((start, end))

    day_events.sort(key=lambda x: x[0])

    free_slots = []
    current_time = day_start
    for start, end in day_events:
        if (start - current_time).total_seconds() >= 1800:
            free_slots.append((current_time, start))
        current_time = max(current_time, end)

    if (day_end - current_time).total_seconds() >= 1800:
        free_slots.append((current_time, day_end))

    st.write("🟢 Found slots:", free_slots)

    if not free_slots:
        state["response"] = "😔 No free 30-minute slots found that day."
    else:
        st.write(f"✅ You're free on {parsed_day.strftime('%A, %B %d')} at:")
        for slot in free_slots:
            start_dt = slot[0]
            end_dt = slot[1]
            label = f"{start_dt.strftime('%I:%M %p')} to {end_dt.strftime('%I:%M %p')}"

            if st.button(f"📅 Book {label}"):
                event = book_calendar_event("Meeting via TailorTalk", start_dt.isoformat(), end_dt.isoformat())
                st.success(f"📆 Booked your meeting at {label}! 🔗 [View event]({event.get('htmlLink')})")
                state["response"] = f"📆 Booked your meeting at {label}! ✅"
                break

        if "response" not in state:
            state["response"] = "✅ Select a time above to book your meeting."

    return state

def book(state: ChatState) -> ChatState:
    user_input = state["user_input"]
    match = re.search(r"called (.+)", user_input.lower())
    event_title = match.group(1).title() if match else "Meeting via TailorTalk"

    results = search_dates(user_input)
    if not results:
        state["response"] = "⚠️ Sorry, I couldn't understand when to book. Try saying 'Book a meeting tomorrow at 3 PM'."
        return state

    parsed_dt = results[0][1].replace(tzinfo=timezone.utc)
    end_time = parsed_dt + timedelta(minutes=30)

    event = book_calendar_event(event_title, parsed_dt.isoformat(), end_time.isoformat())
    state["response"] = (
        f"📆 Booked your meeting '{event_title}' at {parsed_dt.strftime('%A, %B %d at %I:%M %p')}. "
        f"🔗 [View event]({event.get('htmlLink')})"
    )
    return state

def list_events(state: ChatState) -> ChatState:
    events = get_calendar_events()
    if not events:
        state["response"] = "📭 You have no upcoming events."
    else:
        reply = "📅 Your next events:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            reply += f"• {summary} at {start}\n"
        state["response"] = reply
    return state

def fallback(state: ChatState) -> ChatState:
    state["response"] = (
        "🤖 I'm not sure what you meant. Try something like:\n"
        "- 'Am I free tomorrow?'\n"
        "- 'Book a meeting on Friday at 3 PM called Review'\n"
        "- 'List my upcoming events'\n"
        "- 'Reschedule Friday's 2 PM meeting'"
    )
    return state

graph = StateGraph(ChatState)

graph.add_node("router", route)
graph.add_node("greet", greet)
graph.add_node("help", help_user)
graph.add_node("check", check_free)
graph.add_node("book", book)
graph.add_node("events", list_events)
graph.add_node("fallback", fallback)

graph.set_entry_point("router")

graph.add_conditional_edges(
    "router",
    lambda state: state["next"],
    {
        "greet": "greet",
        "help": "help",
        "check": "check",
        "book": "book",
        "events": "events",
        "fallback": "fallback"
    }
)

app = graph.compile()