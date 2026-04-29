@echo off
echo Starting OpenCV Backend...
start cmd /k ".\venv\Scripts\activate && python main.py"

echo Starting Electron Frontend...
cd frontend
npm run dev
