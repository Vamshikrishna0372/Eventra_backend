from fastapi import APIRouter, HTTPException, Depends
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from datetime import datetime
from app.database.connection import get_database
from app.middleware.auth_middleware import get_current_user
import logging

logger = logging.getLogger("eventra.chat")

router = APIRouter(prefix="/api/chat", tags=["AI Chatbot"])


@router.post("")
async def chat_with_ai(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    AI Chatbot endpoint — sends user messages to Gemini and returns a clean response.
    Never returns 502 to the frontend; returns a safe fallback instead.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # ── Fetch lightweight event context (max 5 open events) ──────────────────
    event_context = ""
    try:
        db = get_database()
        events_cursor = db["events"].find({"status": "open"}).limit(5)
        events = await events_cursor.to_list(length=5)
        if events:
            event_context = "\nCurrently available events:\n" + "".join(
                f"- {e.get('title', 'Untitled')} | {e.get('date', '')} | {e.get('venue', '')}\n"
                for e in events
            )
    except Exception as ctx_err:
        logger.warning(f"[Chat] Could not fetch event context: {ctx_err}")
        event_context = ""

    # ── Build concise prompt ──────────────────────────────────────────────────
    system_instruction = (
        "You are the Eventra AI assistant — a friendly, professional helper for a "
        "campus event management platform. Help users with event details, schedules, "
        "registrations, and general queries. Keep answers concise and clear. "
        "If specific event details aren't available in context, suggest users visit "
        "the 'Explore Events' page."
    )

    full_prompt = (
        f"{system_instruction}"
        f"{event_context}\n"
        f"User: {request.message.strip()}"
    )

    # ── Call Gemini (never raises — returns fallback text on error) ───────────
    logger.info(f"[Chat] Processing message from user {current_user.get('id')}: {request.message[:80]}")
    reply = await AIService.ask_gemini(full_prompt)
    logger.info(f"[Chat] Reply generated ({len(reply)} chars).")

    # ── Persist to MongoDB (non-blocking, best-effort) ────────────────────────
    try:
        db = get_database()
        await db["ai_chat_history"].insert_one({
            "userId": current_user.get("id"),
            "userMessage": request.message,
            "aiReply": reply,
            "createdAt": datetime.utcnow()
        })
    except Exception as db_err:
        logger.warning(f"[Chat] Failed to save chat history: {db_err}")

    return {
        "success": True,
        "message": "AI reply generated",
        "data": {"reply": reply}
    }
