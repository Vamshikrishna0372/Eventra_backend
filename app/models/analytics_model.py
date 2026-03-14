from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AnalyticsModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    totalEvents: int = 0
    totalUsers: int = 0
    totalRegistrations: int = 0
    totalRevenue: float = 0.0
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
