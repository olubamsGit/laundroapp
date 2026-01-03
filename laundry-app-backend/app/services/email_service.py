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


async def send_email(to_email: str, subject: str, content: str):
    # This pulls from your Render environment variables
    api_key = os.environ.get('SENDGRID_API_KEY')
    sender = os.environ.get('SENDGRID_FROM_EMAIL') # Your verified sender email
    
    message = Mail(
        from_email=sender,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"SendGrid Error: {e}")
        return None


def send_order_status_update_email(order_id: str, customer_email: str, status: str):
    subject = f"Order #{order_id} status update"
    content = f"Your order #{order_id} has been updated to: {status}. Thank you for using our service."
    return send_email(subject, customer_email, content)


def send_pricing_update_email(order_id: str, customer_email: str, total_cents: int):
    subject = f"Order #{order_id} pricing update"
    total_dollars = total_cents / 100
    content = f"Your order #{order_id} pricing has been updated. Total cost: ${total_dollars:.2f}."
    return send_email(subject, customer_email, content)