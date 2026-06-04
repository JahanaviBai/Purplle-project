import uuid
import json
from datetime import datetime, timezone

def create_event(store_id, camera_id, visitor_id, event_type, timestamp_iso, zone_id=None, confidence=0.95, sku_zone=None, dwell_ms=0, is_staff=False, queue_depth=0, session_seq=1):
    """
    Creates a structured event matching the exact HackerEarth schema requirements.
    """
    event = {
        "event_id": str(uuid.uuid4()),
        "store_id": store_id,
        "camera_id": camera_id,
        "visitor_id": visitor_id,
        "event_type": event_type,
        "timestamp": timestamp_iso,
        "zone_id": zone_id,
        "dwell_ms": dwell_ms,           # Required by rubric: 0 for instantaneous events
        "is_staff": is_staff,           # Required by rubric: boolean flag
        "confidence": float(confidence),
        "metadata": {
            # Only populate queue_depth if it is a billing queue event
            "queue_depth": queue_depth if event_type == "BILLING_QUEUE_JOIN" else None,
            "sku_zone": sku_zone,
            "session_seq": session_seq  # Required by rubric: tracking ordinal position
        }
    }
    return event

def append_to_jsonl(event, filename="events.jsonl"):
    with open(filename, 'a') as f:
        f.write(json.dumps(event) + '\n')