from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.schemas.order_response import OrderPublic, OrderTimeline, ListResponse, ListMeta
from app.schemas.order import OrderCreate
from app.models.order import Order, OrderStatus, LaundryType as ModelLaundryType
from app.services.pricing import calc_price
from app.services.email_service import send_order_status_update_email
from app.api.deps import get_db, customer_user, admin_user, driver_user
from app.models.user import User, UserRole
from app.db.base import Base
from app.services.stripe_service import create_payment_intent
from app.core.email import send_order_status_update_email

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

@router.get("/my", response_model=ListResponse, summary="Customer: track my orders (paginated)")
def track_my_orders(
    limit: int = 20,
    offset: int = 0,
    status: Optional[OrderStatus] = None,
    current_user: User = Depends(customer_user),
    db: Session = Depends(get_db),
):
    # guardrails
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    base_q = db.query(Order).filter(Order.customer_id == current_user.id)

    if status:
        base_q = base_q.filter(Order.status == status)

    total = base_q.count()

    orders = (
        base_q.order_by(Order.pickup_date.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    def timeline_for(s: OrderStatus) -> OrderTimeline:
        return OrderTimeline(
            scheduled=True,
            picked_up=s in [OrderStatus.picked_up, OrderStatus.in_cleaning, OrderStatus.ready_for_delivery, OrderStatus.delivered],
            in_cleaning=s in [OrderStatus.in_cleaning, OrderStatus.ready_for_delivery, OrderStatus.delivered],
            ready_for_delivery=s in [OrderStatus.ready_for_delivery, OrderStatus.delivered],
            delivered=s == OrderStatus.delivered,
        )

    data = [
        OrderPublic(
            order_id=o.id,
            pickup_address=o.pickup_address,
            pickup_date=o.pickup_date,
            status=o.status.value,
            special_instructions=o.special_instructions,
            driver_id=o.driver_id,
            customer_id=o.customer_id,
            weight_lbs=getattr(o, "weight_lbs", None),
            subtotal_cents=getattr(o, "subtotal_cents", None),
            tax_cents=getattr(o, "tax_cents", None),
            total_cents=getattr(o, "total_cents", None),
            timeline=timeline_for(o.status),
        )
        for o in orders
    ]

    return ListResponse(
        data=data,
        meta=ListMeta(limit=limit, offset=offset, count=len(data), total=total),
    )


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

@router.get("/driver/assigned", response_model=ListResponse, summary="Driver: view assigned orders (paginated)")
def get_assigned_orders(
    limit: int = 20,
    offset: int = 0,
    status: Optional[OrderStatus] = None,
    current_user: User = Depends(driver_user),
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    base_q = db.query(Order).filter(Order.driver_id == current_user.id)
    if status:
        base_q = base_q.filter(Order.status == status)

    total = base_q.count()

    orders = (
        base_q.order_by(Order.pickup_date.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    data = [
        OrderPublic(
            order_id=o.id,
            pickup_address=o.pickup_address,
            pickup_date=o.pickup_date,
            status=o.status.value,
            special_instructions=o.special_instructions,
            driver_id=o.driver_id,
            customer_id=o.customer_id,
        )
        for o in orders
    ]

    return ListResponse(
        data=data,
        meta=ListMeta(limit=limit, offset=offset, count=len(data), total=total),
    )

@router.patch("/driver/update-status/{order_id}", summary="Driver: update order status")
def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    current_user: User = Depends(driver_user),
    db: Session = Depends(get_db)
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

    send_order_status_update_email(order.id, current_user.email, new_status.value)

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


@router.get("/quote", summary="Customer: get pricing quote by weight")
def quote_price(
    weight_lbs: int,
    current_user: User = Depends(customer_user),
):
    breakdown = calc_price(weight_lbs)

    return {
        "weight_lbs": breakdown.weight_lbs,
        "price_per_lb_cents": breakdown.price_per_lb_cents,
        "service_fee_cents": breakdown.service_fee_cents,
        "delivery_fee_cents": breakdown.delivery_fee_cents,
        "tax_rate_bp": breakdown.tax_rate_bp,
        "subtotal_cents": breakdown.subtotal_cents,
        "tax_cents": breakdown.tax_cents,
        "total_cents": breakdown.total_cents,
    }


@router.patch("/admin/set-weight/{order_id}", summary="Admin: set weight and calculate totals")
def admin_set_weight_and_price(
    order_id: str,
    weight_lbs: int,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    breakdown = calc_price(
        weight_lbs=weight_lbs,
        price_per_lb_cents=order.price_per_lb_cents,
        service_fee_cents=order.service_fee_cents,
        delivery_fee_cents=order.delivery_fee_cents,
        tax_rate_bp=order.tax_rate_bp,
    )

    order.weight_lbs = breakdown.weight_lbs
    order.subtotal_cents = breakdown.subtotal_cents
    order.tax_cents = breakdown.tax_cents
    order.total_cents = breakdown.total_cents

    db.commit()
    db.refresh(order)

    return {
        "message": "Pricing updated",
        "order_id": str(order.id),
        "weight_lbs": order.weight_lbs,
        "subtotal_cents": order.subtotal_cents,
        "tax_cents": order.tax_cents,
        "total_cents": order.total_cents,
    }


@router.post("/pay/{order_id}", summary="Customer: pay for order")
def pay_for_order(
    order_id: str,
    current_user: User = Depends(customer_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")

    if not order.total_cents:
        raise HTTPException(status_code=400, detail="Order pricing not finalized")

    if order.is_paid:
        raise HTTPException(status_code=400, detail="Order already paid")

    intent = create_payment_intent(order.total_cents, str(order.id))

    order.stripe_payment_intent_id = intent.id
    db.commit()

    return {
        "client_secret": intent.client_secret,
        "amount_cents": order.total_cents,
    }