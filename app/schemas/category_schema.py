from pydantic import BaseModel
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    description: str
    color: str = "#8B5CF6"
    icon: str = "LayoutGrid"

class CategoryResponse(BaseModel):
    id: str
    name: str
    description: str
    color: str
    icon: str
    createdAt: datetime
