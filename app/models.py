from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ZONE_ENTER = "ZONE_ENTER"
    ZONE_EXIT = "ZONE_EXIT"
    ZONE_DWELL = "ZONE_DWELL"
    BILLING_QUEUE_JOIN = "BILLING_QUEUE_JOIN"
    BILLING_QUEUE_ABANDON = "BILLING_QUEUE_ABANDON"
    REENTRY = "REENTRY"

class EventMetadata(BaseModel):
    queue_depth: Optional[int] = Field(default=None, description="Populated for BILLING_QUEUE_JOIN")
    sku_zone: Optional[str] = Field(default=None, description="Zone label from store_layout.json")
    session_seq: int = Field(..., description="Ordinal position of this event in visitor session")

class StoreEvent(BaseModel):
    event_id: UUID4 = Field(..., description="Globally unique UUID-v4")
    store_id: str = Field(..., description="Target store identifier")
    camera_id: str = Field(..., description="Source camera asset identifier")
    visitor_id: str = Field(..., description="Unique Re-ID token per visit session")
    event_type: EventType = Field(..., description="Categorized behavioral event type")
    timestamp: datetime = Field(..., description="ISO-8601 UTC timestamp derived from frame offset")
    zone_id: Optional[str] = Field(default=None, description="Null for global ENTRY/EXIT events")
    dwell_ms: int = Field(default=0, description="Duration in milliseconds; 0 for instantaneous events")
    is_staff: bool = Field(default=False, description="Flag for retail employee filtering")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Raw model object confidence level")
    metadata: EventMetadata