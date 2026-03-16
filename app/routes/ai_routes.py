from fastapi import APIRouter, HTTPException, Depends
from app.services.ai_service import AIService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.get("/test-ai")
async def test_ai():
    """
    Test endpoint to verify Gemini AI integration.
    """
    prompt = "Explain what the Eventra event management platform does in a short and professional way."
    
    try:
        response = await AIService.ask_gemini(prompt)
        return {
            "success": True,
            "message": "Gemini AI is connected and working!",
            "data": {
                "prompt": prompt,
                "response": response
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=502, 
            detail=f"Failed to connect to Gemini AI: {str(e)}"
        )
