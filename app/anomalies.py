from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime, timezone
from .ingestion import STORE_EVENTS_INDEX
from .models import EventType

router = APIRouter()

@router.get("/stores/{store_id}/anomalies")
async def get_anomalies(store_id: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Detects active operational anomalies:
    - QUEUE_SPIKE (CRITICAL/WARN)
    - DEAD_ZONE (WARN)
    - CONVERSION_DROP (CRITICAL)
    """
    events = STORE_EVENTS_INDEX.get(store_id, [])
    anomalies = []

    if not events:
        return {"anomalies": anomalies}

    now_utc = datetime.now(timezone.utc)
    customer_events = [e for e in events if not e.is_staff]

    # 1. QUEUE_SPIKE Detection
    queue_events = [e for e in customer_events if e.event_type == EventType.BILLING_QUEUE_JOIN]
    if queue_events:
        latest_queue_depth = queue_events[-1].metadata.queue_depth or 0
        if latest_queue_depth > 10:
            anomalies.append({
                "type": "QUEUE_SPIKE",
                "severity": "CRITICAL",
                "description": f"Queue depth is severely high ({latest_queue_depth} customers).",
                "suggested_action": "Open an additional billing counter immediately."
            })
        elif latest_queue_depth > 5:
            anomalies.append({
                "type": "QUEUE_SPIKE",
                "severity": "WARN",
                "description": f"Queue depth is building up ({latest_queue_depth} customers).",
                "suggested_action": "Prepare to open another counter."
            })

    # 2. DEAD_ZONE Detection (No visits in a zone for 30+ mins)
    zone_last_seen = {}
    for e in customer_events:
        if e.zone_id and e.event_type in (EventType.ZONE_ENTER, EventType.ZONE_DWELL):
            zone_last_seen[e.zone_id] = e.timestamp

    for zone, last_seen in zone_last_seen.items():
        if (now_utc - last_seen).total_seconds() > 1800:  # 1800 seconds = 30 mins
            anomalies.append({
                "type": "DEAD_ZONE",
                "severity": "WARN",
                "description": f"No customer activity in {zone} for over 30 minutes.",
                "suggested_action": "Deploy staff to check zone layout, signage, or lighting."
            })

    # 3. CONVERSION_DROP Detection (Proxy against a mock 7-day average)
    entered = {e.visitor_id for e in customer_events if e.event_type == EventType.ENTRY}
    abandons = {e.visitor_id for e in customer_events if e.event_type == EventType.BILLING_QUEUE_ABANDON}
    queue_joins = {e.visitor_id for e in customer_events if e.event_type == EventType.BILLING_QUEUE_JOIN}
    
    purchases = queue_joins - abandons
    
    # Only calculate if we have meaningful traffic (e.g., > 10 entries)
    if len(entered) > 10: 
        current_cr = (len(purchases) / len(entered)) * 100
        historical_cr = 15.0  # Mock 7-day average for the in-memory state

        if current_cr < (historical_cr * 0.5):  # Dropped by more than 50%
            anomalies.append({
                "type": "CONVERSION_DROP",
                "severity": "CRITICAL",
                "description": f"Conversion rate ({current_cr:.1f}%) dropped significantly below 7-day avg ({historical_cr}%).",
                "suggested_action": "Check POS system uptime and stock availability on high-intent shelves."
            })

    return {"anomalies": anomalies}