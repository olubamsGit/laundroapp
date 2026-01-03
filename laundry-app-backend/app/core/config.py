from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    DATABASE_URL: str
    FRONTEND_BASE_URL: str
    
    # Add this line to handle the SendGrid key
    sendgrid_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        # This line prevents the crash if other random env vars exist
        extra = "ignore" 

settings = Settings()