from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class EventStatistics(BaseModel):
    event_id: Optional[str] = Field(None, alias="event_id", description="Optional ID of the event being analyzed")
    attendance: int = Field(..., description="Total number of attendees")
    average_rating: float = Field(..., description="Average rating from 1 to 5")
    feedback_summary: str = Field(..., description="A summary of the collected feedback")

class AnalyticsInsightsRequest(BaseModel):
    event_statistics: EventStatistics = Field(..., alias="event_statistics", description="Key statistics of the event")

    class Config:
        populate_by_name = True

class AnalyticsInsightsResponse(BaseModel):
    insights: str = Field(..., description="AI-generated insights and recommendations for future events")
