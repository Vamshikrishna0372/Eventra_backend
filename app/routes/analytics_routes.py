from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.services.analytics_service import AnalyticsService
from app.middleware.role_middleware import require_admin
from app.database.connection import get_database
from app.schemas.analytics_schema import AnalyticsInsightsRequest, AnalyticsInsightsResponse
from app.services.ai_service import AIService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()

@router.get("/api/analytics/overview", tags=["Analytics"], dependencies=[Depends(require_admin)])
async def get_analytics_overview():
    data = await AnalyticsService.get_overview()
    return {"success": True, "message": "Analytics retrieved", "data": data}

@router.get("/api/analytics/leaderboard", tags=["Analytics"])
async def get_leaderboard():
    data = await AnalyticsService.get_leaderboard()
    return {"success": True, "message": "Leaderboard retrieved", "data": data}
@router.post("/api/event-insights", response_model=AnalyticsInsightsResponse, tags=["AI Services"])
async def generate_event_insights(
    request: AnalyticsInsightsRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Analyzes event statistics and generates actionable insights and recommendations using Gemini AI.
    """
    stats = request.event_statistics
    
    # Construct the instruction prompt for data analysis
    prompt = (
        "You are a senior data analyst for the Eventra event management platform. "
        "Your task is to analyze the following event statistics and provide deep insights and actionable recommendations for improvement.\n\n"
        f"Attendance: {stats.attendance}\n"
        f"Average Rating: {stats.average_rating}/5\n"
        f"Feedback Summary: {stats.feedback_summary}\n\n"
        "Requirements:\n"
        "1. Analyze what the data says about the event's success.\n"
        "2. Identify specific areas for improvement based on the feedback.\n"
        "3. Provide 3-5 clear, strategic recommendations for the next event.\n"
        "4. Keep the tone professional, analytical, and encouraging."
    )

    try:
        insights_text = await AIService.ask_gemini(prompt)
        result = AnalyticsInsightsResponse(insights=insights_text)

        # --- Database Persistence ---
        db = get_database()
        storage_data = result.model_dump()
        storage_data.update({
            "eventId": stats.event_id,
            "stats": stats.model_dump(),
            "userId": current_user.get("id"),
            "createdAt": datetime.utcnow()
        })
        await db["ai_analytics_insights"].insert_one(storage_data)
        # ----------------------------

        return result
    except Exception as e:
        print(f"Analytics insight error: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"AI could not generate analytics insights: {str(e)}"
        )
