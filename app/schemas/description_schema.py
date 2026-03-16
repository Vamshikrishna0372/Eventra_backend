from pydantic import BaseModel, Field
from typing import Optional

class EventDescriptionRequest(BaseModel):
    event_id: Optional[str] = Field(None, alias="event_id", description="Optional ID of the event to update")
    event_title: str = Field(..., alias="event_title", description="Title of the event")
    category: str = Field(..., description="Event category")
    location: str = Field(..., description="Event venue or location")
    date: str = Field(..., description="Date of the event")
    organizer: str = Field(..., description="Name of the organizer")

    class Config:
        populate_by_name = True

class EventDescriptionResponse(BaseModel):
    description: str = Field(..., description="The AI-generated event description")
