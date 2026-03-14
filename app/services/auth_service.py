from fastapi import HTTPException
from app.database.connection import get_database
from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreate, UserLogin
from app.middleware.auth_middleware import get_password_hash, verify_password, create_access_token
from bson import ObjectId
import os
from google.oauth2 import id_token
from google.auth.transport import requests

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

class AuthService:
    @staticmethod
    async def register_user(user_data: UserCreate):
        db = get_database()
        existing_user = await db["users"].find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        user_dict = user_data.model_dump()
        user_dict["password"] = get_password_hash(user_dict["password"])
        
        new_user = UserModel(**user_dict)
        result = await db["users"].insert_one(new_user.model_dump(by_alias=True, exclude_none=True))
        
        created_user = await db["users"].find_one({"_id": result.inserted_id})
        created_user["id"] = str(created_user.pop("_id"))
        return created_user

    @staticmethod
    async def login_user(login_data: UserLogin):
        db = get_database()
        user = await db["users"].find_one({"email": login_data.email})
        if not user or not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token(data={"sub": str(user["_id"]), "role": user.get("role", "student")})
        user["id"] = str(user.pop("_id"))
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    @staticmethod
    async def google_login_user(token: str):
        try:
            # Verify Google Token
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
            
            # Extract info
            email = idinfo['email']
            name = idinfo.get('name', email.split('@')[0])
            picture = idinfo.get('picture')
            
            db = get_database()
            user = await db["users"].find_one({"email": email})
            
            if not user:
                # Create new user
                new_user_data = {
                    "name": name,
                    "email": email,
                    "authProvider": "google",
                    "picture": picture,
                    "role": "student"
                }
                new_user = UserModel(**new_user_data)
                result = await db["users"].insert_one(new_user.model_dump(by_alias=True, exclude_none=True))
                user = await db["users"].find_one({"_id": result.inserted_id})
            
            # Generate JWT
            access_token = create_access_token(data={"sub": str(user["_id"]), "role": user.get("role", "student")})
            user["id"] = str(user.pop("_id"))
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            }
        except ValueError:
            # Invalid token
            raise HTTPException(status_code=401, detail="Invalid Google token")

    @staticmethod
    async def get_profile(user_id: str):
        db = get_database()
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user["id"] = str(user.pop("_id"))
        # Remove password hash from response
        if "password" in user:
            del user["password"]
        return user

    @staticmethod
    async def update_profile(user_id: str, update_data: dict):
        db = get_database()
        # Filter out none values
        update_fields = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_fields:
            return await AuthService.get_profile(user_id)
            
        result = await db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return await AuthService.get_profile(user_id)
