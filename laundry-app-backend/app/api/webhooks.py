import stripe
import os
from fastapi import APIRouter, Request, HTTPException
from app.db.session import get_db
from app.models.order import Order
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            os.getenv("STRIPE_WEBHOOK_SECRET"),
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook")

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        order_id = intent["metadata"].get("order_id")

        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.is_paid = True
            db.commit()

    return {"status": "ok"}
