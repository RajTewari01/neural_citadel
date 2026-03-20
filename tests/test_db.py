"""
Test Database Manager
======================
SQLite database for storing test results and logs.
Location: assets/db/test/test.db
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Database path
_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = _ROOT / "assets" / "db" / "test" / "test.db"


class TestDB:
    """SQLite database for test logging."""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Test runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds REAL,
                    error_message TEXT
                )
            """)
            
            # Test logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES test_runs(id)
                )
            """)
            
            # Generation results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    prompt TEXT,
                    negative_prompt TEXT,
                    model_name TEXT,
                    vae_name TEXT,
                    scheduler TEXT,
                    width INTEGER,
                    height INTEGER,
                    steps INTEGER,
                    cfg REAL,
                    seed INTEGER,
                    output_path TEXT,
                    generation_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES test_runs(id)
                )
            """)
            
            conn.commit()
    
    def start_test(self, test_name: str) -> int:
        """Start a new test run. Returns run_id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO test_runs (test_name, status) VALUES (?, ?)",
                (test_name, "running")
            )
            conn.commit()
            return cursor.lastrowid
    
    def end_test(self, run_id: int, status: str, error: str = None):
        """End a test run."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE test_runs 
                SET status = ?, ended_at = CURRENT_TIMESTAMP, 
                    duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400,
                    error_message = ?
                WHERE id = ?
            """, (status, error, run_id))
            conn.commit()
    
    def log(self, run_id: int, level: str, message: str):
        """Add a log entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO test_logs (run_id, level, message) VALUES (?, ?, ?)",
                (run_id, level, message)
            )
            conn.commit()
    
    def log_generation(self, run_id: int, config: Dict[str, Any], output_path: str, 
                       seed: int, generation_time: float):
        """Log a generation result."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO generations 
                (run_id, prompt, negative_prompt, model_name, vae_name, scheduler,
                 width, height, steps, cfg, seed, output_path, generation_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                config.get("prompt", ""),
                config.get("neg_prompt", ""),
                config.get("model_name", ""),
                config.get("vae", ""),
                config.get("scheduler_name", ""),
                config.get("width", 0),
                config.get("height", 0),
                config.get("steps", 0),
                config.get("cfg", 0.0),
                seed,
                str(output_path),
                generation_time
            ))
            conn.commit()
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent test runs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_runs ORDER BY started_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_logs(self, run_id: int) -> List[Dict]:
        """Get logs for a specific run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_logs WHERE run_id = ? ORDER BY timestamp
            """, (run_id,))
            return [dict(row) for row in cursor.fetchall()]


# Convenience functions
_db = None

def get_db() -> TestDB:
    """Get or create the database instance."""
    global _db
    if _db is None:
        _db = TestDB()
    return _db
