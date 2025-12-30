from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, customer_user, driver_user, admin_user

router = APIRouter(prefix="/test", tags=["Test Secure"])

@router.get("/any")
def test_any(user = Depends(get_current_user)):
    return {"message": f"Hello, {user.email}. Role: {user.role.value}"}

@router.get("/customer")
def test_customer(user = Depends(customer_user)):
    return {"message": f"Customer access granted to {user.email}"}

@router.get("/driver")
def test_driver(user = Depends(driver_user)):
    return {"message": "Driver endpoint OK"}

@router.get("/admin")
def test_admin(user = Depends(admin_user)):
    return {"message": "Admin endpoint OK"}
