from fastapi import APIRouter
from typing import Dict, Any, Set
from .ingestion import STORE_EVENTS_INDEX
from .models import EventType

router = APIRouter()

@router.get("/stores/{store_id}/funnel")
async def get_conversion_funnel(store_id: str) -> Dict[str, Any]:
    """
    Returns the conversion funnel metrics.
    Unit is the session (visitor_id), not raw events. 
    Naturally handles re-entries via Set deduplication.
    """
    events = STORE_EVENTS_INDEX.get(store_id, [])

    if not events:
        return _empty_funnel()

    # Exclude staff from metrics [cite: 326]
    customer_events = [e for e in events if not e.is_staff]

    # Stage 1: Store Entry
    # Set comprehension ensures visitor_id is only stored once, even if they REENTRY[cite: 328, 329].
    entered_visitors: Set[str] = {
        e.visitor_id for e in customer_events if e.event_type == EventType.ENTRY
    }

    # Stage 2: Zone Visit (Must have entered store first)
    zone_visitors: Set[str] = {
        e.visitor_id for e in customer_events 
        if e.event_type in (EventType.ZONE_ENTER, EventType.ZONE_DWELL)
        and e.visitor_id in entered_visitors
    }

    # Stage 3: Billing Queue
    queue_visitors: Set[str] = {
        e.visitor_id for e in customer_events 
        if e.event_type == EventType.BILLING_QUEUE_JOIN
        and e.visitor_id in entered_visitors
    }

    # Stage 4: Purchase
    # Note: For real-time stream, we proxy purchase as "Joined queue and did NOT abandon".
    # In a batch job, this is where we correlate with the POS CSV data[cite: 300].
    abandoned_visitors: Set[str] = {
        e.visitor_id for e in customer_events 
        if e.event_type == EventType.BILLING_QUEUE_ABANDON
    }
    purchased_visitors = queue_visitors - abandoned_visitors

    # Counts
    c_entry = len(entered_visitors)
    c_zone = len(zone_visitors)
    c_queue = len(queue_visitors)
    c_purchase = len(purchased_visitors)

    # Drop-off Helper Function
    def calc_dropoff(current: int, previous: int) -> float:
        if previous == 0: 
            return 0.0
        return round(((previous - current) / previous) * 100, 2)

    return {
        "funnel": {
            "1_entry": {"count": c_entry, "dropoff_from_previous": 0.0},
            "2_zone_visit": {"count": c_zone, "dropoff_from_previous": calc_dropoff(c_zone, c_entry)},
            "3_billing_queue": {"count": c_queue, "dropoff_from_previous": calc_dropoff(c_queue, c_zone)},
            "4_purchase": {"count": c_purchase, "dropoff_from_previous": calc_dropoff(c_purchase, c_queue)}
        },
        "overall_conversion_rate": round((c_purchase / c_entry * 100), 2) if c_entry > 0 else 0.0
    }

def _empty_funnel() -> Dict[str, Any]:
    return {
        "funnel": {
            "1_entry": {"count": 0, "dropoff_from_previous": 0.0},
            "2_zone_visit": {"count": 0, "dropoff_from_previous": 0.0},
            "3_billing_queue": {"count": 0, "dropoff_from_previous": 0.0},
            "4_purchase": {"count": 0, "dropoff_from_previous": 0.0}
        },
        "overall_conversion_rate": 0.0
    }