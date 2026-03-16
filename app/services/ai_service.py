import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
import asyncio

# Load environment variables
load_dotenv()

logger = logging.getLogger("eventra.ai")

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")

class AIService:
    _configured = False

    @classmethod
    def configure(cls):
        if not cls._configured:
            if not API_KEY:
                logger.error("GEMINI_API_KEY not found in environment variables.")
                return False
            try:
                # Force 'rest' transport for better reliability in different network environments
                genai.configure(api_key=API_KEY, transport='rest')
                cls._configured = True
                logger.info("Gemini AI (google-generativeai) configured successfully with REST transport.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini AI: {e}")
                return False
        return True

    @staticmethod
    async def ask_gemini(prompt: str) -> str:
        """
        Sends a prompt to the Google Gemini AI using the stable google-generativeai library.
        """
        if not AIService.configure():
            raise HTTPException(
                status_code=500, 
                detail="Gemini AI Service is not properly configured."
            )

        try:
            # Use gemini-1.5-flash which is widely available and stable
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Since google-generativeai is not natively async in the same way as the new SDK, 
            # we use to_thread to keep it non-blocking in FastAPI.
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response and response.text:
                return response.text
            else:
                raise HTTPException(
                    status_code=502, 
                    detail="Received an empty or invalid response from Gemini AI."
                )
                
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            raise HTTPException(
                status_code=502, 
                detail=f"AI Service Error: {str(e)}"
            )
