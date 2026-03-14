from app.database.connection import get_database
from app.models.wishlist_model import WishlistModel
from bson import ObjectId
from datetime import datetime

db = get_database()

class WishlistService:
    @staticmethod
    async def add_to_wishlist(user_id: str, event_id: str):
        # Check if already in wishlist
        existing = await db["wishlists"].find_one({"userId": user_id, "eventId": event_id})
        if existing:
            return {"message": "Already in wishlist"}
        
        wish_item = WishlistModel(userId=user_id, eventId=event_id)
        result = await db["wishlists"].insert_one(wish_item.model_dump(by_alias=True, exclude_none=True))
        return {"id": str(result.inserted_id)}

    @staticmethod
    async def remove_from_wishlist(user_id: str, event_id: str):
        result = await db["wishlists"].delete_one({"userId": user_id, "eventId": event_id})
        return {"deleted": result.deleted_count > 0}

    @staticmethod
    async def get_user_wishlist(user_id: str):
        wishes = await db["wishlists"].find({"userId": user_id}).to_list(length=100)
        
        # Join with event details
        event_ids = [ObjectId(w["eventId"]) for w in wishes]
        events = await db["events"].find({"_id": {"$in": event_ids}}).to_list(length=100)
        
        # Convert IDs to string for JSON serialization
        results = []
        for event in events:
            event["_id"] = str(event["_id"])
            results.append(event)
            
        return results
