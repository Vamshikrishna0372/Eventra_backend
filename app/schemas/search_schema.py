from pydantic import BaseModel, Field
from typing import List

class EventDetail(BaseModel):
    title: str = Field(..., description="Title of the event")
    category: str = Field(..., description="Event category")
    location: str = Field(..., description="Event venue or location")
    date: str = Field(..., description="Date of the event")

class EventSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    available_events: List[EventDetail] = Field(..., alias="available_events", description="List of events to search within")

    class Config:
        populate_by_name = True

class EventSearchResponse(BaseModel):
    results: List[EventDetail] = Field(..., description="Filtered list of events matching the query")
