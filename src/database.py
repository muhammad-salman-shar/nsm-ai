import sqlite3
import json
import os

DB_PATH = "data/nsm_core.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create table to store the entire brain state as a JSON string per user
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS brains (
            user_id TEXT PRIMARY KEY,
            state_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_brain(user_id, state_dict):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    json_data = json.dumps(state_dict)
    cursor.execute('''
        INSERT INTO brains (user_id, state_json) 
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET state_json=excluded.state_json
    ''', (user_id, json_data))
    conn.commit()
    conn.close()

def load_brain(user_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT state_json FROM brains WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None

def delete_brain(user_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM brains WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Initialize on import
init_db()
