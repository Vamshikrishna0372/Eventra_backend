from pydantic import BaseModel
from datetime import datetime

class NotificationCreate(BaseModel):
    userId: str
    message: str
    type: str

class NotificationResponse(BaseModel):
    id: str
    userId: str
    message: str
    type: str
    readStatus: bool
    createdAt: datetime
