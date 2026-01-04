from pydantic import BaseModel, constr

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    token: str
    new_password: constr(min_length=8)  # Enforce a minimum length

# Add these at the top with your other Pydantic models
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str # You can add min_length=8 here for security