from fastapi import APIRouter, Depends, HTTPException
from app.services.registration_service import RegistrationService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

@router.get("/user/{user_id}")
async def get_user_tickets(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    regs = await RegistrationService.get_user_registrations(user_id)
    # Tickets are just confirmed registrations
    tickets = [r for r in regs if r.get("status") == "confirmed"]
    
    return {"success": True, "message": "Tickets retrieved", "data": tickets}
