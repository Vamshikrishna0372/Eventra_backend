from typing import Optional, Any
from fastapi import HTTPException
from app.database.connection import get_database
from app.models.event_model import EventModel
from bson import ObjectId

class EventService:
    @staticmethod
    async def create_event(event_data: dict, current_user: dict):
        db = get_database()
        event_dict = event_data.copy()
        event_dict["organizerId"] = current_user["id"]
        
        # If this is featured, remove featured from others
        if event_dict.get("isFeatured"):
            await db["events"].update_many({"isFeatured": True}, {"$set": {"isFeatured": False}})
        
        new_event = EventModel(**event_dict)
        result = await db["events"].insert_one(new_event.model_dump(by_alias=True, exclude_none=True))
        
        # If featured, notify all users
        if event_dict.get("isFeatured"):
            from datetime import datetime
            users = await db["users"].find({}, {"_id": 1}).to_list(1000)
            notifications = []
            for u in users:
                notifications.append({
                    "userId": str(u["_id"]),
                    "title": "New Featured Event",
                    "message": f"✨ Check out our new featured event: {event_dict['title']}!",
                    "type": "update",
                    "readStatus": False,
                    "createdAt": datetime.utcnow()
                })
            if notifications:
                await db["notifications"].insert_many(notifications)
        
        created_event = await db["events"].find_one({"_id": result.inserted_id})
        created_event["id"] = str(created_event.pop("_id"))
        return created_event

    @staticmethod
    async def get_all_events(search: Optional[str] = None, category: Optional[str] = None, date: Optional[str] = None, venue: Optional[str] = None, isPaidEvent: Optional[bool] = None, page: int = 1, limit: int = 10):
        db = get_database()
        query: dict[str, Any] = {}
        if search:
            # Search across title, description, and category
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"category": {"$regex": search, "$options": "i"}},
                {"venue": {"$regex": search, "$options": "i"}},
            ]
        if category and category.lower() not in ["all", ""]:
            query["category"] = {"$regex": f"^{category}$", "$options": "i"}
        if date:
            query["date"] = date
        if venue and venue.lower() != "all":
            query["venue"] = {"$regex": venue, "$options": "i"}
        if isPaidEvent is not None:
            query["isPaidEvent"] = isPaidEvent
            
        skip = (page - 1) * limit

        projection = {
            "title": 1, "description": 1, "date": 1, "time": 1, "venue": 1,
            "category": 1, "categoryId": 1, "imageUrl": 1, "image": 1, "thumbnailUrl": 1,
            "maxParticipants": 1, "registeredCount": 1, "status": 1, "isPaidEvent": 1,
            "price": 1, "organizerName": 1, "createdAt": 1, "isFeatured": 1
        }

        cursor = db["events"].find(query, projection).sort("createdAt", -1).skip(skip).limit(limit)
        events = await cursor.to_list(length=limit)
        
        for event in events:
            event["id"] = str(event.pop("_id"))
        return events

    @staticmethod
    async def get_event(event_id: str):
        db = get_database()
        try:
            event = await db["events"].find_one({"_id": ObjectId(event_id)})
            if not event:
                raise HTTPException(status_code=404, detail="Event not found")
            event["id"] = str(event.pop("_id"))
            return event
        except:
            raise HTTPException(status_code=400, detail="Invalid event ID")

    @staticmethod
    async def get_featured_event():
        db = get_database()
        event = await db["events"].find_one({"isFeatured": True}, sort=[("createdAt", -1)])
        if not event:
            # Fallback to latest opened event if none featured
            event = await db["events"].find_one({"status": "open"}, sort=[("createdAt", -1)])
        
        if event:
            event["id"] = str(event.pop("_id"))
        return event

    @staticmethod
    async def get_trending_events():
        db = get_database()
        # Events with most registrations
        cursor = db["events"].find({"status": "open"}).sort("registeredCount", -1).limit(5)
        events = await cursor.to_list(5)
        for event in events:
            event["id"] = str(event.pop("_id"))
        return events

    @staticmethod
    async def get_event_participants(event_id: str):
        db = get_database()
        # Find all registrations for this event
        registrations = await db["registrations"].find({"eventId": event_id, "registrationStatus": "confirmed"}).to_list(1000)
        
        participants = []
        for reg in registrations:
            user = await db["users"].find_one({"_id": ObjectId(reg["userId"])})
            if user:
                participants.append({
                    "studentName": user["name"],
                    "studentEmail": user["email"],
                    "registrationDate": reg["registrationDate"]
                })
        return participants

    @staticmethod
    async def update_event(event_id: str, update_data: dict):
        db = get_database()
        update_dict = {k: v for k, v in update_data.items() if v is not None}
        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # If marking as featured, unmark others
        if update_dict.get("isFeatured"):
            await db["events"].update_many({"isFeatured": True}, {"$set": {"isFeatured": False}})

        try:
            result = await db["events"].update_one(
                {"_id": ObjectId(event_id)},
                {"$set": update_dict}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Event not found")
                
            # If significant field updated, notify wishlist users
            significant_fields = ["title", "date", "time", "venue", "status"]
            if any(field in update_dict for field in significant_fields):
                from datetime import datetime
                # Find users who have this event in their wishlist
                wishlist_users = await db["wishlists"].find({"eventId": event_id}, {"userId": 1}).to_list(1000)
                
                event_title = update_dict.get('title')
                if not event_title:
                    event = await db["events"].find_one({"_id": ObjectId(event_id)}, {"title": 1})
                    event_title = event.get('title', 'Unknown Event') if event else 'Unknown Event'

                notifications = []
                for entry in wishlist_users:
                    notifications.append({
                        "userId": entry["userId"],
                        "title": "Wishlist Event Updated",
                        "message": f"📢 An event you saved, '{event_title}', has been updated.",
                        "type": "update",
                        "readStatus": False,
                        "createdAt": datetime.utcnow()
                    })
                if notifications:
                    await db["notifications"].insert_many(notifications)
                
            return await EventService.get_event(event_id)
        except:
             raise HTTPException(status_code=400, detail="Invalid event ID")

    @staticmethod
    async def delete_event(event_id: str):
        db = get_database()
        try:
            result = await db["events"].delete_one({"_id": ObjectId(event_id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Event not found")
            return {"message": "Event deleted successfully"}
        except:
            raise HTTPException(status_code=400, detail="Invalid event ID")
