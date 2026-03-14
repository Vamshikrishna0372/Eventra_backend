from fastapi import APIRouter, Depends
from app.schemas.event_schema import EventCreate, EventUpdate
from app.services.event_service import EventService
from app.middleware.auth_middleware import get_current_user
from app.middleware.role_middleware import require_admin

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("/")
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

@router.get("/{id}")
async def get_event(id: str):
    event = await EventService.get_event(id)
    return {"success": True, "message": "Event retrieved", "data": event}

@router.get("/{id}/participants", dependencies=[Depends(require_admin)])
async def get_event_participants(id: str):
    participants = await EventService.get_event_participants(id)
    return {"success": True, "message": "Participants retrieved", "data": participants}

@router.post("/", dependencies=[Depends(require_admin)])
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
