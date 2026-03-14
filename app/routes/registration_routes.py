from fastapi import APIRouter, Depends
from app.schemas.registration_schema import RegistrationCreate
from app.services.registration_service import RegistrationService
from app.middleware.auth_middleware import get_current_user

from app.middleware.role_middleware import require_admin

router = APIRouter(prefix="/api/registrations", tags=["Registrations"])

@router.get("/", dependencies=[Depends(require_admin)])
async def get_all_registrations():
    regs = await RegistrationService.get_all_registrations()
    return {"success": True, "message": "All registrations retrieved", "data": regs}

@router.post("/")
async def register_student(reg_data: RegistrationCreate, current_user: dict = Depends(get_current_user)):
    reg = await RegistrationService.register_student(reg_data.eventId, current_user)
    return {"success": True, "message": "Registered successfully", "data": reg}

@router.get("/user/{user_id}")
async def get_user_registrations(user_id: str, current_user: dict = Depends(get_current_user)):
    # Student can only view their own OR admin can view any
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not authorized")
        
    regs = await RegistrationService.get_user_registrations(user_id)
    return {"success": True, "message": "Registrations retrieved", "data": regs}

@router.put("/{id}/checkin", dependencies=[Depends(require_admin)])
async def check_in_student(id: str):
    result = await RegistrationService.check_in_student(id)
    return {"success": True, "message": result["message"], "data": result}

@router.delete("/{id}")
async def cancel_registration(id: str, current_user: dict = Depends(get_current_user)):
    result = await RegistrationService.cancel_registration(id, current_user)
    return {"success": True, "message": "Registration cancelled successfully", "data": result}
