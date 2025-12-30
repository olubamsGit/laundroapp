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
    default="argon2",
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

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    # Generic error to avoid leaking which part failed
    invalid_creds_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid email or password"
    )

    if not db_user:
        raise invalid_creds_error

    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )

    if not pwd_context.verify(user.password, db_user.hashed_password):
        raise invalid_creds_error

    # All good → issue tokens
    access_token = create_access_token(str(db_user.id), db_user.role.value)
    refresh_token = create_refresh_token(str(db_user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )