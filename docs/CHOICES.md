# Engineering Trade-Offs & Choices

## 1. Detection Model Selection
* **Options Considered:** YOLOv8, MediaPipe, ByteTrack + OSNet (for deep Re-ID).
* **AI Suggestion:** The AI suggested utilizing ByteTrack combined with a heavy Re-ID model (OSNet) to ensure perfect tracking across overlapping cameras.
* **My Choice:** I chose **YOLOv8 Nano (yolov8n.pt)** with native tracking.
* **Reasoning:** While deep Re-ID offers higher accuracy for cross-camera deduplication, YOLOv8n operates fast enough to process the 15fps constraint seamlessly on CPU-bound edge devices. The business North Star metric (Conversion Rate) relies on velocity and session tracking. By tuning the tracker persistence, I achieved an acceptable accuracy threshold for the entry/exit counts without the heavy overhead of a VLM or two-stage Re-ID pipeline.

## 2. Event Schema Design Rationale
* **Options Considered:** Raw coordinate stream (heavy) vs. Semantic Behavioral Events (light).
* **AI Suggestion:** The AI recommended passing raw bounding box coordinates to the API and letting the backend calculate zone intersections.
* **My Choice:** I enforced Semantic Behavioral Events (e.g., `ZONE_DWELL`, `BILLING_QUEUE_JOIN`) emitted directly from the pipeline.
* **Reasoning:** This is a separation of concerns. The API should not care about pixels or camera angles; it should only care about business events. By calculating spatial logic at the edge (in `detect.py`) and standardizing it into a strict Pydantic schema (`app/models.py`), the API becomes completely agnostic to the camera hardware. If Apex Retail switches camera vendors, the backend API code requires zero changes.

## 3. API Architecture (State Management)
* **Options Considered:** SQLite, Redis, In-Memory Python Dicts.
* **AI Suggestion:** AI suggested Redis for fast in-memory metric aggregations.
* **My Choice:** Standard In-Memory Python Dictionaries.
* **Reasoning:** Introducing Redis would require a secondary Docker container, complicating the single-command startup requirement. Since this is an analytics pipeline calculating *today's* real-time metrics, an in-memory Python dictionary structured as `Dict[store_id, List[StoreEvent]]` provides O(1) lookup times for idempotency and fast O(N) list comprehensions for metric generation, perfectly balancing performance with architectural simplicity.