from pydantic import BaseModel
from datetime import datetime

class RegistrationCreate(BaseModel):
    eventId: str

class RegistrationResponse(BaseModel):
    id: str
    userId: str
    eventId: str
    status: str
    registeredAt: datetime
