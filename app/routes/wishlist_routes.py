from fastapi import APIRouter, Depends, Body
from app.services.wishlist_service import WishlistService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])

@router.post("/add")
async def add_to_wishlist(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    event_id = data.get("eventId")
    result = await WishlistService.add_to_wishlist(current_user["id"], event_id)
    return {"success": True, "message": "Added to wishlist", "data": result}

@router.delete("/remove")
async def remove_from_wishlist(eventId: str, current_user: dict = Depends(get_current_user)):
    result = await WishlistService.remove_from_wishlist(current_user["id"], eventId)
    return {"success": True, "message": "Removed from wishlist", "data": result}

@router.get("/user/{user_id}")
async def get_user_wishlist(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not authorized")
        
    result = await WishlistService.get_user_wishlist(user_id)
    return {"success": True, "message": "Wishlist retrieved", "data": result}
