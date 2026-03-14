from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AuditLogModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    userId: str
    action: str
    resourceType: str
    resourceId: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
