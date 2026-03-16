from fastapi import APIRouter, Depends
from app.schemas.event_schema import EventCreate, EventUpdate
from app.services.event_service import EventService
from app.middleware.auth_middleware import get_current_user
from app.middleware.role_middleware import require_admin

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("")
async def get_events(search: str = None, category: str = None, date: str = None, venue: str = None, isPaidEvent: bool = None, page: int = 1, limit: int = 10):
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
    from app.database.connection import get_database
    db = get_database()
    cursor = db["events"].find({"coordinators.userId": current_user["id"]})
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
    
    # Check if coordinator of THIS specific event
    from app.database.connection import get_database
    from bson import ObjectId
    from fastapi import HTTPException
    db = get_database()
    event = await db["events"].find_one({
        "_id": ObjectId(id),
        "coordinators.userId": current_user["id"]
    })
    
    if not event:
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
    
from pydantic import BaseModel
class AddCoordinatorReq(BaseModel):
    email: str

@router.post("/{id}/add-coordinator", dependencies=[Depends(require_admin)])
async def add_coordinator(id: str, coord_data: AddCoordinatorReq):
    result = await EventService.add_coordinator(id, coord_data.email)
    return {"success": True, "message": "Coordinator added successfully", "data": result}

@router.delete("/{id}/remove-coordinator/{user_id}", dependencies=[Depends(require_admin)])
async def remove_coordinator(id: str, user_id: str):
    result = await EventService.remove_coordinator(id, user_id)
    return {"success": True, "message": "Coordinator removed successfully", "data": result}
