from fastapi import APIRouter, Depends, HTTPException
from app.services.coordinator_service import CoordinatorService
from app.middleware.auth_middleware import get_current_user
from app.middleware.role_middleware import require_admin
from typing import List

router = APIRouter(prefix="/api/coordinators", tags=["Coordinators"])

@router.delete("/{id}")
async def delete_coordinator(id: str, current_user: dict = Depends(require_admin)):
    result = await CoordinatorService.delete_coordinator(id)
    return {"success": True, "message": result["message"]}
