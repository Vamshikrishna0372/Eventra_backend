from pydantic import BaseModel, EmailStr
from typing import Optional
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

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    picture: Optional[str] = None
    department: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    authProvider: str = "credentials"
    picture: Optional[str] = None
    department: Optional[str] = None
    createdAt: datetime
