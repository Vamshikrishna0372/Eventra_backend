"""
ai_service.py — Eventra AI Service using google-genai SDK (official, non-deprecated)

The old google-generativeai package is deprecated and produces:
  FutureWarning: All support for the `google.generativeai` package has ended.

This rewrite uses the new `google-genai` package which supports:
  - gemini-2.0-flash (fast, cheap, supports generateContent)
  - Proper async via asyncio.to_thread
  - Clean error handling with a safe fallback message
"""

import os
import logging
import asyncio
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("eventra.ai")

API_KEY = os.getenv("GEMINI_API_KEY")

# ─── Model selection ─────────────────────────────────────────────────────────
# Confirmed working models for this API key (verified via client.models.list()):
#   gemini-2.5-flash  → latest, fast, full generateContent support
#   gemini-2.0-flash-001 → stable pinned version, good fallback
PREFERRED_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL  = "gemini-2.0-flash-001"
# ─────────────────────────────────────────────────────────────────────────────

FALLBACK_RESPONSE = (
    "Sorry, the AI assistant is temporarily unavailable. "
    "Please try again later or browse the Explore Events tab for information."
)


class AIService:
    """
    Thin wrapper around the new google-genai SDK.
    Using asyncio.to_thread so FastAPI stays non-blocking.
    """

    _client = None  # lazy-init so startup is fast even if key is missing

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            if not API_KEY:
                logger.error("[AI] GEMINI_API_KEY is not set in environment variables.")
                return None
            try:
                import google.genai as genai          # new SDK — not deprecated
                cls._client = genai.Client(api_key=API_KEY)
                logger.info("[AI] google-genai client initialised successfully.")
            except Exception as e:
                logger.error(f"[AI] Failed to create google-genai client: {e}")
                return None
        return cls._client

    @staticmethod
    def _call_gemini_sync(prompt: str) -> str:
        """
        Synchronous Gemini call — run inside to_thread to avoid blocking the event loop.
        """
        client = AIService._get_client()
        if client is None:
            return FALLBACK_RESPONSE

        # Try preferred model, fall back to legacy flash if it fails
        for model_name in (PREFERRED_MODEL, FALLBACK_MODEL):
            try:
                logger.info(f"[AI] Sending request to model: {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                # Extract text from response
                text = ""
                if hasattr(response, "text") and response.text:
                    text = response.text
                elif hasattr(response, "candidates") and response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, "text"):
                            text += part.text
                
                if text.strip():
                    logger.info(f"[AI] Response received from {model_name} ({len(text)} chars).")
                    return text.strip()
                else:
                    logger.warning(f"[AI] Empty response from {model_name}, trying fallback.")
            except Exception as e:
                logger.warning(f"[AI] Error with model {model_name}: {e}")
                continue

        # Both models failed
        logger.error("[AI] All Gemini models failed. Returning fallback response.")
        return FALLBACK_RESPONSE

    @staticmethod
    async def ask_gemini(prompt: str) -> str:
        """
        Async-safe entry point for the chatbot route.
        Returns clean text or a safe fallback — never raises a 502 to the caller.
        """
        try:
            result = await asyncio.to_thread(AIService._call_gemini_sync, prompt)
            return result
        except Exception as e:
            logger.error(f"[AI] Unexpected error in ask_gemini: {e}")
            return FALLBACK_RESPONSE


# ─── Backwards-compat helper used by ai_routes.py ─────────────────────────
async def ask_gemini(prompt: str) -> str:
    return await AIService.ask_gemini(prompt)
