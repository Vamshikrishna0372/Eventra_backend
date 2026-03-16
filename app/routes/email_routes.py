from fastapi import APIRouter, HTTPException, Depends
from app.schemas.email_schema import EmailRequest, EmailResponse
from app.services.ai_service import AIService
from datetime import datetime
from app.database.connection import get_database
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.post("/generate-email", response_model=EmailResponse)
async def generate_email_content(
    request: EmailRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Generates professional email content (templates) using Gemini AI.
    Compatible with invitations, reminders, and general notifications.
    """
    # Validation: basic role check can be added if needed, but usually any organizer can use this
    
    # Construct the instruction prompt
    prompt = (
        "You are a professional communications assistant for Eventra, a premium event management platform.\n"
        f"Generate a professional {request.email_type} email for the following event details:\n\n"
        f"Event Title: {request.event_title}\n"
        f"Event Date: {request.event_date}\n"
        f"Event Location: {request.event_location}\n"
        f"Organizer: {request.organizer}\n\n"
        "Requirements:\n"
        "1. Include a catchy and professional 'Subject:' line at the start.\n"
        "2. Make the body friendly, clear, and informative.\n"
        "3. Include space for placeholders like [Recipient Name] if appropriate.\n"
        "4. Keep the tone suitable for the Eventra brand (modern and reliable).\n"
        "5. Conclude with a professional sign-off representing the organizer."
    )

    try:
        email_text = await AIService.ask_gemini(prompt)
        
        # --- Database Persistence ---
        db = get_database()
        await db["ai_email_logs"].insert_one({
            "userId": current_user.get("id"),
            "emailType": request.email_type,
            "eventTitle": request.event_title,
            "content": email_text,
            "createdAt": datetime.utcnow()
        })
        # ----------------------------

        return EmailResponse(email_content=email_text)
    except Exception as e:
        print(f"Email generation error: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"AI could not generate email content: {str(e)}"
        )
