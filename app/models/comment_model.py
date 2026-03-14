from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CommentModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    eventId: str
    userId: str
    text: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
