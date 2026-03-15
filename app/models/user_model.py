from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class UserPreferences(BaseModel):
    theme: str = "light"
    accentColor: str = "purple"

class UserModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    email: EmailStr
    password: Optional[str] = None
    role: str = "student"
    authProvider: str = "credentials"
    profilePhoto: Optional[str] = None
    picture: Optional[str] = None  # Google picture
    phoneNumber: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    notificationSettings: Dict[str, Any] = Field(default_factory=dict)
    appearanceSettings: Dict[str, Any] = Field(default_factory=dict)
    privacySettings: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
