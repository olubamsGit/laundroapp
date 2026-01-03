import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_payment_intent(amount_cents: int, order_id: str):
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        metadata={"order_id": order_id},
        automatic_payment_methods={"enabled": True},
    )
