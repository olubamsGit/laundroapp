import sendgrid
from sendgrid.helpers.mail import Mail
from app.core.config import settings

def send_order_status_update_email(order_id: int, recipient_email: str, status: str):
    # This pulls the key we fixed in your config.py
    if not settings.sendgrid_api_key:
        print("SYSTEM ERROR: SENDGRID_API_KEY is not set in environment variables.")
        return

    message = Mail(
        from_email="youtvtosin01@gmail.com",  # MUST match your SendGrid Verified Sender
        to_emails=recipient_email,
        subject=f"LaundroApp: Order #{order_id} Update",
        plain_text_content=f"Hello! Your laundry order status has been updated to: {status}."
    )

    try:
        sg = sendgrid.SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")