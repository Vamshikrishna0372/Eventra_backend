from pydantic import BaseModel, Field
from typing import List, Optional

class EventPlanRequest(BaseModel):
    event_id: Optional[str] = Field(None, alias="event_id", description="Optional ID of the event being planned")
    event_title: str = Field(..., alias="event_title", description="Title of the event")
    event_type: str = Field(..., alias="event_type", description="Type of event (e.g., Workshop, Conference)")
    duration: str = Field(..., description="Duration (e.g., 1 day, 3 hours)")
    expected_attendees: int = Field(..., alias="expected_attendees", description="Number of expected attendees")
    location: str = Field(..., description="Location or venue")

    class Config:
        populate_by_name = True

class EventPlanResponse(BaseModel):
    schedule: List[str] = Field(..., description="Suggested timeline/schedule for the event")
    preparation_tasks: List[str] = Field(..., alias="preparation_tasks", description="Key tasks for preparation")
    logistics_checklist: List[str] = Field(..., alias="logistics_checklist", description="Checklist for logistics and equipment")

    class Config:
        populate_by_name = True
