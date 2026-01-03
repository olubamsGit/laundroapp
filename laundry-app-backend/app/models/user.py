import uuid
import enum
from sqlalchemy import Column, String, Boolean, Enum, DateTime # Add DateTime
from sqlalchemy.sql import func # Add func for timestamps
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class UserRole(str, enum.Enum):
    customer = "customer"
    driver = "driver"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.customer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Add this line to track account age
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)