from fastapi import APIRouter, Depends, HTTPException
from app.database.connection import get_database
from app.schemas.notification_schema import NotificationCreate
from app.models.notification_model import NotificationModel
from app.middleware.auth_middleware import get_current_user
from app.middleware.role_middleware import require_admin
from bson import ObjectId

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/user/{user_id}")
async def get_notifications(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db = get_database()
    notifications = await db["notifications"].find({"userId": user_id}).sort("createdAt", -1).to_list(100)
    for n in notifications:
        n["id"] = str(n.pop("_id"))
    return {"success": True, "message": "Notifications retrieved", "data": notifications}

@router.post("/create", dependencies=[Depends(require_admin)])
async def create_notification(notif_data: NotificationCreate):
    db = get_database()
    new_notif = NotificationModel(**notif_data.model_dump())
    res = await db["notifications"].insert_one(new_notif.model_dump(by_alias=True, exclude_none=True))
    created = await db["notifications"].find_one({"_id": res.inserted_id})
    created["id"] = str(created.pop("_id"))
    return {"success": True, "message": "Notification created", "data": created}

@router.put("/read/{id}")
async def mark_read(id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    notif = await db["notifications"].find_one({"_id": ObjectId(id)})
    if not notif:
        raise HTTPException(status_code=404, detail="Not found")
    if notif["userId"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db["notifications"].update_one({"_id": ObjectId(id)}, {"$set": {"readStatus": True}})
    return {"success": True, "message": "Marked as read", "data": None}
@router.post("/broadcast", dependencies=[Depends(require_admin)])
async def broadcast_notification(data: dict):
    # data expects {"message": str, "type": str, "title": str}
    db = get_database()
    users = await db["users"].find({}, {"_id": 1}).to_list(10000)
    import datetime
    notifications = []
    for u in users:
        notifications.append({
            "userId": str(u["_id"]),
            "title": data.get("title", "Announcement"),
            "message": data["message"],
            "type": data.get("type", "update"),
            "readStatus": False,
            "createdAt": datetime.datetime.utcnow()
        })
    if notifications:
        await db["notifications"].insert_many(notifications)
    return {"success": True, "message": f"Broadcasted to {len(notifications)} users"}

@router.delete("/{id}")
async def delete_notification(id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    notif = await db["notifications"].find_one({"_id": ObjectId(id)})
    if not notif:
        raise HTTPException(status_code=404, detail="Not found")
    if notif["userId"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db["notifications"].delete_one({"_id": ObjectId(id)})
    return {"success": True, "message": "Notification deleted"}
