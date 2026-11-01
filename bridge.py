import asyncio
import websockets
import json
from datetime import datetime
import sqlite3
import os
import sys
import webbrowser

# Import both our database functions
from db_manager import insert_transaction, get_last_entry, get_all_transactions, DB_FILE

CONNECTED_CLIENTS = set()

# ==========================================
# CUSTOM FOLDER PATH RESOLUTION 
# ==========================================
# Find the master folder where this Python script (or .exe) is running
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate into your specific folders
CPP_PATH = os.path.join(BASE_DIR, "ANPR_Project", "build", "Debug", "ANPR_App.exe")
HTML_PATH = os.path.join(BASE_DIR, "ParkingVIEW_UI", "index.html")

# ==========================================
# THE RULES ENGINE (HOSPITAL BUSINESS LOGIC)
# ==========================================
def apply_gate_rules(vrn, v_class, base_amount, entry_gate, exit_gate):
    exempt_gates = ["Entry Gate 1 (Staff & Vendors)", "B-1 Entry (Reserved Staff)"]
    if entry_gate in exempt_gates:
        print(f"\n[RULES ENGINE]: {entry_gate} detected. Overriding fee to ₹0.00.")
        return 0.00
        
    if exit_gate == "Exit Gate 4" or exit_gate == "Exit Ramp 1 (Collection point)":
        print(f"\n[RULES ENGINE]: Exit detected. Searching database for {vrn}...")
        
        last_entry = get_last_entry(vrn)
          
        if last_entry:
            entry_time_str, original_entry_gate = last_entry
            entry_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
            time_spent = datetime.now() - entry_time
            minutes_spent = time_spent.total_seconds() / 60
            
            if minutes_spent <= 2:
                final_fee = float(base_amount)
            else:
                extra_minutes = int(minutes_spent - 2) + 1 
                final_fee = float(base_amount) + (extra_minutes * 20)

            print(f"[RULES ENGINE]: Match found! Entered at {original_entry_gate}.")
            print(f"[RULES ENGINE]: {vrn} spent {minutes_spent:.2f} minutes inside.")
            print(f"[RULES ENGINE]: Final Calculated Exit Fee: ₹{final_fee}")
            return final_fee
            
        else:
            print(f"[RULES ENGINE]: WARNING - No entry record found for {vrn}!")
            print(f"[RULES ENGINE]: Charging Maximum Lost-Ticket Penalty.")
            return 500.00
            
    return float(base_amount)

# ==========================================
# WEBSOCKET SERVER LOGIC
# ==========================================
async def register(websocket):
    CONNECTED_CLIENTS.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data.get("action") == "SAVE_TRANSACTION":
                vrn = data.get("vrn")
                v_class = data.get("vehicle_class")
                amount = data.get("amount")
                entry = data.get("entry_gate")
                exit_g = data.get("exit_gate")

                final_amount = apply_gate_rules(vrn, v_class, amount, entry, exit_g)
                success = insert_transaction(vrn, v_class, final_amount, entry, exit_g)
                if success:
                    print(f">>> HARDWARE COMMAND: OPEN BARRIER FOR {vrn} <<<\n")

            elif data.get("action") == "FETCH_HISTORY":
                print("\n[Python Bridge]: Dashboard requested database history...")
                history_data = get_all_transactions()
                await websocket.send(json.dumps({
                    "action": "HISTORY_DATA",
                    "records": history_data
                }))
                print("[Python Bridge]: History sent successfully!")

    finally:
        CONNECTED_CLIENTS.remove(websocket)

async def broadcast(message):
    if CONNECTED_CLIENTS:
        await asyncio.gather(*[client.send(json.dumps(message)) for client in CONNECTED_CLIENTS])

async def run_cpp_engine():
    print(f"\n[System]: Launching C++ ANPR Engine from:\n -> {CPP_PATH}")
    try:
        process = await asyncio.create_subprocess_exec(
            CPP_PATH,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes: break
            
            line = line_bytes.decode('utf-8', errors='replace').strip()
            
            if ">>> SCANNED VRN:" in line:
                plate = line.split(">>> SCANNED VRN:")[1].split("<<<")[0].strip()
                print(f"[Python Bridge]: Caught Plate {plate}! Sending to Dashboard...")
                await broadcast({"action": "NEW_SCAN", "plate_number": plate, "confidence": "94%"})
            elif ">>> FRAME:" in line:
                base64_frame = line.split(">>> FRAME:")[1].strip()
                await broadcast({"action": "VIDEO_FRAME", "frame": base64_frame})
            else:
                print(f"[C++]: {line}") 

    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR]: Could not find C++ engine!")
        print(f"Please ensure it exists exactly at: {CPP_PATH}")

async def main():
    # --- DIAGNOSTIC PATH CHECKER ---
    file_uri = f"file:///{HTML_PATH.replace(os.sep, '/')}"
    
    print("\n==========================================")
    print("🔍 DIAGNOSTIC PATH CHECK:")
    print(f"1. Python thinks it is running from: {BASE_DIR}")
    print(f"2. Looking for Website at: {HTML_PATH}")
    print(f"3. Looking for C++ Engine at: {CPP_PATH}")
    print("==========================================\n")

    # Check if the HTML file actually exists where Python is looking
    if not os.path.exists(HTML_PATH):
        print(f"[CRITICAL ERROR]: I cannot find index.html!")
        print("Please check your folder names. Make sure 'ParkingVIEW_UI' is spelled correctly and 'index.html' is directly inside it.")
        return # Stop the script so you can fix the folders
        
    print(f"[System]: Auto-Opening Dashboard...")
    try:
        webbrowser.open(file_uri)
    except Exception as e:
        print(f"[ERROR]: Could not auto-open browser: {e}")
    
    server = await websockets.serve(register, "localhost", 8765)
    print("\n[System]: Python Bridge Online. Waiting for UI connection...")
    await asyncio.gather(server.wait_closed(), run_cpp_engine())

if __name__ == "__main__":
    asyncio.run(main())