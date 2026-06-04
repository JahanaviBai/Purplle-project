import cv2
from datetime import datetime, timezone, timedelta
from ultralytics import YOLO
from emit import create_event, append_to_jsonl

# Configuration
STORE_ID = "ST1008" 
CAMERA_ID = "CAM_1_ZONE"
VIDEO_PATH = "../data/CAM 1 - zone.mp4" 
FPS = 15.0 

# Your Real Mapped Zones!
THE_FACE_SHOP_ZONE = (363, 4, 406, 756)
MINIMALIST_ZONE = (1352, 5, 1389, 621) 

# State management for tracking dwell times and active zones
active_visitors = {}

def point_in_rect(point, rect):
    """Check if a point (x, y) is inside a rectangle (x1, y1, x2, y2)."""
    x, y = point
    x1, y1, x2, y2 = rect
    return x1 < x < x2 and y1 < y < y2

def process_video():
    print(f"Loading YOLOv8 model...")
    # Using the nano model for speed. 
    model = YOLO('yolov8n.pt') 
    
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"Warning: Could not open video file {VIDEO_PATH}. Ensure the file exists.")
        return

    frame_count = 0
    start_time = datetime.now(timezone.utc)

    print("Starting real CCTV video processing pipeline...")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        frame_count += 1
        # Calculate simulated timestamp based on frame offset
        current_time = start_time + timedelta(seconds=frame_count / FPS)
        timestamp_iso = current_time.isoformat()

        # Run YOLO tracking. classes=[0] ensures we only track humans.
        results = model.track(frame, persist=True, classes=[0], verbose=False)
        
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()

            for box, track_id, conf in zip(boxes, track_ids, confidences):
                visitor_id = f"VIS_{int(track_id):06d}"
                
                # Calculate center point of the bounding box (customer's center)
                center_x = (box[0] + box[2]) / 2
                center_y = (box[1] + box[3]) / 2
                point = (center_x, center_y)

                # 1. Handle New Entries
                if visitor_id not in active_visitors:
                    active_visitors[visitor_id] = {
                        "first_seen": current_time,
                        "last_seen": current_time,
                        "current_zone": None,
                        "zone_entry_time": None
                    }
                    
                    # Emit ENTRY event
                    entry_event = create_event(
                        store_id=STORE_ID, camera_id=CAMERA_ID, visitor_id=visitor_id,
                        event_type="ENTRY", timestamp_iso=timestamp_iso, confidence=conf
                    )
                    append_to_jsonl(entry_event)

                # Update last seen
                active_visitors[visitor_id]["last_seen"] = current_time

                # 2. Zone Logic (Using your real coordinates!)
                current_state = active_visitors[visitor_id]
                
                # Check The Face Shop
                if point_in_rect(point, THE_FACE_SHOP_ZONE) and current_state["current_zone"] != "THE_FACE_SHOP":
                    current_state["current_zone"] = "THE_FACE_SHOP"
                    current_state["zone_entry_time"] = current_time
                    
                    zone_event = create_event(
                        store_id=STORE_ID, camera_id=CAMERA_ID, visitor_id=visitor_id,
                        event_type="ZONE_ENTER", timestamp_iso=timestamp_iso,
                        zone_id="THE_FACE_SHOP", confidence=conf, sku_zone="SKINCARE"
                    )
                    append_to_jsonl(zone_event)

                # Check Minimalist
                elif point_in_rect(point, MINIMALIST_ZONE) and current_state["current_zone"] != "MINIMALIST":
                    current_state["current_zone"] = "MINIMALIST"
                    current_state["zone_entry_time"] = current_time
                    
                    zone_event = create_event(
                        store_id=STORE_ID, camera_id=CAMERA_ID, visitor_id=visitor_id,
                        event_type="ZONE_ENTER", timestamp_iso=timestamp_iso,
                        zone_id="MINIMALIST", confidence=conf, sku_zone="SKINCARE"
                    )
                    append_to_jsonl(zone_event)

    cap.release()
    print("Finished processing video.")

if __name__ == "__main__":
    process_video()