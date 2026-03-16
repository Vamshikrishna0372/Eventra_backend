from fastapi import APIRouter
from app.services.ai_service import AIService

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.get("/test-ai")
async def test_ai():
    """
    Health-check endpoint to verify Gemini AI integration.
    Always returns 200 — AIService returns a safe fallback if Gemini is unavailable.
    """
    prompt = "In one sentence, describe what the Eventra campus event management platform does."
    response = await AIService.ask_gemini(prompt)
    is_fallback = "temporarily unavailable" in response.lower()
    return {
        "success": not is_fallback,
        "message": "Gemini AI is connected and working!" if not is_fallback else "AI fallback active — check API key or model name.",
        "data": {"prompt": prompt, "response": response}
    }
