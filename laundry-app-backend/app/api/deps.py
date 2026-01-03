from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from fastapi.security import OAuth2PasswordBearer


# --------------------
# Database Session
# --------------------


# --------------------
# Token Bearer Scheme
# --------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# --------------------
# Current User
# --------------------
def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    return user


# --------------------
# Role Based Access
# --------------------
def require_role(required_role: str):
    def role_checker(user = Depends(get_current_user)):
        if user.role.value != required_role:
            raise HTTPException(status_code=403, detail="Not authorized for this role")
        return user
    return role_checker


def customer_user(user = Depends(require_role("customer"))):
    return user

def driver_user(user = Depends(require_role("driver"))):
    return user

def admin_user(user = Depends(require_role("admin"))):
    return user

def admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user
