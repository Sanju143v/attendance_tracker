from flask import Flask, render_template, jsonify, request
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Database setup
DB_FILE = 'attendance.db'

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE logs 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp TEXT, 
                      type TEXT)''')
        conn.commit()
        conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/attendance", methods=['POST'])
def mark_attendance():
    data = request.json
    action_type = data.get('type')
    
    if action_type not in ['check-in', 'check-out']:
        return jsonify({'error': 'Invalid action'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, type) VALUES (?, ?)", 
              (datetime.now().isoformat(), action_type))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'action': action_type})

@app.route("/api/logs")
def get_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM logs ORDER BY timestamp DESC LIMIT 20').fetchall()
    conn.close()
    
    return jsonify([dict(log) for log in logs])

@app.route("/api/stats")
def get_stats():
    # Simple dummy stats for now, real calc would be more complex
    # Calculating hours would require pairing check-ins and check-outs
    conn = get_db_connection()
    # Just counting check-ins for demo purposes as "hours" is complex without user sessions
    logs = conn.execute("SELECT COUNT(*) as count FROM logs WHERE type='check-in' AND date(timestamp) = date('now')").fetchone()
    today_count = logs['count']
    
    conn.close()
    
    return jsonify({
        'today_hours': today_count, # Simplified: 1 checkin = 1 unit
        'week_hours': today_count * 5 # Dummy projection
    })

if __name__ == "__main__":
    # Host on 0.0.0.0 to be accessible on network
    app.run(debug=True, host='0.0.0.0', port=5000)
