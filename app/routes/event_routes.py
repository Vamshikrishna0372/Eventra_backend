from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from app.database.connection import get_database
from app.schemas.event_schema import EventCreate, EventUpdate
from app.services.event_service import EventService
from app.middleware.auth_middleware import get_current_user
from app.middleware.role_middleware import require_admin

router = APIRouter(prefix="/api/events", tags=["Events"])

class AddCoordinatorReq(BaseModel):
    email: str

@router.get("")

async def get_events(search: Optional[str] = None, category: Optional[str] = None, date: Optional[str] = None, venue: Optional[str] = None, isPaidEvent: Optional[bool] = None, page: int = 1, limit: int = 10):
    events = await EventService.get_all_events(search, category, date, venue, isPaidEvent, page, limit)
    return {"success": True, "message": "Events retrieved", "data": events}

@router.get("/featured")
async def get_featured_event():
    event = await EventService.get_featured_event()
    return {"success": True, "message": "Featured event retrieved", "data": event}

@router.get("/trending")
async def get_trending_events():
    events = await EventService.get_trending_events()
    return {"success": True, "message": "Trending events retrieved", "data": events}

@router.get("/coordinated")
async def get_coordinated_events(current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    # 1. Get from new coordinators collection
    coord_cursor = db["coordinators"].find({"userId": current_user["id"]})
    user_coords = await coord_cursor.to_list(1000)
    event_ids = [ObjectId(c["eventId"]) for c in user_coords if "eventId" in c]
    
    # 2. ALSO check legacy list by fetching the user's email
    user = await db["users"].find_one({"_id": ObjectId(current_user["id"])})
    if user and user.get("email"):
        user_email = user.get("email").lower()
        legacy_cursor = db["events"].find({"coordinators.email": user_email}, {"_id": 1})
        legacy_events = await legacy_cursor.to_list(1000)
        for le in legacy_events:
            if le["_id"] not in event_ids:
                event_ids.append(le["_id"])
            
    if not event_ids:
        return {"success": True, "message": "Coordinated events retrieved", "data": []}
        
    cursor = db["events"].find({"_id": {"$in": event_ids}})
    events = await cursor.to_list(1000)
    for event in events:
        event["id"] = str(event.pop("_id"))
    return {"success": True, "message": "Coordinated events retrieved", "data": events}

@router.get("/{id}")
async def get_event(id: str):
    event = await EventService.get_event(id)
    return {"success": True, "message": "Event retrieved", "data": event}

@router.get("/{id}/participants")
async def get_event_participants(id: str, current_user: dict = Depends(get_current_user)):
    # Check if admin
    if current_user.get("role") == "admin":
        participants = await EventService.get_event_participants(id)
        return {"success": True, "message": "Participants retrieved", "data": participants}
    
    db = get_database()
    
    # Check new coordinators collection using userId
    coord = await db["coordinators"].find_one({
        "eventId": id,
        "userId": current_user["id"]
    })
    
    if not coord:
        # Also check legacy list by fetching the user's email first
        user = await db["users"].find_one({"_id": ObjectId(current_user["id"])})
        user_email = user.get("email", "").lower() if user else None
        
        legacy_coord = await db["events"].find_one({
            "_id": ObjectId(id),
            "coordinators.email": user_email
        })
        
        if not legacy_coord:
            raise HTTPException(status_code=403, detail="Not authorized to view participants for this event")
        
    participants = await EventService.get_event_participants(id)
    return {"success": True, "message": "Participants retrieved", "data": participants}

@router.post("", dependencies=[Depends(require_admin)])
async def create_event(event_data: EventCreate, current_user: dict = Depends(get_current_user)):
    event = await EventService.create_event(event_data.model_dump(), current_user)
    return {"success": True, "message": "Event created successfully", "data": event}

@router.put("/{id}", dependencies=[Depends(require_admin)])
async def update_event(id: str, event_data: EventUpdate):
    event = await EventService.update_event(id, event_data.model_dump())
    return {"success": True, "message": "Event updated successfully", "data": event}

@router.delete("/{id}", dependencies=[Depends(require_admin)])
async def delete_event(id: str):
    result = await EventService.delete_event(id)
    return {"success": True, "message": "Event deleted successfully", "data": result}
    
@router.post("/{id}/coordinators", dependencies=[Depends(require_admin)])
async def add_coordinator(id: str, coord_data: AddCoordinatorReq):
    from app.services.coordinator_service import CoordinatorService
    # Add coordinator service expects data dict with eventId
    result = await CoordinatorService.add_coordinator({
        "email": coord_data.email,
        "eventId": id
    })
    return {"success": True, "message": "Coordinator added successfully", "data": result}

@router.get("/{id}/coordinators")
async def get_event_coordinators(id: str, current_user: dict = Depends(get_current_user)):
    from app.services.coordinator_service import CoordinatorService
    from datetime import datetime
    
    event = await EventService.get_event(id)
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user is admin or coordinator
    is_privileged = current_user.get("role") == "admin"
    if not is_privileged:
        from app.database.connection import get_database
        db = get_database()
        coord = await db["coordinators"].find_one({"userId": current_user["id"]})
        if coord:
            is_privileged = True
            
    if not is_privileged:
        # Visibility logic: Hide if closed, completed, or expired
        event_status = event.get("status", "open").lower()
        
        # Parse event date/time to check if completed/expired
        try:
            event_date_str = event.get("date", "")
            if "T" in event_date_str:
                event_end_time = datetime.fromisoformat(event_date_str)
            else:
                event_end_time = datetime.fromisoformat(f"{event_date_str}T22:00:00")
            
            is_expired = datetime.utcnow() > event_end_time
            is_hidden_status = event_status in ["closed", "completed", "expired"]
            
            if is_expired or is_hidden_status:
                return {"success": True, "data": [], "hidden": True}
        except Exception:
            if event_status in ["closed", "completed", "expired"]:
                return {"success": True, "data": [], "hidden": True}
    
    result = await CoordinatorService.get_coordinators_by_event(id)
    return {"success": True, "data": result}
