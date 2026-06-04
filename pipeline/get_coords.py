import cv2
import os

print("\n--- STARTING COORDINATE MAPPER ---")

# The path to your video
VIDEO_PATH = "../data/CAM 1 - zone.mp4" 

# Debugging: Tell us exactly where it's looking
absolute_path = os.path.abspath(VIDEO_PATH)
print(f"🔍 Looking for video at: {absolute_path}")

# Check if the file actually exists before trying to open it
if not os.path.exists(VIDEO_PATH):
    print("\n❌ ERROR: Cannot find the video file!")
    print("Please make sure your data folder has a file named exactly 'CAM 1 - zone.mp4'.")
    exit()

print("✅ Video file found! Loading the first frame...")
cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()

if not ret:
    print("\n❌ ERROR: Found the file, but couldn't read the video. It might be corrupted or unsupported.")
    exit()

points = []
def click_event(event, x, y, flags, param):
    global points
    # Trigger when the Left Mouse Button is clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"🖱️ Click detected at pixel -> X: {x}, Y: {y}")
        points.append((x, y))
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        cv2.imshow('Video Zone Mapper', frame)
        
        # When two clicks are registered, print the zone
        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]
            print(f"\n🎯 BOOM! Your Zone Coordinates are: ({x1}, {y1}, {x2}, {y2})")
            print("-> Copy these numbers. Click two more times for another zone, or press 'q' to quit.\n")
            points.clear()

print("🖼️ Opening the image window... (Check your Windows Taskbar if it popped up behind your terminal!)")

# Create the window and attach the mouse clicker
cv2.imshow('Video Zone Mapper', frame)
cv2.setMouseCallback('Video Zone Mapper', click_event)

print("⏳ Waiting for you to click the image... (Press 'q' to quit)")
while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        
cv2.destroyAllWindows()
cap.release()
print("--- CLOSED MAPPER ---\n")