from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.schemas.registration_schema import RegistrationCreate
from app.services.registration_service import RegistrationService
from app.middleware.auth_middleware import get_current_user
from app.middleware.role_middleware import require_admin
from app.database.connection import get_database

router = APIRouter(prefix="/api/registrations", tags=["Registrations"])

@router.get("", dependencies=[Depends(require_admin)])
async def get_all_registrations():
    regs = await RegistrationService.get_all_registrations()
    return {"success": True, "message": "All registrations retrieved", "data": regs}

@router.post("")
async def register_student(reg_data: RegistrationCreate, current_user: dict = Depends(get_current_user)):
    reg = await RegistrationService.register_student(reg_data.eventId, current_user)
    return {"success": True, "message": "Registered successfully", "data": reg}

@router.get("/user/{user_id}")
async def get_user_registrations(user_id: str, current_user: dict = Depends(get_current_user)):
    # Student can only view their own OR admin can view any
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    regs = await RegistrationService.get_user_registrations(user_id)
    return {"success": True, "message": "Registrations retrieved", "data": regs}

@router.get("/event/{event_id}")
async def get_event_registrations(event_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    event = await db["events"].find_one({"_id": ObjectId(event_id)})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Allow admin, organizer, or coordinator
    is_authorized = (
        current_user["role"] == "admin"
        or str(event.get("organizerId")) == current_user["id"]
    )
    if not is_authorized:
        for coord in event.get("coordinators", []):
            if coord.get("userId") == current_user["id"]:
                is_authorized = True
                break

    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized to view attendees for this event")

    regs = await RegistrationService.get_event_registrations(event_id)
    return {"success": True, "message": "Event registrations retrieved", "data": regs}

@router.put("/{id}/checkin")
async def check_in_student(id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    reg = await db["registrations"].find_one({"_id": ObjectId(id)})
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Allow admin, organizer, or coordinator of the event
    if current_user["role"] != "admin":
        event = await db["events"].find_one({"_id": ObjectId(reg["eventId"])})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        is_authorized = str(event.get("organizerId")) == current_user["id"]
        if not is_authorized:
            for coord in event.get("coordinators", []):
                if coord.get("userId") == current_user["id"]:
                    is_authorized = True
                    break

        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized to check in students for this event")

    result = await RegistrationService.check_in_student(id)
    return {"success": True, "message": result["message"], "data": result}

@router.delete("/{id}")
async def cancel_registration(id: str, current_user: dict = Depends(get_current_user)):
    result = await RegistrationService.cancel_registration(id, current_user)
    return {"success": True, "message": "Registration cancelled successfully", "data": result}
