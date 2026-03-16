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
        raise HTTPException(status_code=404, detail="Invalid ticket — not found in system")
        
    # Fetch event info (needed for auth check AND result card)
    event = None
    try:
        event = await db["events"].find_one({"_id": ObjectId(ticket["eventId"])})
    except:
        pass

    # Authorization: admin always allowed; others need to be coordinator/organizer
    if current_user["role"] != "admin":
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
            
        # 1. Check legacy coordinators array
        is_coordinator = any(
            coord.get("userId") == current_user["id"]
            for coord in event.get("coordinators", [])
        )
        
        # 2. Check new coordinators collection
        if not is_coordinator:
            new_coord = await db["coordinators"].find_one({
                "eventId": str(event["_id"]),
                "userId": current_user["id"]
            })
            if new_coord:
                is_coordinator = True

        if not is_coordinator and event.get("organizerId") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to scan tickets for this event")

    # Fetch participant info — userId may be stored as ObjectId string or plain string
    participant = None
    user_id_str = ticket.get("userId", "")
    # Try as MongoDB ObjectId first (most common case)
    try:
        participant = await db["users"].find_one(
            {"_id": ObjectId(user_id_str)}, {"name": 1, "email": 1}
        )
    except Exception:
        pass
    # Fallback: some auth providers store userId as a plain string
    if not participant:
        participant = await db["users"].find_one(
            {"$or": [{"id": user_id_str}, {"userId": user_id_str}]},
            {"name": 1, "email": 1}
        )

    # Build rich response payload for result card
    result_data = {
        "ticketId": ticket_id,
        "eventName": event.get("title", "Unknown Event") if event else "Unknown Event",
        "eventVenue": event.get("venue", "") if event else "",
        "userName": participant.get("name", "Unknown Participant") if participant else "Unknown Participant",
        "userEmail": participant.get("email", "") if participant else "",
    }

    # Already checked in?
    if ticket.get("checkedIn"):
        result_data["checkedInAt"] = str(ticket.get("checkedInAt", ""))
        return {
            "success": False,
            "message": "Ticket already checked in",
            "data": result_data
        }
        
    from datetime import datetime
    now = datetime.utcnow()
    await db["tickets"].update_one(
        {"_id": ticket["_id"]},
        {"$set": {"checkedIn": True, "checkedInAt": now}}
    )
    
    # Mirror update in registrations collection
    await db["registrations"].update_one(
        {"eventId": ticket["eventId"], "userId": ticket["userId"]},
        {"$set": {"attendanceStatus": "present"}}
    )
    
    result_data["checkedInAt"] = str(now)
    return {
        "success": True,
        "message": "Attendance marked successfully",
        "data": result_data
    }

@router.post("/checkin")
async def checkin_ticket(payload: dict, current_user: dict = Depends(get_current_user)):
    """Universal check-in endpoint — alias of /scan, auto-detects event from ticketId."""
    return await scan_ticket(payload, current_user)
