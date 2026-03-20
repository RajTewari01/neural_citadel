"""
Prompt Storage for Image Surgeon
=================================
Save, recall, and manage frequently used prompts.
Supports favorites and auto-suggestions.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# Database location (same as main DB)
DB_PATH = Path(__file__).parent.parent.parent.parent / "assets" / "db" / "img_surgeon" / "prompts.db"


def _get_connection():
    """Get database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            prompt TEXT NOT NULL,
            mode TEXT DEFAULT 'general',
            is_favorite INTEGER DEFAULT 0,
            use_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            last_used TEXT
        )
    """)
    conn.commit()
    return conn


def save_prompt(name: str, prompt: str, mode: str = "general", favorite: bool = False) -> int:
    """
    Save a prompt with a memorable name.
    
    Args:
        name: Short name for quick recall (e.g., "beach", "sunset", "red_dress")
        prompt: Full prompt text
        mode: Category (clothes, background, general)
        favorite: Mark as favorite
        
    Returns:
        Prompt ID
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("""
            INSERT OR REPLACE INTO prompts (name, prompt, mode, is_favorite, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, prompt, mode, 1 if favorite else 0, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_prompt(name: str) -> Optional[str]:
    """
    Get a prompt by name.
    
    Args:
        name: Prompt name
        
    Returns:
        Prompt text or None
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT prompt FROM prompts WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            # Update usage
            conn.execute("""
                UPDATE prompts 
                SET use_count = use_count + 1, last_used = ?
                WHERE name = ?
            """, (datetime.now().isoformat(), name))
            conn.commit()
            return row["prompt"]
        return None
    finally:
        conn.close()


def list_prompts(mode: Optional[str] = None, favorites_only: bool = False) -> List[Dict]:
    """
    List all saved prompts.
    
    Args:
        mode: Filter by mode (clothes, background, general)
        favorites_only: Only show favorites
        
    Returns:
        List of prompt records
    """
    conn = _get_connection()
    try:
        query = "SELECT * FROM prompts WHERE 1=1"
        params = []
        
        if mode:
            query += " AND mode = ?"
            params.append(mode)
        if favorites_only:
            query += " AND is_favorite = 1"
            
        query += " ORDER BY use_count DESC, name ASC"
        
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def suggest_prompts(partial: str, limit: int = 5) -> List[str]:
    """
    Suggest prompts based on partial text match.
    
    Args:
        partial: Partial prompt text
        limit: Max suggestions
        
    Returns:
        List of matching prompt texts
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("""
            SELECT prompt FROM prompts
            WHERE prompt LIKE ? OR name LIKE ?
            ORDER BY use_count DESC
            LIMIT ?
        """, (f"%{partial}%", f"%{partial}%", limit))
        
        return [row["prompt"] for row in cursor.fetchall()]
    finally:
        conn.close()


def delete_prompt(name: str) -> bool:
    """Delete a prompt by name."""
    conn = _get_connection()
    try:
        cursor = conn.execute("DELETE FROM prompts WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def toggle_favorite(name: str) -> bool:
    """Toggle favorite status for a prompt."""
    conn = _get_connection()
    try:
        conn.execute("""
            UPDATE prompts 
            SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
            WHERE name = ?
        """, (name,))
        conn.commit()
        return True
    finally:
        conn.close()
