from typing import List, Dict, Any
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from .models import StoreEvent
from uuid import UUID
events_db = []

router = APIRouter()

# In-Memory Storage Engine
# EVENT_DB gives us O(1) idempotency checks.
EVENT_DB: Dict[UUID, StoreEvent] = {}

# STORE_EVENTS_INDEX groups events by store_id for fast metric calculations.
STORE_EVENTS_INDEX: Dict[str, List[StoreEvent]] = {}

@router.post("/events/ingest")
async def ingest_events(request: Request):
    """
    Ingests a batch of structured events from the detection layer.
    Idempotent by event_id. Allows partial success.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid JSON payload format."}
        )

    if not isinstance(payload, list):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Payload must be a JSON array of events."}
        )

    if len(payload) > 500:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Batch size exceeds maximum of 500 events."}
        )

    successful = 0
    failed = 0
    errors = []

    for index, item in enumerate(payload):
        try:
            # Validate against our Pydantic schema
            event = StoreEvent(**item)
            
            # Idempotency Check: Safely skip if we already processed this event_id
            if event.event_id not in EVENT_DB:
                EVENT_DB[event.event_id] = event
                
                if event.store_id not in STORE_EVENTS_INDEX:
                    STORE_EVENTS_INDEX[event.store_id] = []
                STORE_EVENTS_INDEX[event.store_id].append(event)
                
            successful += 1
            
        except ValidationError as e:
            failed += 1
            # Capture structured errors for partial failures
            errors.append({"index": index, "errors": e.errors()})

    # Return structured response detailing successes and failures
    return JSONResponse(
        status_code=status.HTTP_207_MULTI_STATUS if failed > 0 else status.HTTP_200_OK,
        content={
            "message": "Batch processed",
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
    )