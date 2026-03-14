from fastapi import HTTPException
from app.database.connection import get_database
from app.models.registration_model import RegistrationModel
from bson import ObjectId
from datetime import datetime
import secrets
from app.services.email_service import EmailService

class RegistrationService:
    @staticmethod
    async def register_student(event_id: str, current_user: dict):
        db = get_database()
        user_id = current_user["id"]

        # Check for duplication
        existing = await db["registrations"].find_one({"userId": user_id, "eventId": event_id, "registrationStatus": "confirmed"})
        if existing:
            raise HTTPException(status_code=400, detail="Already registered for this event")
        
        # Check capacity
        event = await db["events"].find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        if event["status"] != "open":
            raise HTTPException(status_code=400, detail="Event registration is closed or completed")
        if event["registeredCount"] >= event["maxParticipants"]:
            raise HTTPException(status_code=400, detail="Event is already full")

        # Create registration
        ticket_number = f"TCK-{secrets.token_hex(4).upper()}"
        new_reg = RegistrationModel(userId=user_id, eventId=event_id, registrationStatus="confirmed", ticketNumber=ticket_number)
        res = await db["registrations"].insert_one(new_reg.model_dump(by_alias=True, exclude_none=True))
        
        # Update event count
        await db["events"].update_one({"_id": ObjectId(event_id)}, {"$inc": {"registeredCount": 1}})

        # Create notification
        await db["notifications"].insert_one({
            "userId": user_id,
            "message": f"Successfully registered for {event['title']}!",
            "type": "confirmation",
            "readStatus": False,
            "createdAt": datetime.utcnow()
        })

        # Send confirmation email
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if user and user.get("email"):
            # Avoid awaiting to not block response, or use a background task in a real app
            # For simplicity, we just fire and forget the synchronous send or make send_email async.
            EmailService.send_registration_confirmation(
                to_email=user["email"],
                student_name=user["name"],
                event_title=event["title"],
                ticket_number=ticket_number
            )

        created = await db["registrations"].find_one({"_id": res.inserted_id})
        created["id"] = str(created.pop("_id"))
        return created

    @staticmethod
    async def get_user_registrations(user_id: str):
        db = get_database()
        # Get all registrations (including cancelled so user can see history)
        regs = await db["registrations"].find({"userId": user_id}).sort("registrationDate", -1).to_list(1000)
        
        results = []
        for r in regs:
            # Fetch minimal event info
            try:
                event = await db["events"].find_one({"_id": ObjectId(r["eventId"])}, {"title": 1, "date": 1, "venue": 1, "imageUrl": 1})
            except:
                event = None
            r["id"] = str(r.pop("_id"))
            # Add 'registeredAt' and 'status' aliases for frontend compatibility
            r["registeredAt"] = r.get("registrationDate", datetime.utcnow()).isoformat() if isinstance(r.get("registrationDate"), datetime) else str(r.get("registrationDate", ""))
            r["status"] = r.get("registrationStatus", "confirmed")
            if event:
                r["event"] = {
                    "id": str(event["_id"]),
                    "title": event["title"],
                    "date": event["date"],
                    "venue": event["venue"],
                    "imageUrl": event.get("imageUrl", "")
                }
            results.append(r)
        return results

    @staticmethod
    async def check_in_student(reg_id: str):
        db = get_database()
        reg = await db["registrations"].find_one({"_id": ObjectId(reg_id)})
        if not reg:
            raise HTTPException(status_code=404, detail="Registration not found")
        if reg["attendanceStatus"] == "present":
            raise HTTPException(status_code=400, detail="Student already checked in")
            
        await db["registrations"].update_one(
            {"_id": ObjectId(reg_id)}, 
            {"$set": {"attendanceStatus": "present"}}
        )
        
        return {"message": "Student successfully checked in"}

    @staticmethod
    async def get_all_registrations():
        db = get_database()
        regs = await db["registrations"].find().sort("registrationDate", -1).to_list(1000)
        
        results = []
        for r in regs:
            # Fetch user and event info
            try:
                user = await db["users"].find_one({"_id": ObjectId(r["userId"])}, {"name": 1, "email": 1})
                event = await db["events"].find_one({"_id": ObjectId(r["eventId"])}, {"title": 1})
            except:
                user = None
                event = None
            
            r["id"] = str(r.pop("_id"))
            # Add frontend-compatible aliases
            r["status"] = r.get("registrationStatus", "confirmed")
            r["registeredAt"] = r.get("registrationDate", datetime.utcnow()).isoformat() if isinstance(r.get("registrationDate"), datetime) else str(r.get("registrationDate", ""))
            if user:
                r["studentName"] = user["name"]
                r["studentEmail"] = user["email"]
            if event:
                r["eventName"] = event["title"]
            
            results.append(r)
        return results

    @staticmethod
    async def cancel_registration(reg_id: str, current_user: dict):
        db = get_database()
        reg = await db["registrations"].find_one({"_id": ObjectId(reg_id)})
        if not reg:
            raise HTTPException(status_code=404, detail="Registration not found")
            
        if reg["userId"] != current_user["id"] and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to cancel this registration")

        if reg["registrationStatus"] == "cancelled":
            raise HTTPException(status_code=400, detail="Already cancelled")

        # Update status
        await db["registrations"].update_one({"_id": ObjectId(reg_id)}, {"$set": {"registrationStatus": "cancelled"}})
        
        # Decrease count
        await db["events"].update_one({"_id": ObjectId(reg["eventId"])}, {"$inc": {"registeredCount": -1}})

        return {"message": "Registration cancelled successfully"}
