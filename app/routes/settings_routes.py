from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.middleware.auth_middleware import get_current_user
from app.database.connection import get_database
from bson import ObjectId
from passlib.context import CryptContext

router = APIRouter(prefix="/api/users", tags=["Users Settings"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Schemas ──────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phoneNumber: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None
    profileImage: Optional[str] = None
    website: Optional[str] = None
    linkedIn: Optional[str] = None
    github: Optional[str] = None

class NotificationSettings(BaseModel):
    emailNotifications: bool = True
    eventReminders: bool = True
    newEventAlerts: bool = True
    adminMessages: bool = True
    systemNotifications: bool = True
    registrationConfirmations: bool = True
    weeklyDigest: bool = False
    pushNotifications: bool = False

class AppearanceSettings(BaseModel):
    theme: str = "system"          # light | dark | system
    dashboardLayout: str = "comfortable"  # compact | comfortable
    cardStyle: str = "rounded"     # rounded | sharp
    sidebarDefault: str = "collapsed"    # collapsed | expanded
    accentColor: str = "purple"    # purple | blue | green | orange
    fontSize: str = "medium"       # small | medium | large
    animationsEnabled: bool = True
    densityMode: str = "normal"    # normal | compact | spacious

class PrivacySettings(BaseModel):
    showProfileInParticipants: bool = True
    allowProfileViewing: bool = True
    showParticipationHistory: bool = True
    showEmail: bool = False
    showPhone: bool = False
    allowDirectMessages: bool = True

class ChangePassword(BaseModel):
    currentPassword: str
    newPassword: str
    confirmPassword: str


# ─── Profile Routes ───────────────────────────────────────────────────────────

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user = await db["users"].find_one({"_id": ObjectId(current_user["id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["id"] = str(user.pop("_id"))
    user.pop("password", None)
    return {"success": True, "message": "Profile fetched", "data": user}

@router.put("/update-profile")
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    from datetime import datetime
    update_data["updatedAt"] = datetime.utcnow()
    
    await db["users"].update_one({"_id": ObjectId(current_user["id"])}, {"$set": update_data})
    user = await db["users"].find_one({"_id": ObjectId(current_user["id"])})
    user["id"] = str(user.pop("_id"))
    user.pop("password", None)
    return {"success": True, "message": "Profile updated successfully", "data": user}


# ─── Notification Settings ────────────────────────────────────────────────────

@router.get("/notification-settings")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user = await db["users"].find_one({"_id": ObjectId(current_user["id"])}, {"notificationSettings": 1})
    settings = user.get("notificationSettings", NotificationSettings().model_dump()) if user else NotificationSettings().model_dump()
    return {"success": True, "message": "Notification settings fetched", "data": settings}

@router.put("/notification-settings")
async def update_notification_settings(data: NotificationSettings, current_user: dict = Depends(get_current_user)):
    db = get_database()
    await db["users"].update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"notificationSettings": data.model_dump()}}
    )
    return {"success": True, "message": "Notification settings saved", "data": data.model_dump()}


# ─── Appearance Settings ──────────────────────────────────────────────────────

@router.get("/appearance-settings")
async def get_appearance_settings(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user = await db["users"].find_one({"_id": ObjectId(current_user["id"])}, {"appearanceSettings": 1})
    settings = user.get("appearanceSettings", AppearanceSettings().model_dump()) if user else AppearanceSettings().model_dump()
    return {"success": True, "message": "Appearance settings fetched", "data": settings}

@router.put("/appearance-settings")
async def update_appearance_settings(data: AppearanceSettings, current_user: dict = Depends(get_current_user)):
    db = get_database()
    await db["users"].update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"appearanceSettings": data.model_dump()}}
    )
    return {"success": True, "message": "Appearance settings saved", "data": data.model_dump()}


# ─── Privacy Settings ─────────────────────────────────────────────────────────

@router.get("/privacy-settings")
async def get_privacy_settings(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user = await db["users"].find_one({"_id": ObjectId(current_user["id"])}, {"privacySettings": 1})
    settings = user.get("privacySettings", PrivacySettings().model_dump()) if user else PrivacySettings().model_dump()
    return {"success": True, "message": "Privacy settings fetched", "data": settings}

@router.put("/privacy-settings")
async def update_privacy_settings(data: PrivacySettings, current_user: dict = Depends(get_current_user)):
    db = get_database()
    await db["users"].update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"privacySettings": data.model_dump()}}
    )
    return {"success": True, "message": "Privacy settings saved", "data": data.model_dump()}


# ─── Security / Password ──────────────────────────────────────────────────────

@router.post("/change-password")
async def change_password(data: ChangePassword, current_user: dict = Depends(get_current_user)):
    if data.newPassword != data.confirmPassword:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    if len(data.newPassword) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    db = get_database()
    user = await db["users"].find_one({"_id": ObjectId(current_user["id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Google-only users cannot change password
    if user.get("authProvider") == "google" and not user.get("password"):
        raise HTTPException(status_code=400, detail="Your password is managed through Google.")
    
    # Verify current password
    if not user.get("password") or not pwd_context.verify(data.currentPassword, user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    hashed = pwd_context.hash(data.newPassword)
    from datetime import datetime
    await db["users"].update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"password": hashed, "updatedAt": datetime.utcnow()}}
    )
    return {"success": True, "message": "Password changed successfully", "data": None}


@router.get("/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """Return active sessions for the user"""
    db = get_database()
    sessions = await db["sessions"].find({"userId": current_user["id"]}).to_list(20)
    for s in sessions:
        s["id"] = str(s.pop("_id"))
    return {"success": True, "message": "Sessions fetched", "data": sessions}

@router.post("/logout-all")
async def logout_all_sessions(current_user: dict = Depends(get_current_user)):
    """Invalidate all sessions (clear from DB)"""
    db = get_database()
    await db["sessions"].delete_many({"userId": current_user["id"]})
    return {"success": True, "message": "All sessions terminated", "data": None}

@router.delete("/delete-account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Permanently delete user account"""
    db = get_database()
    await db["users"].delete_one({"_id": ObjectId(current_user["id"])})
    await db["registrations"].delete_many({"userId": current_user["id"]})
    await db["notifications"].delete_many({"userId": current_user["id"]})
    await db["wishlists"].delete_many({"userId": current_user["id"]})
    await db["event_comments"].delete_many({"userId": current_user["id"]})
    await db["sessions"].delete_many({"userId": current_user["id"]})
    return {"success": True, "message": "Account deleted", "data": None}
