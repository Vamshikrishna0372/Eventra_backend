from pydantic import BaseModel, Field
from typing import List, Optional

class EventInfo(BaseModel):
    title: str = Field(..., description="Title of the event")
    category: str = Field(..., description="Event category")
    location: str = Field(..., description="Event venue or location")

class RecommendationRequest(BaseModel):
    user_interests: List[str] = Field(..., alias="user_interests", description="List of user interest tags")
    available_events: List[EventInfo] = Field(..., alias="available_events", description="List of available events to recommend from")

    class Config:
        populate_by_name = True

class RecommendationResponse(BaseModel):
    recommendations: str = Field(..., description="The AI-generated recommendations and explanations")
