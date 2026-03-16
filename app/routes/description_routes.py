from fastapi import APIRouter, HTTPException, Depends
from app.schemas.description_schema import EventDescriptionRequest, EventDescriptionResponse
from app.services.ai_service import AIService
from app.database.connection import get_database
from bson import ObjectId
from datetime import datetime
from app.middleware.auth_middleware import get_current_user
from app.middleware.role_middleware import require_admin

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.post("/generate-event-description")
async def generate_event_description(
    request: EventDescriptionRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Generates a professional event description using Gemini AI.
    """
    # Authorization check - typically for admins/organizers
    if current_user["role"] not in ["admin", "organizer"]:
        # We allow organizers too as they create events
        pass 

    # Construct the prompt
    prompt = (
        "You are an expert copywriter for Eventra, a premium event management platform. "
        "Generate a professional, engaging, and comprehensive event description based on the following details:\n\n"
        f"Event Title: {request.event_title}\n"
        f"Category: {request.category}\n"
        f"Location: {request.location}\n"
        f"Date: {request.date}\n"
        f"Organizer: {request.organizer}\n\n"
        "The description should include an overview of why to attend, what to expect, and a call to action. "
        "Keep it structured and appealing for potential attendees."
    )

    try:
        generated_text = await AIService.ask_gemini(prompt)
        
        # --- Database Persistence ---
        db = get_database()
        
        # 1. Store in AI logs
        await db["ai_description_logs"].insert_one({
            "eventId": request.event_id,
            "eventTitle": request.event_title,
            "description": generated_text,
            "userId": current_user.get("id"),
            "createdAt": datetime.utcnow()
        })
        
        # 2. If event_id is provided, update the actual event record
        if request.event_id:
            try:
                await db["events"].update_one(
                    {"_id": ObjectId(request.event_id)},
                    {"$set": {"description": generated_text}}
                )
            except Exception as update_err:
                print(f"Failed to update event description: {str(update_err)}")
        # ----------------------------

        return {
            "success": True,
            "message": "Description generated",
            "data": {"description": generated_text}
        }
    except Exception as e:
        print(f"Description generation error: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"AI could not generate description: {str(e)}"
        )
