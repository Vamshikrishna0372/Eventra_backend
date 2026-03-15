import razorpay
import os
from fastapi import APIRouter, Depends, HTTPException
from app.database.connection import get_database
from app.middleware.auth_middleware import get_current_user
from app.schemas.payment_schema import PaymentCreate, PaymentVerify
from app.services.registration_service import RegistrationService
from app.models.payment_model import PaymentModel
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/payments", tags=["Payments"])

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "secret_placeholder")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@router.post("/create-order")
async def create_order(data: PaymentCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    event = await db["events"].find_one({"_id": ObjectId(data.eventId)})
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if not event.get("isPaidEvent"):
        raise HTTPException(status_code=400, detail="This is a free event")
    
    amount = int(event.get("price", 0) * 100) # Razorpay expects amount in paise
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid event price")
        
    order_data = {
        "amount": amount,
        "currency": "INR",
        "receipt": f"receipt_{data.eventId}_{current_user['id']}",
        "payment_capture": 1
    }
    
    try:
        order = client.order.create(data=order_data)
        return {"success": True, "data": order}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay error: {str(e)}")

@router.post("/verify")
async def verify_payment(data: PaymentVerify, current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    # 1. Verify Signature
    params_dict = {
        'razorpay_order_id': data.razorpay_order_id,
        'razorpay_payment_id': data.razorpay_payment_id,
        'razorpay_signature': data.razorpay_signature
    }
    
    try:
        client.utility.verify_payment_signature(params_dict)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    # 2. Store Payment Details
    event = await db["events"].find_one({"_id": ObjectId(data.eventId)})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    payment_record = {
        "userId": current_user["id"],
        "eventId": data.eventId,
        "orderId": data.razorpay_order_id,
        "paymentId": data.razorpay_payment_id,
        "amount": event.get("price"),
        "status": "completed",
        "createdAt": datetime.utcnow()
    }
    
    await db["payments"].insert_one(payment_record)
    
    # 3. Create Registration and Ticket
    # We can call RegistrationService.register_student but it needs to be aware that payment is done
    # Let's call it. register_student already checks for existing registrations.
    try:
        reg = await RegistrationService.register_student(data.eventId, current_user, is_paid=True)
        return {"success": True, "message": "Payment verified and registered", "data": reg}
    except Exception as e:
        # If registration fails after payment, we have a manual intervention case or we should log it
        # But here we'll try to return the error
        raise HTTPException(status_code=500, detail=f"Registration failed after payment: {str(e)}")
