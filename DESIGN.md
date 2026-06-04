# System Architecture & Design

## Overview
The Store Intelligence API is designed as a decoupled, event-driven architecture bridging raw computer vision edge-processing with a central analytical backend. 

1.  **Detection Layer (Edge):** `detect.py` uses YOLOv8 to process video frames, identify humans, and assign tracking IDs. It correlates spatial bounding boxes with predefined zone geometries to deduce behavioral states (e.g., ZONE_ENTER).
2.  **Event Stream (Emitter):** State changes trigger `emit.py` to construct strictly validated JSON objects. This decouples the CV models from the backend logic.
3.  **Intelligence API (Backend):** A FastAPI service built for high-throughput ingestion. It maintains an in-memory state of visitor sessions to calculate real-time funnels, metrics, and detect anomalies.

## AI-Assisted Decisions
As required, AI tools were used extensively during this build. Here is how they shaped the design:

* **Agreed with AI - Funnel Deduplication:** I initially considered tracking state across multiple database tables for the funnel. The AI suggested using Python `Set` comprehensions on the raw event stream based on `visitor_id` to intrinsically handle Re-Entry deduplication without complex DB queries. I agreed and implemented this in `funnel.py`.
* **Overrode AI - Storage Engine:** The AI initially recommended using PostgreSQL for robust event storage. However, given the requirement for a frictionless `docker compose up` experience and the "real-time" nature of the queries, I overrode this and opted for a highly optimized In-Memory Python Dictionary (`STORE_EVENTS_INDEX`). This drastically reduced deployment complexity and latency, satisfying the core business need over theoretical persistence.
* **Prompting Strategy for CV:** I used an LLM to generate the `point_in_rect` zone intersection logic, explicitly prompting it to handle coordinates from `store_layout.json` to ensure modularity if the store layout changes.