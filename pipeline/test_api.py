import json
import requests
import os
from datetime import datetime, timezone

# Pointing to the exact file you just found
file_path = "events_output.jsonl"

if not os.path.exists(file_path):
    print(f"❌ ERROR: {file_path} not found!")
    exit()

events = []
now = datetime.now(timezone.utc).isoformat()

with open(file_path, 'r') as f:
    for line in f:
        try:
            event = json.loads(line.strip())
            # Force timestamp to now so it is "live"
            event['timestamp'] = now
            events.append(event)
        except json.JSONDecodeError:
            continue

print(f"✅ Loaded {len(events)} events from {file_path}.")

try:
    response = requests.post("http://localhost:8000/events/ingest", json=events)
    print(f"Status Code: {response.status_code}")
    if response.status_code in [200, 207]:
        print("✅ SUCCESS: Data sent to API!")
    else:
        print(f"Error: {response.json()}")
except Exception as e:
    print(f"❌ ERROR: {e}")