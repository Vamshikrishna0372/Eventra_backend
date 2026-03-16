import json
import re
from datetime import datetime
from app.database.connection import get_database
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.feedback_analysis_schema import FeedbackRequest, FeedbackAnalysisResponse
from app.services.ai_service import AIService
from app.middleware.auth_middleware import get_current_user
from app.middleware.role_middleware import require_admin

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.post("/analyze-feedback", response_model=FeedbackAnalysisResponse)
async def analyze_feedback(
    request: FeedbackRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Analyzes event feedback and extracts structured insights (positives, negatives, suggestions) using Gemini AI.
    """
    if not request.feedback.strip():
        raise HTTPException(status_code=400, detail="Feedback text cannot be empty")

    # Construct a prompt that asks for JSON specifically
    prompt = (
        "You are an AI analyst for Eventra, an event management platform. "
        "Analyze the following event feedback and extract key insights in a strict JSON format.\n\n"
        f"Feedback: '{request.feedback}'\n\n"
        "Return ONLY a JSON object with exactly these keys:\n"
        "- positive_points (a list of strings)\n"
        "- negative_points (a list of strings)\n"
        "- suggestions (a list of strings)\n\n"
        "Do not include any other text, markdown formatting, or explanations."
    )

    try:
        # Call Gemini
        raw_response = await AIService.ask_gemini(prompt)
        
        # Extract JSON from response (sometimes Gemini wraps it in ```json ... ```)
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            analysis_data = json.loads(json_str)
            
            # Ensure lists exist if Gemini misses keys
            result = FeedbackAnalysisResponse(
                positive_points=analysis_data.get("positive_points", []),
                negative_points=analysis_data.get("negative_points", []),
                suggestions=analysis_data.get("suggestions", [])
            )

            # --- Database Persistence ---
            db = get_database()
            storage_data = result.model_dump()
            storage_data.update({
                "eventId": request.event_id,
                "rawFeedback": request.feedback,
                "userId": current_user.get("id"),
                "createdAt": datetime.utcnow()
            })
            await db["ai_feedback_analysis"].insert_one(storage_data)
            # ----------------------------

            return result
        else:
            # Fallback if no JSON found
            raise ValueError("No valid JSON found in AI response")

    except Exception as e:
        print(f"Feedback analysis error: {str(e)}")
        # If it fails to parse JSON, we return a 502 with details
        raise HTTPException(
            status_code=502, 
            detail=f"AI could not analyze feedback into a structured format: {str(e)}"
        )
