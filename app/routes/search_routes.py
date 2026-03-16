import json
import re
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.search_schema import EventSearchRequest, EventSearchResponse
from app.services.ai_service import AIService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.post("/search-events", response_model=EventSearchResponse)
async def semantic_event_search(
    request: EventSearchRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Performs a natural language search on available events using Gemini AI.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    if not request.available_events:
        return EventSearchResponse(results=[])

    # Format the events for the prompt
    events_list_str = ""
    for idx, event in enumerate(request.available_events, 1):
        events_list_str += f"{idx}. Title: {event.title}, Category: {event.category}, Location: {event.location}, Date: {event.date}\n"

    # Construct the instruction prompt
    prompt = (
        "You are an AI search assistant for the Eventra platform. "
        "Your goal is to parse the user's natural language query and return a list of events that match the intent.\n\n"
        f"User Query: '{request.query}'\n\n"
        "Available Events:\n"
        f"{events_list_str}\n\n"
        "Task:\n"
        "1. Identify every event from the list that matches the user's constraints (location, category, time, etc.).\n"
        "2. Return the results strictly as a JSON array of objects, where each object has these keys: 'title', 'category', 'location', 'date'.\n"
        "3. Match the event details exactly as provided in the list.\n"
        "4. If no events match, return an empty array [].\n\n"
        "Do not include any conversational text, markdown blocks, or explanations. Just the raw JSON array."
    )

    try:
        # Call Gemini
        raw_response = await AIService.ask_gemini(prompt)
        
        # Extract JSON array using regex
        json_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            results = json.loads(json_str)
            return EventSearchResponse(results=results)
        elif raw_response.strip() == "[]":
            return EventSearchResponse(results=[])
        else:
            # If the response is not a clean array, try parsing it directly if it looks like JSON
            try:
                results = json.loads(raw_response)
                if isinstance(results, list):
                    return EventSearchResponse(results=results)
            except:
                pass
            raise ValueError("AI response did not contain a valid JSON array of events.")

    except Exception as e:
        print(f"Smart search error: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"AI could not process the search query: {str(e)}"
        )
