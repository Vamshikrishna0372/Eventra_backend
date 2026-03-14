from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NotificationModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    userId: str
    title: str = "Notification"
    message: str
    type: str # e.g. "reminder", "update", "confirmation"
    readStatus: bool = False
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
