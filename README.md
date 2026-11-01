====================================================================
PROJECT: ParkingVIEW Level-2 ANPR Toll Automation System
DEVELOPED BY: Abhishek Kumar
DATE: August 2026
====================================================================

--- OVERVIEW ---
This project is a real-time, hybrid Automated Number Plate Recognition (ANPR) and Toll Management system made entirely by Abhishek Kumar. It uses a high-speed C++ computer vision engine to scan video feeds, and a Python WebSocket backend to process business logic, calculate fees, and push live data to a dynamic HTML/JS dashboard.

--- ARCHITECTURE & TECH STACK ---

1. COMPUTER VISION ENGINE (C++ / OpenCV / Tesseract OCR)
   - Captures live video and applies Gaussian blur and Canny edge detection.
   - Utilizes Tesseract (PSM_SINGLE_LINE) for high-speed alphanumeric extraction, completely eliminating processing lag.
   - Streams base64 encoded video frames directly to the backend.

2. THE BACKEND & APPLICATION BRIDGE (Python)
   - Subprocess Management: Utilizes `asyncio.create_subprocess_exec` to run the compiled C++ engine (ANPR_App.exe) asynchronously, capturing standard output (stdout) in real-time without blocking the main thread.
   - Real-Time Communication: Implements a live, bi-directional WebSocket server (`websockets` library) running on localhost:8765. This instantly pushes base64 video frames, newly scanned license plates, and hardware statuses (Barrier, OHLS, Traffic Lights) to the frontend without requiring page reloads.
   - Database Management: Implements a serverless relational database using `sqlite3` (via db_manager.py) to persistently log vehicle entries/exits, fetch entry times for duration calculations, and serve historical data to the UI.
   - Business Rules Engine: Features a dynamic logic block (`apply_gate_rules`) to handle financial rules. It automatically grants fee exemptions based on specific hardware triggers, calculates minute-based exit fees, and enforces maximum penalties for lost entry tickets.
   - Data Sanitization: Runs custom regex and logic filters (`is_valid_plate`) before any data hits the database or UI. It enforces strict alphanumeric mixing and length requirements to aggressively filter out false-positives like car logos or phone numbers.

3. FRONTEND DASHBOARD (HTML / CSS / JavaScript)
   - Real-time PiP (Picture-in-Picture) video monitoring.
   - Dynamic hardware status grid (Barrier, Traffic Lights, OHLS).
   - Instant database history viewing and theme-switching capabilities.
   - Asynchronous event listeners that handle backend WebSocket payloads seamlessly.

--- HOW TO RUN THE PROJECT ---
1. Open a terminal or command prompt inside this main master folder.
2. Ensure you have Python installed on your system.
3. Run the following command:
   
   python bridge.py

4. The system will automatically:
   - Launch the background C++ ANPR engine (ANPR_App.exe).
   - Start the WebSocket server on localhost:8765.
   - Open the ParkingVIEW dashboard in your default web browser.

--- IMPORTANT NOTES FOR REVIEWERS ---
- Ensure all required OpenCV and Tesseract .dll files remain in the \build\Debug\ directory next to the compiled .exe, or the C++ engine will not launch.
- If testing with a webcam, hold the test license plate clearly in the frame. The Python bridge requires a mixed alphanumeric string of at least 5 characters to trigger a valid scan and avoid processing background noise.
