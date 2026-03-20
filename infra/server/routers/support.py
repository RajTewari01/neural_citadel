import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
from pathlib import Path
from datetime import datetime

# Import Database & Configs
from infra.server import database
from configs import paths

router = APIRouter(prefix="/support", tags=["Support"])

# Configuration (Environment Variables preferred in production)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # SSL
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "neural.citadel.sys@gmail.com") 
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "") # App Password
TARGET_EMAIL = "tewari765@gmail.com"

# REPORTS DIR
REPORTS_DIR = paths.ASSETS_DIR / "temp" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def send_bug_email(description: str, steps: str, user_id: str, screenshot_bytes: bytes, filename: str):
    if not SMTP_PASSWORD:
        print("Support: SMTP_PASSWORD not set. Email skipped.")
        return

    msg = MIMEMultipart()
    msg['Subject'] = f"[BUG REPORT] Neural Citadel - User {user_id}"
    msg['From'] = SMTP_EMAIL
    msg['To'] = TARGET_EMAIL

    body = f"""
    <html>
      <body>
        <h2>🐛 Bug Report for Neural Citadel</h2>
        <p><strong>User ID:</strong> {user_id}</p>
        <hr>
        <h3>Description</h3>
        <p>{description}</p>
        <h3>Steps to Reproduce</h3>
        <p>{steps}</p>
        <hr>
        <p><em>Screenshot attached.</em></p>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    # Attach Screenshot
    if screenshot_bytes:
        img = MIMEImage(screenshot_bytes, name=filename)
        msg.attach(img)

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Support: Bug Report sent to {TARGET_EMAIL}")
    except Exception as e:
        print(f"Support Error: Failed to send email. {e}")

@router.post("/report_bug")
async def report_bug(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    steps: str = Form(""),
    user_id: str = Form("Unknown"),
    screenshot: UploadFile = File(...)
):
    # 1. Read Content
    content = await screenshot.read()
    filename = screenshot.filename or f"bug_report.png"
    
    # 2. Save to Disk (for Admin Panel)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = REPORTS_DIR / safe_filename
    
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Public URL (Mapped to /static/temp/reports/...)
    public_url = f"/static/temp/reports/{safe_filename}"
    
    # 3. Save to Database
    database.save_report(
        user_id=user_id,
        description=description,
        steps=steps,
        screenshot_path=public_url,
        severity="High" # Defaulting for now, could be passed from UI
    )

    # 4. Email (Background)
    background_tasks.add_task(
        send_bug_email, 
        description, 
        steps, 
        user_id, 
        content, 
        filename
    )
    
    return {"status": "success", "message": "Bug report logged and queued."}

# --- ADMIN ENDPOINTS ---

@router.get("/admin/reports")
async def list_reports():
    """Admin: Get all bug reports"""
    return database.get_all_reports()

@router.delete("/admin/reports/{report_id}")
async def delete_report(report_id: int):
    """Admin: Delete a report"""
    database.delete_report(report_id)
    return {"status": "deleted"}
