from pydantic import BaseModel
from typing import Optional

class PaymentCreate(BaseModel):
    eventId: str

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    eventId: str

class CheckInRequest(BaseModel):
    ticketId: str
