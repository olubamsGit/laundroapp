from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import UserRegister, UserLogin
from app.schemas.auth import TokenResponse
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.services.password_validation import validate_password_strength
from app.core.token import (
    create_email_verification_token,
    verify_email_token,
    create_access_token,
    create_refresh_token,
)
from app.services.email_service import send_verification_email
from passlib.context import CryptContext

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__memory_cost=65536,  # matches m=65536
    argon2__time_cost=3,        # matches t=3
    argon2__parallelism=4,      # matches p=4
    deprecated="auto"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    # Check if email exists
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate password
    if not validate_password_strength(user.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters and include upper, lower, number, and symbol."
        )

    # Hash password
    hashed_pw = pwd_context.hash(user.password)

    # Create inactive, unverified customer account
    new_user = User(
        email=user.email,
        hashed_password=hashed_pw,
        role=UserRole.customer,
        is_verified=False,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create token + print "email"
    token = create_email_verification_token(new_user.id)
    send_verification_email(new_user.email, token)

    return {
        "message": "Account created. Please check your email to verify your account.",
        "email": new_user.email
    }

    from app.core.token import verify_email_token

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user_id = verify_email_token(token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()

    return {"message": "Email verified. You may now log in."}

from fastapi import Form
from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username
    password = form_data.password

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")


    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified yet")

    access_token = create_access_token(user_id=user.id, role=user.role)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role
}
