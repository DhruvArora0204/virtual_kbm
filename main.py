import cv2
import pyautogui
import numpy as np
import asyncio
import websockets
import json
import base64
import threading
import time

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

pyautogui.FAILSAFE = False

# Screen dimensions
wScr, hScr = pyautogui.size()

# Cam dimensions
wCam, hCam = 640, 480

# Frame reduction for mouse moving area (to reach edges)
frameR = 50
smoothening = 7
plocX, plocY = 0, 0
clocX, clocY = 0, 0

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

# Initialize Mediapipe HandLandmarker
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.HandLandmarker.create_from_options(options)

mode = "mouse" # "mouse" or "keyboard"
last_toggle_time = 0

# Shared state for websocket
ws_state = {
    "mode": mode,
    "cursor_x": 0,
    "cursor_y": 0,
    "click": False,
    "frame": None
}

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4), # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8), # Index
    (5, 9), (9, 10), (10, 11), (11, 12), # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
]

def draw_landmarks(img, landmarks):
    h, w, c = img.shape
    for connection in HAND_CONNECTIONS:
        p1 = landmarks[connection[0]]
        p2 = landmarks[connection[1]]
        x1, y1 = int(p1.x * w), int(p1.y * h)
        x2, y2 = int(p2.x * w), int(p2.y * h)
        cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
    for lm in landmarks:
        x, y = int(lm.x * w), int(lm.y * h)
        cv2.circle(img, (x, y), 4, (0, 0, 255), -1)

def get_fingers_up(landmarks):
    fingers = []
    # Thumb
    if landmarks[4].y > landmarks[3].y:
        fingers.append(1)
    else:
        fingers.append(0)
    # 4 Fingers
    tipIds = [8, 12, 16, 20]
    for id in tipIds:
        if landmarks[id].y < landmarks[id - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

def find_distance(p1, p2, landmarks, w, h):
    x1, y1 = int(landmarks[p1].x * w), int(landmarks[p1].y * h)
    x2, y2 = int(landmarks[p2].x * w), int(landmarks[p2].y * h)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    length = np.hypot(x2 - x1, y2 - y1)
    return length, [x1, y1, x2, y2, cx, cy]

def process_frames():
    global plocX, plocY, clocX, clocY, mode, last_toggle_time
    
    while True:
        success, img = cap.read()
        if not success:
            continue
            
        img = cv2.flip(img, 1) # Flip horizontally for selfie view
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
        results = detector.detect(mp_image)
        
        h, w, _ = img.shape
        
        if results.hand_landmarks:
            for handLms in results.hand_landmarks:
                draw_landmarks(img, handLms)
                
                x1, y1 = int(handLms[8].x * w), int(handLms[8].y * h)
                
                # Draw movement area
                cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)
                
                fingers = get_fingers_up(handLms)
                
                # Mode is now toggled via UI buttons receiving clicks.
                # The frontend sends a websocket message to change `mode`.
                
                ws_state["mode"] = mode
                
                if mode == "mouse":
                    if fingers[1] == 1:
                        x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                        y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))
                        clocX = plocX + (x3 - plocX) / smoothening
                        clocY = plocY + (y3 - plocY) / smoothening
                        try:
                            pyautogui.moveTo(clocX, clocY)
                        except: pass
                        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                        plocX, plocY = clocX, clocY
                        
                    # Pinch to click (Index 8 and Thumb 4)
                    length_click, lineInfo = find_distance(4, 8, handLms, w, h)
                    if length_click < 60: 
                        cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                        if time.time() - last_toggle_time > 0.5:
                            threading.Thread(target=pyautogui.click, daemon=True).start()
                            last_toggle_time = time.time()
                            
                elif mode == "keyboard":
                    if fingers[1] == 1:
                        x_norm = max(0, min(1, (x1 - frameR) / (wCam - 2*frameR)))
                        y_norm = max(0, min(1, (y1 - frameR) / (hCam - 2*frameR)))
                        
                        # Apply smoothening to keyboard mode as well
                        prev_x = ws_state.get("cursor_x", 0)
                        prev_y = ws_state.get("cursor_y", 0)
                        
                        ws_state["cursor_x"] = prev_x + (x_norm - prev_x) / smoothening
                        ws_state["cursor_y"] = prev_y + (y_norm - prev_y) / smoothening
                        
                    length_click, lineInfo = find_distance(4, 8, handLms, w, h)
                    ws_state["click"] = bool(length_click < 60)
        
        cv2.putText(img, f"Mode: {mode.upper()}", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        
        # Compress image for websocket to avoid lag
        img_small = cv2.resize(img, (320, 240))
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
        _, buffer = cv2.imencode('.jpg', img_small, encode_param)
        
        ws_state["frame"] = base64.b64encode(buffer).decode('utf-8')
        
        # We removed time.sleep(0.01) to read frames as fast as possible, preventing camera buffer lag

async def websocket_handler(websocket):
    global mode
    print("Client connected!")
    
    async def receive_messages():
        global mode
        try:
            async for message in websocket:
                data = json.loads(message)
                if "mode" in data:
                    mode = data["mode"]
                    print("Mode changed via UI to:", mode)
        except:
            pass

    asyncio.create_task(receive_messages())

    try:
        while True:
            await websocket.send(json.dumps({
                "mode": ws_state["mode"],
                "cursor_x": ws_state["cursor_x"],
                "cursor_y": ws_state["cursor_y"],
                "click": ws_state["click"],
                "frame": ws_state["frame"]
            }))
            await asyncio.sleep(0.03)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")

async def start_server():
    print("Starting WebSocket server on ws://localhost:8765")
    async with websockets.serve(websocket_handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    cv_thread = threading.Thread(target=process_frames, daemon=True)
    cv_thread.start()
    asyncio.run(start_server())
