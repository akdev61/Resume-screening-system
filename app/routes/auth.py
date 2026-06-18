from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import MessageResponse, Token, UserCreate, UserResponse, UserUpdate, UserUpdateResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")
    db.add(User(
        first_name=payload.first_name, last_name=payload.last_name,
        email=payload.email, hashed_password=hash_password(payload.password),
    ))
    db.commit()
    return MessageResponse(message="Account created successfully")


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    return Token(access_token=create_access_token(subject=user.email))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserUpdateResponse)
def update_profile(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if db.query(User).filter(User.email == payload.email, User.id != current_user.id).first():
        raise HTTPException(400, "Email already in use")
    email_changed = current_user.email != payload.email
    current_user.first_name = payload.first_name
    current_user.last_name = payload.last_name
    current_user.email = payload.email
    if payload.password:
        current_user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(current_user)
    return UserUpdateResponse(
        user=UserResponse.model_validate(current_user),
        access_token=create_access_token(current_user.email) if email_changed else None,
    )
