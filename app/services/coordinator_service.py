from fastapi import HTTPException
from app.database.connection import get_database
from app.models.coordinator_model import CoordinatorModel
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger("eventra.coordinators")

class CoordinatorService:
    @staticmethod
    async def add_coordinator(data: dict):
        db = get_database()
        event_id = str(data.get("eventId"))
        email = data.get("email", "").lower().strip()
        
        if not event_id or not email:
            raise HTTPException(status_code=400, detail="Event ID and Email are required")
        
        # Verify event exists
        event = await db["events"].find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Verify user exists
        user = await db["users"].find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found with this email")
        
        # Role Protection: Prevent mixing Admin and Coordinator roles
        if user.get("role") == "admin":
            raise HTTPException(status_code=400, detail="Administrative accounts cannot be assigned as event coordinators")
        
        # Check if already a coordinator for this event in separate collection
        existing = await db["coordinators"].find_one({"eventId": event_id, "email": email})
        if existing:
            raise HTTPException(status_code=400, detail="User is already a coordinator for this event")
        
        # ALSO check the legacy coordinators array in the event document
        event_coords = event.get("coordinators", [])
        if any(c.get("email", "").lower() == email for c in event_coords):
             raise HTTPException(status_code=400, detail="User is already a coordinator for this event (legacy list)")
        
        coordinator_data = {
            "name": user["name"],
            "email": email,
            "userId": str(user["_id"]),
            "phone": user.get("phoneNumber") or user.get("phone") or "N/A",
            "eventId": event_id,
            "eventTitle": event["title"],
            "createdAt": datetime.utcnow()
        }
        
        new_coord = CoordinatorModel(**coordinator_data)
        result = await db["coordinators"].insert_one(new_coord.model_dump(by_alias=True, exclude_none=True))
        
        # Also update the user to mark them as a coordinator if not already
        if not user.get("isCoordinator"):
            await db["users"].update_one({"_id": user["_id"]}, {"$set": {"isCoordinator": True}})
        
        # Return the created coordinator
        created = await db["coordinators"].find_one({"_id": result.inserted_id})
        created["id"] = str(created.pop("_id"))
        return created

    @staticmethod
    async def delete_coordinator(coordinator_id: str):
        db = get_database()
        try:
            # Handle legacy IDs (e.g., "legacy-email@example.com")
            if coordinator_id.startswith("legacy-"):
                email = coordinator_id.replace("legacy-", "")
                await db["events"].update_many(
                    {"coordinators.email": email},
                    {"$pull": {"coordinators": {"email": email}}}
                )
                return {"success": True, "message": "Legacy coordinator removed successfully"}

            # Get the coordinator first to check if we should clear user.isCoordinator
            coord = await db["coordinators"].find_one({"_id": ObjectId(coordinator_id)})
            if not coord:
                # If not in separate collection, maybe it's a userId from the legacy list?
                # Check if it matches a userId in any event
                event = await db["events"].find_one({"coordinators.userId": coordinator_id})
                if event:
                    await db["events"].update_one(
                        {"_id": event["_id"]},
                        {"$pull": {"coordinators": {"userId": coordinator_id}}}
                    )
                    return {"success": True, "message": "Legacy coordinator removed via userId"}
                raise HTTPException(status_code=404, detail="Coordinator record not found")
            
            email = coord["email"]
            event_id = coord.get("eventId")
            
            # Delete the coordinator record
            result = await db["coordinators"].delete_one({"_id": ObjectId(coordinator_id)})
            
            # ALSO remove from legacy array if it exists
            if event_id:
                try:
                    await db["events"].update_one(
                        {"_id": ObjectId(event_id)},
                        {"$pull": {"coordinators": {"email": email}}}
                    )
                except:
                    pass
            
            # Check if user has other coordinated events. If not, remove isCoordinator flag
            other_coords = await db["coordinators"].count_documents({"email": email})
            if other_coords == 0:
                await db["users"].update_one({"email": email}, {"$set": {"isCoordinator": False}})
                
            return {"success": True, "message": "Coordinator removed successfully"}
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            logger.error(f"Error deleting coordinator: {e}")
            raise HTTPException(status_code=400, detail="Invalid coordinator ID or operation failed")

    @staticmethod
    async def get_coordinators_by_event(event_id: str):
        db = get_database()
        try:
            # 1. Get from separate collection
            cursor = db["coordinators"].find({"eventId": event_id})
            coords = await cursor.to_list(length=100)
            seen_emails = set()
            
            for c in coords:
                c["id"] = str(c.pop("_id"))
                seen_emails.add(c["email"].lower())
                if isinstance(c.get("createdAt"), datetime):
                    c["createdAt"] = c["createdAt"].isoformat()
            
            # 2. ALSO check legacy array in event document
            event = await db["events"].find_one({"_id": ObjectId(event_id)}, {"coordinators": 1})
            if event and "coordinators" in event:
                for xc in event["coordinators"]:
                    email = xc.get("email", "").lower()
                    if email and email not in seen_emails:
                        # Add legacy coordinator to the list
                        # Note: They might not have a separate ID, so we might need a workaround for the UI
                        # We'll use a virtual ID for now if it's missing
                        seen_emails.add(email)
                        coords.append({
                            "id": xc.get("userId") or f"legacy-{email}",
                            "name": xc.get("name", "Unknown"),
                            "email": xc.get("email"),
                            "phone": xc.get("phoneNumber") or xc.get("phone") or "N/A",
                            "eventId": event_id,
                            "isLegacy": True
                        })
                        
            return coords
        except Exception as e:
            logger.error(f"Error fetching coordinators: {e}")
            return []
