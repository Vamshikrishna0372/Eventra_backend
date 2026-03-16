from datetime import datetime
from app.database.connection import get_database
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.recommendation_schema import RecommendationRequest, RecommendationResponse
from app.services.ai_service import AIService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.post("/recommend-events")
async def recommend_events(
    request: RecommendationRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Analyzes user interests against available events and generates personalized recommendations using Gemini AI.
    """
    if not request.user_interests:
        raise HTTPException(status_code=400, detail="User interests cannot be empty")
    
    if not request.available_events:
        raise HTTPException(status_code=400, detail="Available events list cannot be empty")

    # Construct the event list for the prompt
    events_text = ""
    for idx, event in enumerate(request.available_events, 1):
        events_text += f"{idx}. {event.title} – {event.category} – {event.location}\n"

    # Construct the prompt
    interests_str = ", ".join(request.user_interests)
    prompt = (
        "You are an intelligent AI recommendation assistant for the Eventra platform. "
        "Your goal is to analyze a user's interests and suggest the most relevant events from the provided list.\n\n"
        f"User interests: {interests_str}\n\n"
        "Available events:\n"
        f"{events_text}\n"
        "Task:\n"
        "1. Identify the 2-3 most suitable events for this user.\n"
        "2. Briefly explain why each suggested event matches their specific interests.\n"
        "3. Keep the tone friendly, professional, and encouraging. "
        "If none of the events match perfectly, suggest the closest ones or mention that they might enjoy exploring new categories."
    )

    try:
        recommendations_text = await AIService.ask_gemini(prompt)
        result = RecommendationResponse(recommendations=recommendations_text)

        # --- Database Persistence ---
        db = get_database()
        storage_data = result.model_dump()
        storage_data.update({
            "userInterests": request.user_interests,
            "userId": current_user.get("id"),
            "createdAt": datetime.utcnow()
        })
        await db["ai_recommendations"].insert_one(storage_data)
        # ----------------------------

        return {
            "success": True,
            "message": "Recommendations generated",
            "data": {"recommendations": recommendations_text}
        }
    except Exception as e:
        print(f"Recommendation error: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"AI could not generate recommendations: {str(e)}"
        )
