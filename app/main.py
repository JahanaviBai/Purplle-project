from fastapi import FastAPI, Request
from typing import List, Dict, Any
from app.ingestion import events_db  # Correctly importing the global database

app = FastAPI(title="Store Intelligence API")

# Middleware from your traceback
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    return response

# The ingestion endpoint your test_api.py is trying to hit
@app.post("/events/ingest")
async def ingest_events(events: List[Dict[str, Any]]):
    """Receives a list of events from the JSONL script and stores them."""
    for event in events:
        events_db.append(event)
    return {"status": "success", "message": f"Ingested {len(events)} events."}

# The metrics endpoint you are checking in the browser
@app.get("/stores/{store_id}/metrics")
async def get_metrics(store_id: str):
    """Calculates and returns metrics for a specific store."""
    # FIXED: Now using 'events_db' instead of 'stored_events'
    # FIXED: Wrapped in str() to prevent any type mismatch errors
    store_events = [e for e in events_db if str(e.get("store_id")) == str(store_id)]
    
    return {
        "store_id": store_id,
        "event_count": len(store_events),
        "events": store_events
    }