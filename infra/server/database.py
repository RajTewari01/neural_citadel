
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


from pathlib import Path
import sys

# Ensure root is in path to import configs
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from configs import paths

DB_PATH = paths.DB_DIR / "citadel.db"
# Ensure directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Enable Write-Ahead Logging for concurrency
    c.execute('PRAGMA journal_mode=WAL;')

    # USERS Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT,
            last_seen TEXT
        )
    ''')

    # EVENTS Table (The Analytics Engine)
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, -- chat, image_gen, newspaper, login, error
            user_id INTEGER,
            timestamp TEXT,
            metadata TEXT -- JSON string for extra details (e.g. prompt length, model used)
        )
    ''')

    # MESSAGES Table (The Content History)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT, -- user, assistant, system
            content TEXT,
            type TEXT DEFAULT 'text', -- text, image
            timestamp TEXT,
            is_deleted INTEGER DEFAULT 0 -- Soft Delete flag
        )
    ''')

    # REPORTS Table (Bug Reporting System)
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            description TEXT,
            steps TEXT,
            screenshot_path TEXT,
            severity TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open', -- Open, Investigating, Resolved
            timestamp TEXT
        )
    ''')

    
    # Create Default Admin if not exists
    # We encrypt this properly in the real flow, but this is the fallback root
    c.execute("SELECT * FROM users WHERE email = 'admin'")
    if not c.fetchone():
        c.execute('''
            INSERT INTO users (username, email, password_hash, role, created_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('The Architect', 'admin', 'admin123', 'admin', datetime.now().isoformat(), datetime.now().isoformat()))

    # MIGRATIONS
    try:
        c.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()
    conn.close()
    print("Locked & Loaded: Citadel Database Initialized.")

# --- USER MANAGEMENT ---

def get_user_by_email(email: str):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_or_update_user(email: str, username: str, role: str = 'user', photo_url: str = None):
    conn = get_db_connection()
    c = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Check exist
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    existing = c.fetchone()
    
    if existing:
        if photo_url:
            c.execute('UPDATE users SET last_seen = ?, photo_url = ? WHERE email = ?', (now, photo_url, email))
        else:
            c.execute('UPDATE users SET last_seen = ? WHERE email = ?', (now, email))
        user_id = existing['id']
    else:
        c.execute('''
            INSERT INTO users (username, email, role, photo_url, created_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, role, photo_url, now, now))
        user_id = c.lastrowid
        
    conn.commit()
    conn.close()
    return user_id

def set_block_status(user_id: int, is_blocked: bool):
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_blocked = ? WHERE id = ?', (1 if is_blocked else 0, user_id))
    conn.commit()
    conn.close()

