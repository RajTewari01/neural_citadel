
from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel
from typing import Optional, Dict
import os
import smtplib
from email.mime.text import MIMEText
from cryptography.fernet import Fernet
import secrets
import database as db

router = APIRouter(prefix="/admin", tags=["Admin"])

# Environment Config
from dotenv import load_dotenv
from pathlib import Path
# Load secrets
env_path = Path(__file__).resolve().parent.parent.parent.parent / "configs" / "secrets" / "socials.env"
load_dotenv(env_path)

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_TARGET_EMAIL = os.getenv("ADMIN_EMAIL", "tewari765@gmail.com")

# --- ENCRYPTION KEYS ---
# In production, this KEY should be persistent (env var).
# For this session, we generate one in memory. If server restarts, old tokens invalid.
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)

# Store pending OTPs in memory for short term
# { "session_token": { "otp": "123456", "timestamp": ... } }
pending_auths = {}

class LoginStage1(BaseModel):
    username: str
    password: str

class LoginStage2(BaseModel):
    otp: str
    session_token: str

class BlockRequest(BaseModel):
    is_blocked: bool

# --- HELPER: Send Email ---
# --- HELPER: Send Email ---
def send_otp_email(otp: str):
    # FORCE MOCK for Speed (User reported "superslow" SMTP)
    if True: 
        print(f"\n[FAST LOGIN] >>> To: {ADMIN_TARGET_EMAIL} | OTP: {otp} <<<\n")
        return

    # ... (Legacy SMTP Code below commented out effectively by the return above)

# ...

@router.post("/auth/stage1")
async def admin_auth_stage1(creds: LoginStage1, background_tasks: BackgroundTasks):
    # DEBUG: Print exact credentials received
    print(f"DEBUG AUTH: User='{creds.username}', Pass='{creds.password}'")
    
    u = creds.username.strip().lower()
    p = creds.password.strip().lower() # Case Insensitive for ease

    # Updated to User Request: rajtewari / raj123**
    if (u == "rajtewari" and p == "raj123**") or \
       (u == "admin" and p == "admin123"):
        
        # 2. Generate OTP
        otp = str(secrets.randbelow(900000) + 100000) # 6 digits
        session_token = secrets.token_hex(16)
        
        # 3. Store Encrypted OTP (Protection against memory dumps)
        encrypted_otp = cipher.encrypt(otp.encode()).decode()
        pending_auths[session_token] = encrypted_otp
        
        # 4. Send Email (Background)
        background_tasks.add_task(send_otp_email, otp)
        
        return {"status": "otp_sent", "session_token": session_token}
    
    raise HTTPException(status_code=401, detail="Access Denied: Invalid Credentials")

@router.post("/auth/stage2")
async def admin_auth_stage2(data: LoginStage2):
    # 1. Verify Session
    if data.session_token not in pending_auths:
        raise HTTPException(status_code=401, detail="Session Expired")
        
    encrypted_otp = pending_auths[data.session_token]
    
    # 2. Decrypt & Verify OTP
    try:
        decrypted_otp = cipher.decrypt(encrypted_otp.encode()).decode()
    except:
        raise HTTPException(status_code=401, detail="Security Error: Token Corrupted")

    if data.otp == decrypted_otp:
        del pending_auths[data.session_token] # Burn OTP
        
        # 3. Generate Admin Token (Encrypted)
        # Create a secure token representing the session
        admin_payload = f"admin:{ADMIN_TARGET_EMAIL}"
        admin_token = cipher.encrypt(admin_payload.encode()).decode()
        
        # In DB, ensure admin exists
        user_id = db.create_or_update_user(ADMIN_TARGET_EMAIL, "The Architect", "admin")
        
        return {
            "status": "authorized", 
            "admin_token": admin_token, 
            "user": db.get_user_by_email(ADMIN_TARGET_EMAIL)
        }
        
    raise HTTPException(status_code=401, detail="Invalid OTP")

# --- DASHBOARD STATS ---

@router.get("/stats")
async def get_stats():
    # Only allow if 'admin' header? (Simplified for now)
    return db.get_stats_overview()

# --- USER MANAGEMENT (BAN HAMMER) ---

@router.get("/users")
async def get_users():
    return db.get_all_users()

@router.post("/users/{user_id}/block")
async def block_user(user_id: int, req: BlockRequest):
    # Check if target is admin (Protection)
    conn = db.get_db_connection()
    user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    if user and user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="The Architect cannot be blocked.")

    db.set_block_status(user_id, req.is_blocked)
    action = "BLOCKED" if req.is_blocked else "UNBLOCKED"
    return {"status": "success", "message": f"User {user_id} has been {action}."}

@router.get("/users/{user_id}/audit")
async def get_user_audit(user_id: int):
    """Get last 20 events for a specific user."""
    conn = db.get_db_connection()
    events = conn.execute('''
        SELECT type, timestamp, metadata 
        FROM events 
        WHERE user_id = ? 
        ORDER BY id DESC 
        LIMIT 20
    ''', (user_id,)).fetchall()
    conn.close()
    return [dict(e) for e in events]

# --- DATA SYNC ---

from fastapi import UploadFile, File, Form
from configs.paths import USER_HISTORY_DIR
from datetime import datetime

@router.post("/upload_history")
async def upload_user_history(username: str = Form(...), file: UploadFile = File(...)):
    """
    Backup Android SQLite DB to Server.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-'))
        filename = f"backup_{safe_username}_{timestamp}.db"
        file_path = USER_HISTORY_DIR / filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        print(f"[BACKUP] Saved user history: {file_path}")
        return {"status": "success", "path": str(file_path)}
    except Exception as e:
        print(f"Backup Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload_avatar")
async def upload_user_avatar(username: str = Form(...), file: UploadFile = File(...)):
    """
    Sync User Avatar to Server.
    """
    try:
        safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-'))
        # Overwrite existing: Fixed filename per user
        filename = f"avatar_{safe_username}.jpg"
        
        # Ensure dir exists (it should, but safety first)
        avatar_dir = USER_HISTORY_DIR.parent / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = avatar_dir / filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        print(f"[AVATAR] Saved avatar: {file_path}")
        return {"status": "success", "path": str(file_path)}
    except Exception as e:
        print(f"Avatar Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
