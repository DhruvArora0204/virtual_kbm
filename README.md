# AI Gesture Control System

An open-source computer vision system that provides a virtual mouse and virtual keyboard controlled via real-time hand gestures. This project consists of a Python-based backend utilizing OpenCV and MediaPipe for hand tracking, and an Electron-based React frontend providing a transparent, always-on-top overlay.

## Features
- **Virtual Mouse Mode**: Move your mouse by pointing with your index finger. Pinch (thumb and index finger) to click.
- **Virtual Keyboard Mode**: Track your gestures to interact with on-screen keyboard elements.
- **Low-Latency Streaming**: Real-time communication between the backend and frontend using WebSockets.
- **Always-on-top Overlay**: A transparent React-based Electron frontend for seamless desktop interaction.

## Prerequisites
- Node.js (v18+)
- Python (3.10+)
- A Webcam

## Setup Instructions

### 1. Backend Setup
1. Open a terminal and navigate to the project root directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure that `hand_landmarker.task` is in the root directory for MediaPipe)*

### 2. Frontend Setup
1. Open a terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```

## Running the Application

**Using the included script (Windows):**
Simply run the `start.bat` file from the root directory. This will start both the Python backend and the Electron frontend simultaneously.

**Running manually:**
1. **Start Backend**: `python main.py`
2. **Start Frontend**: Open another terminal, navigate to `frontend/`, and run `npm run dev`.

## How to Use
- Hold your hand up to the webcam.
- **Mouse Movement**: Keep your index finger up. The cursor will follow your finger's movement.
- **Click**: Pinch your thumb and index finger together.
- Switch between **Mouse** and **Keyboard** modes using the on-screen UI overlay.
