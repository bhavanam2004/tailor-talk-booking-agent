import sys
import os
import pytz
import re
from datetime import datetime, timedelta
import dateparser
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

# 📦 Import calendar_service
from calendar_api.calendar_service import book_slot, is_time_slot_available

# Set timezone
tz = pytz.timezone("Asia/Kolkata")

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    parsed_time: datetime
    intent: str
    response: str

# 🧠 Fuzzy time normalization
def normalize_fuzzy_time(message: str) -> str:
    fuzzy_map = {
        "morning": "10 AM",
        "afternoon": "2 PM",
        "evening": "6 PM",
        "night": "8 PM",
        "noon": "12 PM",
        "midnight": "12 AM",
    }

    if "tonight" in message:
        message = message.replace("tonight", "today at 6 PM")

    for word, replacement in fuzzy_map.items():
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, message) and not re.search(rf'{word}.*\d+', message):
            message = re.sub(pattern, f'at {replacement}', message)

    return message

# Intent and time parsing
def parse_intent_and_time(state: AgentState) -> AgentState:
    message = normalize_fuzzy_time(state["messages"][-1].lower())
    now = datetime.now(tz)

    if "free time" in message or "available" in message:
        state["intent"] = "check_availability"
        parsed = dateparser.parse(message, settings={
            'PREFER_DATES_FROM': 'future',
            'TIMEZONE': 'Asia/Kolkata',
            'TO_TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True
        })
        if not parsed:
            state["response"] = "❌ I couldn't understand the day."
            return state
        state["parsed_time"] = parsed.replace(hour=0, minute=0, second=0, microsecond=0)

    elif "between" in message:
        state["intent"] = "book_range"
        parsed = dateparser.parse(message, settings={
            'PREFER_DATES_FROM': 'future',
            'TIMEZONE': 'Asia/Kolkata',
            'TO_TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True
        })
        if not parsed and "next week" in message:
            parsed = now + timedelta(days=(7 - now.weekday()))
        if not parsed:
            state["response"] = "❌ Couldn't understand time range."
            return state
        state["parsed_time"] = parsed.replace(hour=0, minute=0, second=0, microsecond=0)

    else:
        state["intent"] = "book_direct"
        parsed = dateparser.parse(message, settings={
            'PREFER_DATES_FROM': 'future',
            'TIMEZONE': 'Asia/Kolkata',
            'TO_TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True
        })
        if not parsed:
            state["response"] = "❌ Couldn't understand time."
            return state
        if parsed < now:
            state["response"] = "❌ Time is in the past."
            return state
        minute = 0 if parsed.minute < 30 else 30
        state["parsed_time"] = parsed.replace(minute=minute, second=0, microsecond=0)

    return state

# Availability

def handle_availability(state: AgentState) -> AgentState:
    day = state["parsed_time"]
    suggestions = []
    for hour in range(9, 18):
        start = day.replace(hour=hour, minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=30)
        if is_time_slot_available(start.isoformat(), end.isoformat()):
            suggestions.append(start.strftime("%I:%M %p"))
    state["response"] = (
        f"✅ You're available at: {', '.join(suggestions[:3])}..." if suggestions else "⛔ No free slots found."
    )
    return state

# Book in range

def handle_range_booking(state: AgentState) -> AgentState:
    day = state["parsed_time"]
    for hour in range(15, 17):
        for minute in [0, 30]:
            start = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
            end = start + timedelta(minutes=30)
            if is_time_slot_available(start.isoformat(), end.isoformat()):
                event = book_slot("Meeting from TailorTalk Agent", start.isoformat(), end.isoformat())
                state["response"] = f"✅ Booked: {start.strftime('%I:%M %p')}\n🔗 {event.get('htmlLink')}"
                return state
    state["response"] = "⛔ No free slots between 3–5 PM."
    return state

# Book direct

def handle_direct_booking(state: AgentState) -> AgentState:
    start = state["parsed_time"]
    end = start + timedelta(minutes=30)
    if not is_time_slot_available(start.isoformat(), end.isoformat()):
        state["response"] = "⛔ Already booked. Try another time."
        return state
    event = book_slot("Meeting from TailorTalk Agent", start.isoformat(), end.isoformat())
    state["response"] = f"✅ Meeting booked!\n📅 {start.strftime('%Y-%m-%d %I:%M %p')}\n🔗 {event.get('htmlLink')}"
    return state

# Workflow

def create_workflow():
    wf = StateGraph(AgentState)
    wf.set_entry_point("parse_intent")

    wf.add_node("parse_intent", parse_intent_and_time)
    wf.add_node("check_availability", handle_availability)
    wf.add_node("book_range", handle_range_booking)
    wf.add_node("book_direct", handle_direct_booking)

    wf.add_conditional_edges(
        "parse_intent",
        lambda state: state["intent"] if not state.get("response") else "end",
        {
            "check_availability": "check_availability",
            "book_range": "book_range",
            "book_direct": "book_direct",
            "end": END,
        },
    )

    wf.add_edge("check_availability", END)
    wf.add_edge("book_range", END)
    wf.add_edge("book_direct", END)

    return wf.compile()

def process_message(message: str) -> str:
    graph = create_workflow()
    result = graph.invoke({"messages": [message], "response": ""})
    return result["response"]

if __name__ == "__main__":
    while True:
        user_input = input("💬 You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        print(process_message(user_input))
