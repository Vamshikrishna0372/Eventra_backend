from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleLogin(BaseModel):
    token: str

class UserPreferences(BaseModel):
    theme: str = "light"
    accentColor: str = "purple"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    profilePhoto: Optional[str] = None
    picture: Optional[str] = None
    phoneNumber: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    preferences: Optional[UserPreferences] = None
    notificationSettings: Optional[Dict[str, Any]] = None
    appearanceSettings: Optional[Dict[str, Any]] = None
    privacySettings: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    authProvider: str = "credentials"
    profilePhoto: Optional[str] = None
    picture: Optional[str] = None
    phoneNumber: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    preferences: UserPreferences = UserPreferences()
    notificationSettings: Dict[str, Any] = {}
    appearanceSettings: Dict[str, Any] = {}
    privacySettings: Dict[str, Any] = {}
    createdAt: datetime