def is_user_blocked(user_id: int) -> bool:
    conn = get_db_connection()
    row = conn.execute('SELECT is_blocked FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return row and row['is_blocked'] == 1

def get_all_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY last_seen DESC').fetchall()
    conn.close()
    return [dict(u) for u in users]

# --- ANALYTICS ENGINE ---

def log_event(type: str, user_email: str = None, metadata: Dict[str, Any] = None):
    """
    Logs an event to the Matrix.
    """
    conn = get_db_connection()
    user_id = None
    
    if user_email:
        u = conn.execute('SELECT id FROM users WHERE email = ?', (user_email,)).fetchone()
        if u: user_id = u['id']
        
    meta_json = json.dumps(metadata) if metadata else '{}'
    
    conn.execute('''
        INSERT INTO events (type, user_id, timestamp, metadata)
        VALUES (?, ?, ?, ?)
    ''', (type, user_id, datetime.now().isoformat(), meta_json))
    
    # Pruning: Keep only last 20 events per user to prevent explosion
    if user_id:
        conn.execute('''
            DELETE FROM events 
            WHERE user_id = ? 
            AND id NOT IN (
                SELECT id FROM events 
                WHERE user_id = ? 
                ORDER BY id DESC 
                LIMIT 20
            )
        ''', (user_id, user_id))
    else:
        # Global prune for anonymous events (Keep last 100)
        conn.execute('''
            DELETE FROM events 
            WHERE user_id IS NULL 
            AND id NOT IN (
                SELECT id FROM events 
                WHERE user_id IS NULL 
                ORDER BY id DESC 
                LIMIT 100
            )
        ''')
    
    conn.commit()
    conn.close()

def log_message(user_email: str, role: str, content: str, msg_type: str = 'text'):
    conn = get_db_connection()
    user_id = None
    if user_email:
        u = conn.execute('SELECT id FROM users WHERE email = ?', (user_email,)).fetchone()
        if u: user_id = u['id']
    
    conn.execute('''
        INSERT INTO messages (user_id, role, content, type, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, role, content, msg_type, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_user_history(user_id: int, include_deleted: bool = False):
    conn = get_db_connection()
    query = 'SELECT * FROM messages WHERE user_id = ?'
    if not include_deleted:
        query += ' AND is_deleted = 0'
    query += ' ORDER BY timestamp ASC'
    
    msgs = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return [dict(m) for m in msgs]

def soft_delete_message(message_id: int):
    conn = get_db_connection()
    conn.execute('UPDATE messages SET is_deleted = 1 WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()

def get_stats_overview():
    conn = get_db_connection()
    
    # Total Users
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    
    # Total Requests
    total_reqs = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    
    # Usage by Type (Pie Chart)
    by_type = conn.execute('SELECT type, COUNT(*) as count FROM events GROUP BY type').fetchall()
    
    # Activity over time (Line Chart - Last 24h by hour)
    # SQLite string slicing for hour: YYYY-MM-DDTHH
    by_hour = conn.execute('''
        SELECT strftime('%Y-%m-%dT%H', timestamp) as hour, COUNT(*) as count 
        FROM events 
        GROUP BY hour 
        ORDER BY hour DESC 
        LIMIT 24
    ''').fetchall()
    
    # God Mode Feed - ENHANCED with User Info
    recent = conn.execute('''
        SELECT e.type, e.timestamp, e.metadata, u.username, u.email, u.photo_url
        FROM events e
        LEFT JOIN users u ON e.user_id = u.id
        ORDER BY e.id DESC LIMIT 50
    ''').fetchall()
    
    # Model Usage (Extract context from metadata)
    # SQLite JSON Support required
    model_stats = {}
    try:
        # Simple string matching if json_extract isn't available or for robustness
        # This gets all chat events and python-side parsing (safer given sqlite versions)
        chat_events = conn.execute("SELECT metadata FROM events WHERE type='chat'").fetchall()
        for row in chat_events:
            try:
                meta = json.loads(row['metadata'])
                ctx = meta.get('context', 'Unknown')
                model_stats[ctx] = model_stats.get(ctx, 0) + 1
            except: pass
    except Exception as e:
        print(f"Stats Error: {e}")
        
    conn.close()
    
    return {
        "total_users": total_users,
        "total_events": total_reqs,
        "by_type": {row['type']: row['count'] for row in by_type},
        "by_model": model_stats, # New Stat
        "by_hour": [{"hour": row['hour'], "count": row['count']} for row in by_hour],
        "recent_events": [dict(r) for r in recent]
    }

# --- REPORT MANAGEMENT ---

def save_report(user_id: str, description: str, steps: str, screenshot_path: str, severity: str = "Medium"):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO reports (user_id, description, steps, screenshot_path, severity, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, description, steps, screenshot_path, severity, 'Open', datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_reports():
    conn = get_db_connection()
    reports = conn.execute('SELECT * FROM reports ORDER BY timestamp DESC').fetchall()
    conn.close()
    return [dict(r) for r in reports]

def delete_report(report_id: int):
    conn = get_db_connection()
    conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
    conn.commit()
    conn.close()

