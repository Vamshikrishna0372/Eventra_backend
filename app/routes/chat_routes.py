from fastapi import APIRouter, HTTPException, Depends
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from datetime import datetime
from app.database.connection import get_database
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/chat", tags=["AI Chatbot"])

@router.post("")
async def chat_with_ai(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    AI Chatbot endpoint that interacts with Gemini.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Optional: Fetch some context about events to make the AI smarter
    try:
        db = get_database()
        events_cursor = db["events"].find({"status": "open"}).limit(5)
        events = await events_cursor.to_list(length=5)
        
        event_context = ""
        if events:
            event_context = "\nHere are some upcoming events currently on the platform:\n"
            for e in events:
                event_context += f"- {e.get('title')} on {e.get('date')} at {e.get('venue')}\n"
    except Exception:
        event_context = ""

    # Construct the instruction prompt
    system_instruction = (
        "You are an AI assistant for Eventra, a premium event management platform. "
        "Your goal is to help users with information about events, schedules, venues, and registrations. "
        "Be professional, helpful, and concise in your responses. "
        "If you don't know specific details about an event not listed in your context, "
        "kindly ask the user to check the 'Explore Events' tab."
    )
    
    full_prompt = (
        f"{system_instruction}\n"
        f"{event_context}\n"
        f"User question: {request.message}"
    )

    try:
        reply = await AIService.ask_gemini(full_prompt)
        
        # --- Database Persistence ---
        db = get_database()
        await db["ai_chat_history"].insert_one({
            "userId": current_user.get("id"),
            "userMessage": request.message,
            "aiReply": reply,
            "createdAt": datetime.utcnow()
        })
        # ----------------------------

        return {
            "success": True,
            "message": "AI reply generated",
            "data": {"reply": reply}
        }
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"Failed to get a response from AI assistant: {str(e)}"
        )
