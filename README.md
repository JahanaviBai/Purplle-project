# Apex Retail - Store Intelligence API

An end-to-end computer vision and analytics pipeline that processes raw CCTV footage, tracks customer movement, and exposes real-time store metrics via a Fast-API backend.

## 🚀 Setup & Execution (5 Commands)

To get the entire system running from scratch, execute the following:

1. `git clone <repository-url>`
2. `cd store-intelligence`
3. `docker compose up --build -d`
4. `cd pipeline && pip install ultralytics opencv-python`
5. `bash run.sh` 

## 📹 Running the Detection Pipeline
The computer vision pipeline (`pipeline/detect.py`) uses YOLOv8 to process video clips. 
* Place your `sample_clip.mp4` in the `pipeline/` directory.
* Run the pipeline using `bash run.sh` (or `python detect.py` on Windows).
* The script will process the frames, handle visitor Re-ID tracking, and output structured schema events to `pipeline/events_output.jsonl`.

## ⚡ Feeding Output to the API
Once the `events_output.jsonl` file is generated, you can ingest the events into the running API. 

Because the API expects a JSON array (up to 500 events per batch) for idempotency and error handling, you can send the data using this Python snippet:

```python
import json
import requests

# Read the JSONL file and convert to a list of dictionaries
events = []
with open('pipeline/events_output.jsonl', 'r') as f:
    for line in f:
        events.append(json.loads(line.strip()))

# Send batch to the API
response = requests.post(
    "http://localhost:8000/events/ingest", 
    json=events[:500] # Send first 500
)
print(response.json())