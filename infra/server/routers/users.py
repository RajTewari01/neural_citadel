from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database as db

router = APIRouter(prefix="/users", tags=["Users"])

class UserSync(BaseModel):
    email: str
    username: str
    role: str = "user"
    photo_url: str = None

@router.post("/sync")
async def sync_user(user: UserSync):
    """
    Called by Mobile App on login to ensure Server DB knows about this user.
    """
    try:
        user_id = db.create_or_update_user(user.email, user.username, user.role, user.photo_url)
        
        # Check Block Status
        if db.is_user_blocked(user_id):
             raise HTTPException(status_code=403, detail="ACCESS DENIED: User is blocked.")
             
        return {"status": "success", "user_id": user_id}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"User Sync Error: {e}")
        # Don't block login if sync fails, but log it
        raise HTTPException(status_code=500, detail=str(e))
