from fastapi import APIRouter, Depends
from app.schemas.user_schema import UserCreate, UserLogin, GoogleLogin
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
async def register(user_data: UserCreate):
    result = await AuthService.register_user(user_data)
    return {
        "success": True,
        "message": "User registered successfully",
        "data": result
    }

@router.post("/login")
async def login(login_data: UserLogin):
    result = await AuthService.login_user(login_data)
    return {
        "success": True,
        "message": "Login successful",
        "data": result
    }

@router.post("/google")
async def google_login(login_data: GoogleLogin):
    result = await AuthService.google_login_user(login_data.token)
    return {
        "success": True,
        "message": "Google login successful",
        "data": result
    }

users_router = APIRouter(prefix="/api/users", tags=["Users"])

@users_router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    result = await AuthService.get_profile(current_user["id"])
    return {
        "success": True,
        "message": "User profile fetched successfully",
        "data": result
    }

from app.schemas.user_schema import UserUpdate
@users_router.put("/profile")
async def update_profile(update_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    result = await AuthService.update_profile(current_user["id"], update_data.model_dump(exclude_unset=True))
    return {
        "success": True,
        "message": "User profile updated successfully",
        "data": result
    }

@users_router.get("/notification-settings")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    user = await AuthService.get_profile(current_user["id"])
    return {"success": True, "data": user.get("notificationSettings", {})}

@users_router.put("/notification-settings")
async def update_notification_settings(settings: dict, current_user: dict = Depends(get_current_user)):
    result = await AuthService.update_profile(current_user["id"], {"notificationSettings": settings})
    return {"success": True, "message": "Notification settings updated", "data": result.get("notificationSettings", {})}

@users_router.get("/appearance-settings")
async def get_appearance_settings(current_user: dict = Depends(get_current_user)):
    user = await AuthService.get_profile(current_user["id"])
    return {"success": True, "data": user.get("appearanceSettings", {})}

@users_router.put("/appearance-settings")
async def update_appearance_settings(settings: dict, current_user: dict = Depends(get_current_user)):
    result = await AuthService.update_profile(current_user["id"], {"appearanceSettings": settings})
    return {"success": True, "message": "Appearance settings updated", "data": result.get("appearanceSettings", {})}

@users_router.get("/privacy-settings")
async def get_privacy_settings(current_user: dict = Depends(get_current_user)):
    user = await AuthService.get_profile(current_user["id"])
    return {"success": True, "data": user.get("privacySettings", {})}

@users_router.put("/privacy-settings")
async def update_privacy_settings(settings: dict, current_user: dict = Depends(get_current_user)):
    result = await AuthService.update_profile(current_user["id"], {"privacySettings": settings})
    return {"success": True, "message": "Privacy settings updated", "data": result.get("privacySettings", {})}

@users_router.get("/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    # Mocking sessions for now as per frontend expectation
    from datetime import datetime
    now = datetime.utcnow().isoformat() + "Z"
    return {"success": True, "data": [
        {"id": "1", "device": "Current Device", "ip": "127.0.0.1", "browser": "Chrome", "lastActive": now}
    ]}
