from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EventCreate(BaseModel):
    title: str
    description: str
    date: str
    time: str
    venue: str
    category: str
    imageUrl: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    maxParticipants: int
    organizerName: str
    isPaidEvent: bool = False
    price: float = 0.0
    isFeatured: bool = False
    coordinators: Optional[List[dict]] = []

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    venue: Optional[str] = None
    category: Optional[str] = None
    imageUrl: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    maxParticipants: Optional[int] = None
    organizerName: Optional[str] = None
    isPaidEvent: Optional[bool] = None
    price: Optional[float] = None
    isFeatured: Optional[bool] = None
    status: Optional[str] = None
    coordinators: Optional[List[dict]] = None

class EventResponse(BaseModel):
    id: str
    title: str
    description: str
    date: str
    time: str
    venue: str
    category: str
    organizerId: str
    imageUrl: Optional[str]
    thumbnailUrl: Optional[str] = None
    maxParticipants: int
    registeredCount: int
    status: str
    organizerName: str
    isPaidEvent: bool
    price: float
    isFeatured: bool = False
    createdAt: datetime
