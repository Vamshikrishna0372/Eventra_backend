from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaymentModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    userId: str
    eventId: str
    amount: float
    currency: str = "INR"
    paymentMethod: str
    paymentStatus: str = "pending"
    transactionId: Optional[str] = None
    paymentDate: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
