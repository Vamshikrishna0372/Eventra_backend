from fastapi import HTTPException
from app.database.connection import get_database
from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreate, UserLogin
from app.middleware.auth_middleware import get_password_hash, verify_password, create_access_token
from bson import ObjectId
import os
import httpx

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

class AuthService:
    @staticmethod
    async def register_user(user_data: UserCreate):
        db = get_database()
        try:
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
        except HTTPException:
            raise
        except Exception as e:
            import logging
            error_msg = str(e)
            logging.error(f"Error in user registration: {error_msg}")
            if "DNS" in error_msg or "selection timeout" in error_msg:
                raise HTTPException(status_code=503, detail="Database connection issue. Please check your MongoDB Atlas cluster hostname in .env")
            raise HTTPException(status_code=500, detail="Registration failed due to server error")

    @staticmethod
    async def login_user(login_data: UserLogin):
        db = get_database()
        try:
            user = await db["users"].find_one({"email": login_data.email})
            if not user or not verify_password(login_data.password, user["password"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            access_token = create_access_token(data={"sub": str(user["_id"]), "role": user.get("role", "student")})
            
            # Check if user is a coordinator (check both new and legacy storage)
            is_coordinator = await db["coordinators"].find_one({"userId": str(user["_id"])}) is not None
            if not is_coordinator:
                is_coordinator = await db["events"].find_one({"coordinators.userId": str(user["_id"])}) is not None
            
            # Return only necessary user info for performance
            minimal_user = {
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role", "student"),
                "isCoordinator": is_coordinator
            }
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": minimal_user
            }
        except HTTPException:
            raise
        except Exception as e:
            import logging
            error_msg = str(e)
            logging.error(f"Error in user login: {error_msg}")
            if "DNS" in error_msg or "selection timeout" in error_msg:
                raise HTTPException(status_code=503, detail="Database connection issue. Please check your MongoDB Atlas cluster hostname in .env")
            raise HTTPException(status_code=500, detail="Login failed due to server error")

    @staticmethod
    async def google_login_user(token: str):
        """
        Accepts a Google OAuth2 access token (from useGoogleLogin implicit flow).
        Fetches user info from Google's UserInfo endpoint to verify and get profile.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {token}"}
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google access token")

            idinfo = resp.json()
            email = idinfo.get('email')
            if not email:
                raise HTTPException(status_code=401, detail="Could not retrieve email from Google")

            name = idinfo.get('name', email.split('@')[0])
            picture = idinfo.get('picture')

            db = get_database()
            user = await db["users"].find_one({"email": email})

            if not user:
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
            else:
                # Update picture if changed
                if picture and user.get("picture") != picture:
                    await db["users"].update_one(
                        {"_id": user["_id"]},
                        {"$set": {"picture": picture}}
                    )

            access_token = create_access_token(data={"sub": str(user["_id"]), "role": user.get("role", "student")})
            
            # Check if user is a coordinator (check both new and legacy storage)
            is_coordinator = await db["coordinators"].find_one({"userId": str(user["_id"])}) is not None
            if not is_coordinator:
                is_coordinator = await db["events"].find_one({"coordinators.userId": str(user["_id"])}) is not None
            
            # Return only necessary user info for performance
            minimal_user = {
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role", "student"),
                "isCoordinator": is_coordinator
            }

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": minimal_user
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Google authentication failed: {str(e)}")

    @staticmethod
    async def get_profile(user_id: str):
        db = get_database()
        try:
            user = await db["users"].find_one({"_id": ObjectId(user_id)})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        except HTTPException:
            raise
        except Exception as e:
            import logging
            logging.error(f"Error fetching profile: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        
        user["id"] = str(user.pop("_id"))
        
        # Check if user is a coordinator for any event
        is_coordinator = await db["coordinators"].find_one({"userId": user["id"]}) is not None
        user["isCoordinator"] = is_coordinator

        # Remove password hash from response
        if "password" in user:
            del user["password"]
        return user

    @staticmethod
    async def update_profile(user_id: str, update_data: dict):
        db = get_database()
        from datetime import datetime
        
        # Filter out none values
        update_fields = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_fields:
            return await AuthService.get_profile(user_id)

        # Handle nested preferences if present to avoid overwriting the entire object
        if "preferences" in update_fields and isinstance(update_fields["preferences"], dict):
            preferences = update_fields.pop("preferences")
            for key, value in preferences.items():
                update_fields[f"preferences.{key}"] = value
        
        update_fields["updatedAt"] = datetime.utcnow()
            
        result = await db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return await AuthService.get_profile(user_id)
