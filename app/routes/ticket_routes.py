from fastapi import APIRouter, Depends, HTTPException
from app.database.connection import get_database
from app.middleware.auth_middleware import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

@router.get("/user/{user_id}")
async def get_user_tickets(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db = get_database()
    tickets_cursor = db["tickets"].find({"userId": user_id})
    tickets = await tickets_cursor.to_list(1000)
    
    results = []
    for t in tickets:
        # Fetch event minimal info
        try:
            event = await db["events"].find_one({"_id": ObjectId(t["eventId"])}, {"title": 1, "date": 1, "venue": 1})
        except:
            event = None
            
        t["id"] = str(t.pop("_id"))
        if event:
            t["event"] = {
                "id": str(event["_id"]),
                "title": event["title"],
                "date": event["date"],
                "venue": event["venue"]
            }
        results.append(t)
    
    return {"success": True, "message": "Tickets retrieved", "data": results}

@router.post("/scan")
async def scan_ticket(payload: dict, current_user: dict = Depends(get_current_user)):
    ticket_id = payload.get("ticketId")
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Ticket mapping required (ticketId)")
        
    db = get_database()
    ticket = await db["tickets"].find_one({"ticketId": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Invalid ticket")
        
    # Check if user is admin or coordinator
    if current_user["role"] != "admin":
        event = await db["events"].find_one({"_id": ObjectId(ticket["eventId"])})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
            
        is_coordinator = False
        for coord in event.get("coordinators", []):
            if coord.get("userId") == current_user["id"]:
                is_coordinator = True
                break
                
        if not is_coordinator and event.get("organizerId") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to scan tickets for this event")
            
    if ticket.get("checkedIn"):
        return {"success": False, "message": "Ticket already used", "data": {"ticketId": ticket_id, "checkedInAt": ticket.get("checkedInAt")}}
        
    from datetime import datetime
    await db["tickets"].update_one({"_id": ticket["_id"]}, {"$set": {"checkedIn": True, "checkedInAt": datetime.utcnow()}})
    
    # Also update attendanceStatus in registrations if possible
    # We can try to find the matching registration
    await db["registrations"].update_one(
        {"eventId": ticket["eventId"], "userId": ticket["userId"]},
        {"$set": {"attendanceStatus": "present"}}
    )
    
    return {"success": True, "message": "Attendance marked", "data": {"ticketId": ticket_id}}

@router.post("/checkin")
async def checkin_ticket(payload: dict, current_user: dict = Depends(get_current_user)):
    # This is an alias for /scan as per user request
    return await scan_ticket(payload, current_user)
