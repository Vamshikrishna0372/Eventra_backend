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
@users_router.put("/update-profile")
async def update_profile(update_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    result = await AuthService.update_profile(current_user["id"], update_data.model_dump(exclude_unset=True))
    return {
        "success": True,
        "message": "User profile updated successfully",
        "data": result
    }
