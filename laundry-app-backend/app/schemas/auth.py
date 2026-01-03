from pydantic import BaseModel, constr

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    token: str
    new_password: constr(min_length=8)  # Enforce a minimum length