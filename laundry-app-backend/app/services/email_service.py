import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import HTTPException
from app.core.config import settings

def send_verification_email(email: str, token: str):
    verification_link = f"{settings.FRONTEND_BASE_URL}/api/v1/auth/verify-email?token={token}"
    print("==============================================")
    print(f"TO: {email}")
    print("SUBJECT: Verify your email")
    print(f"CLICK THIS LINK TO VERIFY: {verification_link}")
    print("==============================================\n")


def send_email(subject: str, to_email: str, content: str):
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        message = Mail(
            from_email="youtvtosin01@gmail.com",  # Your verified SendGrid email
            to_emails=to_email,
            subject=subject,
            plain_text_content=content,
        )
        response = sg.send(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error sending email")


def send_order_status_update_email(order_id: str, customer_email: str, status: str):
    subject = f"Order #{order_id} status update"
    content = f"Your order #{order_id} has been updated to: {status}. Thank you for using our service."
    return send_email(subject, customer_email, content)


def send_pricing_update_email(order_id: str, customer_email: str, total_cents: int):
    subject = f"Order #{order_id} pricing update"
    total_dollars = total_cents / 100
    content = f"Your order #{order_id} pricing has been updated. Total cost: ${total_dollars:.2f}."
    return send_email(subject, customer_email, content)