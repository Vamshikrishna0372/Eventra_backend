from pydantic import BaseModel, Field
from typing import List, Optional

class PromotionRequest(BaseModel):
    event_id: Optional[str] = Field(None, alias="event_id", description="Optional ID of the event this promotion is for")
    event_title: str = Field(..., alias="event_title", description="Title of the event")
    category: str = Field(..., description="Event category")
    location: str = Field(..., description="Location or venue")
    date: str = Field(..., description="Date of the event")
    target_audience: str = Field(..., alias="target_audience", description="Description of the target audience")

    class Config:
        populate_by_name = True

class PromotionResponse(BaseModel):
    caption: str = Field(..., description="A short, catchy social media caption")
    post: str = Field(..., description="A long, informative promotional post")
    hashtags: List[str] = Field(..., description="A list of relevant hashtags")
