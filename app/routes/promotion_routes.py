import json
import re
from datetime import datetime
from app.database.connection import get_database
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.promotion_schema import PromotionRequest, PromotionResponse
from app.services.ai_service import AIService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.post("/generate-promotion", response_model=PromotionResponse)
async def generate_promotion(
    request: PromotionRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Generates engaging social media promotional content (captions, posts, and hashtags) using Gemini AI.
    """
    
    # Construct the instruction prompt for marketing content
    prompt = (
        "You are a creative marketing assistant for the Eventra event management platform. "
        "Your task is to generate high-conversion promotional content for the following event details:\n\n"
        f"Event Title: {request.event_title}\n"
        f"Category: {request.category}\n"
        f"Location: {request.location}\n"
        f"Date: {request.date}\n"
        f"Target Audience: {request.target_audience}\n\n"
        "Please provide the content strictly in JSON format with exactly these keys:\n"
        "- caption (a short, punchy social media caption with emojis)\n"
        "- post (a longer, more detailed and persuasive post for LinkedIn or Facebook)\n"
        "- hashtags (a list of 5-10 highly relevant trending hashtags)\n\n"
        "Do not include any other text, markdown blocks, or explanations. Just the raw JSON object."
    )

    try:
        # Call Gemini
        raw_response = await AIService.ask_gemini(prompt)
        
        # Clean and extract JSON using regex
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            promo_data = json.loads(json_str)
            
            result = PromotionResponse(
                caption=promo_data.get("caption", ""),
                post=promo_data.get("post", ""),
                hashtags=promo_data.get("hashtags", [])
            )

            # --- Database Persistence ---
            db = get_database()
            storage_data = result.model_dump()
            storage_data.update({
                "eventId": request.event_id,
                "eventTitle": request.event_title,
                "userId": current_user.get("id"),
                "createdAt": datetime.utcnow()
            })
            await db["ai_promotions"].insert_one(storage_data)
            # ----------------------------

            return result
        else:
            raise ValueError("AI response did not contain a valid JSON block.")

    except Exception as e:
        print(f"Promotion generation error: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"AI could not generate promotional content: {str(e)}"
        )
