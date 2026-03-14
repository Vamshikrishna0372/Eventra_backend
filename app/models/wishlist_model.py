from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WishlistModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    userId: str
    eventId: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
