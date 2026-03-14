from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    email: EmailStr
    password: Optional[str] = None
    role: str = "student"
    authProvider: str = "credentials"
    profileImage: Optional[str] = None
    phoneNumber: Optional[str] = None
    department: Optional[str] = None
    status: str = "active"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
