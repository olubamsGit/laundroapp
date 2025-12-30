from pydantic import BaseModel
from datetime import date
from enum import Enum


class LaundryType(str, Enum):
    regular = "regular"
    dry_clean = "dry_clean"


class OrderCreate(BaseModel):
    pickup_address: str
    laundry_type: LaundryType
    pickup_date: date
    special_instructions: str | None = None
