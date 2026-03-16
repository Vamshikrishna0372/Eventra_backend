from pydantic import BaseModel, Field
from typing import List, Optional

class FeedbackRequest(BaseModel):
    event_id: Optional[str] = Field(None, alias="event_id", description="Optional ID of the event this feedback belongs to")
    feedback: str = Field(..., description="The user's feedback text to analyze")

class FeedbackAnalysisResponse(BaseModel):
    positive_points: List[str] = Field(..., alias="positive_points", description="List of positive insights")
    negative_points: List[str] = Field(..., alias="negative_points", description="List of negative insights or pain points")
    suggestions: List[str] = Field(..., description="List of suggestions for improvement")

    class Config:
        populate_by_name = True
