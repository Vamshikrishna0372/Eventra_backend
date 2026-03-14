from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class RegistrationModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    userId: str
    eventId: str
    registrationStatus: str = "confirmed"
    paymentStatus: str = "completed"
    registrationDate: datetime = Field(default_factory=datetime.utcnow)
    attendanceStatus: str = "pending"
    ticketNumber: Optional[str] = None

    class Config:
        populate_by_name = True
