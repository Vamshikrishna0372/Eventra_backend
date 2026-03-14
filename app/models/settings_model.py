from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SettingsModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    platformName: str = "Eventra"
    contactEmail: str
    supportPhone: str
    maintenanceMode: bool = False
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
