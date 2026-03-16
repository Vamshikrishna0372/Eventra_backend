import json
import re
from datetime import datetime
from app.database.connection import get_database
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.planner_schema import EventPlanRequest, EventPlanResponse
from app.services.ai_service import AIService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api", tags=["AI Services"])

@router.post("/generate-event-plan", response_model=EventPlanResponse)
async def generate_event_plan(
    request: EventPlanRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Generates a structured event plan including schedule, preparation tasks, and logistics using Gemini AI.
    """
    
    # Construct the instruction prompt for structured planning
    prompt = (
        "You are an expert event planning assistant for the Eventra platform. "
        "Create a comprehensive and structured event plan based on these details:\n\n"
        f"Event Title: {request.event_title}\n"
        f"Event Type: {request.event_type}\n"
        f"Duration: {request.duration}\n"
        f"Expected Attendees: {request.expected_attendees}\n"
        f"Location: {request.location}\n\n"
        "Return the plan strictly in JSON format with exactly these keys:\n"
        "- schedule (a list of descriptive strings with times)\n"
        "- preparation_tasks (a list of priority tasks)\n"
        "- logistics_checklist (a list of necessary equipment and services)\n\n"
        "Do not include any conversational text, markdown formatting (no ```json blocks), or explanations. "
        "Just the raw JSON object."
    )

    try:
        # Call Gemini
        raw_response = await AIService.ask_gemini(prompt)
        
        # Extract JSON using regex to be safe
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            plan_data = json.loads(json_str)
            
            result = EventPlanResponse(
                schedule=plan_data.get("schedule", []),
                preparation_tasks=plan_data.get("preparation_tasks", []),
                logistics_checklist=plan_data.get("logistics_checklist", [])
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
            await db["ai_event_plans"].insert_one(storage_data)
            # ----------------------------

            return result
        else:
            raise ValueError("AI response did not contain a valid JSON object.")

    except Exception as e:
        print(f"Event planning error: {str(e)}")
        raise HTTPException(
            status_code=502, 
            detail=f"AI could not generate a structured event plan: {str(e)}"
        )
