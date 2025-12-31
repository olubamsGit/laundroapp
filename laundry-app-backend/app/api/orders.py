from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.order import OrderCreate
from app.models.order import Order, OrderStatus, LaundryType as ModelLaundryType
from app.api.deps import get_db, customer_user, admin_user, driver_user
from app.models.user import User, UserRole
from app.db.base import Base

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/create")
def create_order(
    order_data: OrderCreate,
    current_user = Depends(customer_user),
    db: Session = Depends(get_db)
):
    new_order = Order(
        customer_id=current_user.id,
        pickup_address=order_data.pickup_address,
        laundry_type=ModelLaundryType(order_data.laundry_type.value),
        pickup_date=order_data.pickup_date,
        special_instructions=order_data.special_instructions,
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "message": "Order created successfully",
        "order_id": str(new_order.id),
        "status": new_order.status.value
    }

@router.get("/my")
def list_my_orders(
    current_user = Depends(customer_user),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(Order.customer_id == current_user.id).all()

    return [
        {
            "order_id": str(order.id),
            "pickup_address": order.pickup_address,
            "laundry_type": order.laundry_type.value,
            "pickup_date": str(order.pickup_date),
            "status": order.status.value,
            "special_instructions": order.special_instructions,
        }
        for order in orders
    ]

@router.patch("/assign/{order_id}")
def assign_order_to_driver(
    order_id: str,
    driver_id: str,
    admin = Depends(admin_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    driver = db.query(User).filter(User.id == driver_id, User.role == UserRole.driver).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found or is not a driver")

    order.driver_id = driver.id
    order.status = OrderStatus.picked_up  # optional, can be changed later

    db.commit()
    db.refresh(order)

    return {
        "message": f"Order assigned to driver {driver.email}",
        "order_id": str(order.id),
        "driver": driver.email,
        "status": order.status.value
    }

@router.get("/driver/assigned", summary="Driver: view assigned orders")
def get_assigned_orders(
    current_user: User = Depends(driver_user),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(Order.driver_id == current_user.id).all()

    if not orders:
        return {
            "message": "No assigned orders yet",
            "orders": []
        }

    return {
        "driver": current_user.email,
        "assigned_orders": [
            {
                "order_id": o.id,
                "pickup_address": o.pickup_address,
                "status": o.status.value,
                "pickup_date": o.pickup_date,
                "special_instructions": o.special_instructions
            }
            for o in orders
        ]
    }
