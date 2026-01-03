from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # JWT & Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    FRONTEND_BASE_URL: str
    
    # Database
    DATABASE_URL: str

    # SendGrid
    # Using Optional allows the app to start even if the key is missing
    sendgrid_api_key: Optional[str] = None
    from_email: Optional[str] = "youtvtosin01@gmail.com"

    # New Pydantic V2 configuration style
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # This prevents the "Extra inputs are not permitted" crash
    )

settings = Settings()