from datetime import date
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field

class OrderTimeline(BaseModel):
    scheduled: bool
    picked_up: bool
    in_cleaning: bool
    ready_for_delivery: bool
    delivered: bool

class OrderPublic(BaseModel):
    order_id: UUID
    pickup_address: str
    pickup_date: date
    status: str
    special_instructions: Optional[str] = None

    driver_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None

    # pricing fields (optional if you added them)
    weight_lbs: Optional[int] = None
    subtotal_cents: Optional[int] = None
    tax_cents: Optional[int] = None
    total_cents: Optional[int] = None

    timeline: Optional[OrderTimeline] = None

class ListMeta(BaseModel):
    limit: int
    offset: int
    count: int
    total: int

class ListResponse(BaseModel):
    data: List[OrderPublic]
    meta: ListMeta

class SingleResponse(BaseModel):
    data: OrderPublic
