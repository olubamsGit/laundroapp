import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import HTTPException
from app.core.config import settings

# Fully corrected send_verification_email
async def send_verification_email(email: str, token: str):
    base_url = settings.FRONTEND_BASE_URL.rstrip('/')
    verification_link = f"{base_url}/api/v1/auth/verify-email?token={token}"
    
    subject = "Verify your email"
    content = f"Please click the link to verify your email: {verification_link}"
    
    # This is the line that actually triggers SendGrid
    return await send_email(email, subject, content)


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


d# Use 'async def' so you can use 'await' inside
async def send_order_status_update_email(order_id: str, customer_email: str, status: str):
    subject = f"Order #{order_id} status update"
    content = f"Your order #{order_id} has been updated to: {status}."
    # You MUST await the send_email coroutine
    return await send_email(customer_email, subject, content)

async def send_pricing_update_email(order_id: str, customer_email: str, total_cents: int):
    subject = f"Order #{order_id} pricing update"
    total_dollars = total_cents / 100
    content = f"Your order #{order_id} pricing has been updated. Total cost: ${total_dollars:.2f}."
    # You MUST await the send_email coroutine
    return await send_email(customer_email, subject, content)