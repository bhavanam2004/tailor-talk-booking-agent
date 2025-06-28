# calendar/test_calendar.py

from calendar_service import get_available_slots, book_slot
import datetime

# List upcoming calendar events
print("🔔 Upcoming Events:")
events = get_available_slots()

if not events:
    print("No upcoming events found.")
else:
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"- {start}: {event.get('summary', 'No Title')}")

# Book a test event for tomorrow at 10:00 AM
print("\n📅 Booking a new test meeting...")

tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
end_time = start_time + datetime.timedelta(minutes=30)

event = book_slot("TailorTalk Test Meeting", start_time.isoformat(), end_time.isoformat())

print(f"\n✅ Event created successfully: {event.get('htmlLink')}")
