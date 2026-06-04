from fastapi import APIRouter
from typing import Dict, Any
from .ingestion import STORE_EVENTS_INDEX
from .models import EventType

router = APIRouter()

@router.get("/stores/{store_id}/metrics")
async def get_store_metrics(store_id: str) -> Dict[str, Any]:
    """
    Returns real-time store analytics.
    Handles zero-traffic stores gracefully and explicitly excludes staff events.
    """
    # 1. Fetch events for this specific store
    events = STORE_EVENTS_INDEX.get(store_id, [])
    
    # EDGE CASE: Empty store periods (Handle zero-traffic correctly - not crash or return null)
    if not events:
        return {
            "unique_visitors": 0,
            "conversion_rate": 0.0,
            "avg_dwell_per_zone_seconds": {},
            "current_queue_depth": 0,
            "abandonment_rate": 0.0
        }

    # 2. FILTERING: Exclude staff from all customer metrics
    customer_events = [e for e in events if not e.is_staff]

    # 3. UNIQUE VISITORS: Deduplicate sessions using the visitor_id on ENTRY
    # Note: REENTRY events do not trigger a new visitor count, preventing double-counting.
    unique_visitors = len(set(
        e.visitor_id for e in customer_events if e.event_type == EventType.ENTRY
    ))

    # 4. DWELL TIMES: Aggregate and average by zone
    zone_dwells = {}
    zone_counts = {}
    for e in customer_events:
        if e.event_type == EventType.ZONE_DWELL and e.zone_id:
            zone_dwells[e.zone_id] = zone_dwells.get(e.zone_id, 0) + e.dwell_ms
            zone_counts[e.zone_id] = zone_counts.get(e.zone_id, 0) + 1

    avg_dwell_per_zone = {
        zone: round((total_dwell / zone_counts[zone]) / 1000, 2) # Convert ms to seconds
        for zone, total_dwell in zone_dwells.items()
    }

    # 5. QUEUE ANALYTICS: Abandonment rate and current depth
    queue_joins = [e for e in customer_events if e.event_type == EventType.BILLING_QUEUE_JOIN]
    abandons = [e for e in customer_events if e.event_type == EventType.BILLING_QUEUE_ABANDON]
    
    # Get the most recent queue depth if available
    current_queue_depth = 0
    if queue_joins and queue_joins[-1].metadata.queue_depth is not None:
        current_queue_depth = queue_joins[-1].metadata.queue_depth
        
    abandonment_rate = (len(abandons) / len(queue_joins) * 100) if queue_joins else 0.0

    # 6. CONVERSION RATE: (Purchases / Unique Visitors)
    # *Note: In a full production system, we correlate POS CSV data here. 
    # For this real-time endpoint, we use a behavioral proxy: visitors who joined the queue and didn't abandon.
    converted_visitors = len(queue_joins) - len(abandons)
    conversion_rate = (converted_visitors / unique_visitors * 100) if unique_visitors > 0 else 0.0

    return {
        "unique_visitors": unique_visitors,
        "conversion_rate": round(conversion_rate, 2),
        "avg_dwell_per_zone_seconds": avg_dwell_per_zone,
        "current_queue_depth": current_queue_depth,
        "abandonment_rate": round(abandonment_rate, 2)
    }