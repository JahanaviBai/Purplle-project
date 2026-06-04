from fastapi import APIRouter
from datetime import datetime, timezone
from typing import Dict, Any
from .ingestion import STORE_EVENTS_INDEX

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Returns service status and checks for stale camera feeds.
    Flags 'STALE_FEED' if the last event for a store is older than 10 minutes.
    """
    status_data = {
        "service_status": "OK",
        "store_feeds": {}
    }
    
    # Use UTC to match the ISO-8601 timestamps from the events
    now_utc = datetime.now(timezone.utc)
    
    for store_id, events in STORE_EVENTS_INDEX.items():
        if not events:
            continue
            
        # Get the most recent event for this store
        latest_event = events[-1]
        last_timestamp = latest_event.timestamp
        
        # Calculate the time difference in minutes
        lag_minutes = (now_utc - last_timestamp).total_seconds() / 60.0
        
        # Determine if the feed is lagging beyond the 10-minute threshold
        feed_status = "STALE_FEED" if lag_minutes > 10 else "HEALTHY"
        
        status_data["store_feeds"][store_id] = {
            "last_event_timestamp": last_timestamp.isoformat(),
            "lag_minutes": round(lag_minutes, 2),
            "status": feed_status
        }
        
    return status_data