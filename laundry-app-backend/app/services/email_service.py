def send_verification_email(email: str, token: str):
    verification_link = f"http://127.0.0.1:8000/auth/verify-email?token={token}"
    print("==============================================")
    print(f"TO: {email}")
    print("SUBJECT: Verify your email")
    print(f"CLICK THIS LINK TO VERIFY: {verification_link}")
    print("==============================================\n")