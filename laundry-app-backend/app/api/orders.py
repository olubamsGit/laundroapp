from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.order import OrderCreate
from app.models.order import Order, OrderStatus, LaundryType as ModelLaundryType
from app.api.deps import get_db, customer_user, admin_user, driver_user
from app.models.user import User, UserRole
from app.db.base import Base

router = APIRouter(prefix="/orders", tags=["Orders"])
ALLOWED_STATUS_TRANSITIONS = {
    "picked_up": ["in_cleaning"],
    "in_cleaning": ["ready_for_delivery"],
    "ready_for_delivery": ["delivered"],
}


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

@router.get("/my", summary="Customer: track my orders")
def track_my_orders(
    current_user: User = Depends(customer_user),
    db: Session = Depends(get_db)
):
    orders = (
        db.query(Order)
        .filter(Order.customer_id == current_user.id)
        .order_by(Order.pickup_date.desc())
        .all()
    )

    return {
        "customer": current_user.email,
        "orders": [
            {
                "order_id": o.id,
                "pickup_address": o.pickup_address,
                "pickup_date": o.pickup_date,
                "status": o.status.value,
                "timeline": {
                    "scheduled": True,
                    "picked_up": o.status in [
                        OrderStatus.picked_up,
                        OrderStatus.in_cleaning,
                        OrderStatus.ready_for_delivery,
                        OrderStatus.delivered,
                    ],
                    "in_cleaning": o.status in [
                        OrderStatus.in_cleaning,
                        OrderStatus.ready_for_delivery,
                        OrderStatus.delivered,
                    ],
                    "ready_for_delivery": o.status in [
                        OrderStatus.ready_for_delivery,
                        OrderStatus.delivered,
                    ],
                    "delivered": o.status == OrderStatus.delivered,
                },
            }
            for o in orders
        ],
    }

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

@router.patch("/driver/update-status/{order_id}", summary="Driver: update order status")
def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    current_user: User = Depends(driver_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your assigned order")

    current_status = order.status.value
    requested_status = new_status.value

    allowed_next = ALLOWED_STATUS_TRANSITIONS.get(current_status, [])

    if requested_status not in allowed_next:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from '{current_status}' to '{requested_status}'",
        )

    order.status = new_status
    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated",
        "order_id": order.id,
        "old_status": current_status,
        "new_status": requested_status,
    }

@router.get("/admin/all", summary="Admin: view all orders")
def admin_view_all_orders(
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    orders = db.query(Order).order_by(Order.pickup_date.desc()).all()

    return {
        "total_orders": len(orders),
        "orders": [
            {
                "order_id": o.id,
                "customer_id": o.customer_id,
                "driver_id": o.driver_id,
                "pickup_address": o.pickup_address,
                "pickup_date": o.pickup_date,
                "status": o.status.value,
            }
            for o in orders
        ],
    }


@router.get("/admin/by-status", summary="Admin: filter orders by status")
def admin_filter_by_status(
    status: OrderStatus,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .filter(Order.status == status)
        .order_by(Order.pickup_date.desc())
        .all()
    )

    return {
        "status": status.value,
        "count": len(orders),
        "orders": [
            {
                "order_id": o.id,
                "customer_id": o.customer_id,
                "driver_id": o.driver_id,
                "pickup_address": o.pickup_address,
                "pickup_date": o.pickup_date,
            }
            for o in orders
        ],
    }


@router.get("/admin/by-driver", summary="Admin: filter orders by driver")
def admin_filter_by_driver(
    driver_id: str,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .filter(Order.driver_id == driver_id)
        .order_by(Order.pickup_date.desc())
        .all()
    )

    return {
        "driver_id": driver_id,
        "count": len(orders),
        "orders": [
            {
                "order_id": o.id,
                "customer_id": o.customer_id,
                "status": o.status.value,
                "pickup_address": o.pickup_address,
                "pickup_date": o.pickup_date,
            }
            for o in orders
        ],
    }


@router.get("/admin/summary", summary="Admin: order summary")
def admin_order_summary(
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    summary = {}

    for status in OrderStatus:
        summary[status.value] = (
            db.query(Order).filter(Order.status == status).count()
        )

    return {
        "total_orders": sum(summary.values()),
        "by_status": summary,
    }
