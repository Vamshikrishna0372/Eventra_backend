from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CoordinatorModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    email: str
    userId: Optional[str] = None
    phone: Optional[str] = None
    eventId: str
    eventTitle: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
