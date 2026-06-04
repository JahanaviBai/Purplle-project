# PROMPT: Generate FastAPI tests using TestClient for a metrics endpoint that calculates unique visitors and conversion rates. Include a test for the empty store edge case.
# CHANGES MADE: I modified the AI's generic mock data to strictly adhere to the Pydantic StoreEvent schema and properly route to our in-memory ingestion index.

from fastapi.testclient import TestClient
from app.main import app
from app.ingestion import EVENT_DB, STORE_EVENTS_INDEX

client = TestClient(app)

def test_empty_store_metrics():
    """Edge Case: Ensure an empty store returns 0s and doesn't crash."""
    # Ensure the store is completely empty
    STORE_EVENTS_INDEX["STORE_TEST_EMPTY"] = []
    
    response = client.get("/stores/STORE_TEST_EMPTY/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["unique_visitors"] == 0
    assert data["conversion_rate"] == 0.0
    assert data["current_queue_depth"] == 0

def test_health_endpoint():
    """Verify the health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "service_status" in response.json()