import uuid
from sqlalchemy import Column, String, Enum, Date, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import User
from app.db.base import Base
from enum import Enum as PyEnum


class LaundryType(PyEnum):
    regular = "regular"
    dry_clean = "dry_clean"


class OrderStatus(PyEnum):
    scheduled = "scheduled"
    picked_up = "picked_up"
    in_cleaning = "in_cleaning"
    ready_for_delivery = "ready_for_delivery"
    delivered = "delivered"


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)

    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    pickup_address = Column(String, nullable=False)
    laundry_type = Column(Enum(LaundryType), nullable=False)
    pickup_date = Column(Date, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.scheduled, nullable=False)
    special_instructions = Column(String, nullable=True)

    weight_lbs = Column(Integer, nullable=True)

    price_per_lb_cents = Column(Integer, nullable=False, default=175)
    service_fee_cents = Column(Integer, nullable=False, default=300)
    delivery_fee_cents = Column(Integer, nullable=False, default=500)
    tax_rate_bp = Column(Integer, nullable=False, default=700)  # basis points: 700 = 7.00%

    subtotal_cents = Column(Integer, nullable=True)
    tax_cents = Column(Integer, nullable=True)
    total_cents = Column(Integer, nullable=True)
    is_paid = Column(Boolean, default=False)
    stripe_payment_intent_id = Column(String, nullable=True)

    # Explicit relationships to resolve ambiguity
    customer = relationship("User", foreign_keys=[customer_id])
    driver = relationship("User", foreign_keys=[driver_id])
