from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ParticipantModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    eventId: str
    userId: str
    checkedIn: bool = False
    checkedInTime: Optional[datetime] = None

    class Config:
        populate_by_name = True
