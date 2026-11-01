import sqlite3
import os
from datetime import datetime

DB_FILE = 'toll_database.db'

def init_db():
    print(f"Checking Database: {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            vrn TEXT NOT NULL,
            confidence_score INTEGER,
            vehicle_class TEXT NOT NULL,
            amount REAL NOT NULL,
            entry_gate TEXT,
            exit_gate TEXT,
            transaction_type TEXT DEFAULT 'CASH',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gate_config (
            gate_id TEXT PRIMARY KEY,
            gate_type TEXT,
            base_fee REAL
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_transaction(vrn, vehicle_class, amount, entry_gate="Unknown", exit_gate="Unknown"):
    ticket_id = f"TCK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # NEW: Grab the exact local real-world time
    local_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # NEW: Explicitly insert the local_timestamp into the database
        cursor.execute('''
            INSERT INTO transactions 
            (ticket_id, vrn, vehicle_class, amount, entry_gate, exit_gate, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ticket_id, vrn, vehicle_class, amount, entry_gate, exit_gate, local_timestamp))
        
        conn.commit()
        print(f"[DATABASE LOG]: Saved Transaction -> {vrn} | {vehicle_class} | ₹{amount} at {local_timestamp}")
        return True
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR]: Failed to save transaction: {e}")
        return False
        
    finally:
        if conn: conn.close()

# ==========================================
# NEW FUNCTION: MEMORY RETRIEVAL
# ==========================================
def get_last_entry(vrn):
    """
    Searches the database for the last time this vehicle entered the hospital.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Find the most recent record for this VRN that is NOT an exit
        cursor.execute('''
            SELECT timestamp, entry_gate 
            FROM transactions 
            WHERE vrn = ? AND entry_gate != '--Select--'
            ORDER BY timestamp DESC LIMIT 1
        ''', (vrn,))
        
        result = cursor.fetchone()
        return result # Returns a tuple: (timestamp, entry_gate) or None if not found
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR]: {e}")
        return None
    finally:
        if conn: conn.close()

# ==========================================
# NEW FUNCTION: FETCH ALL HISTORY
# ==========================================
def get_all_transactions(limit=50):
    """
    Fetches the most recent transaction records from the database.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Standard SQL SELECT query to pull the history
        cursor.execute('''
            SELECT ticket_id, vrn, vehicle_class, amount, entry_gate, exit_gate, timestamp
            FROM transactions
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return rows
        
    except sqlite3.Error as e:
        print(f"[DATABASE ERROR]: {e}")
        return []
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    init_db()