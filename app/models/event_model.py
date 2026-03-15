from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class EventModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    title: str
    description: str
    date: str
    time: str
    venue: str
    category: str
    organizerId: Optional[str] = None
    organizerName: str
    organizerEmail: Optional[str] = "support@eventra.com"
    coordinators: List[dict] = []
    imageUrl: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    maxParticipants: int
    registeredCount: int = 0
    status: str = "open"
    isPaidEvent: bool = False
    price: float = 0.0
    isFeatured: bool = False
    categoryId: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
