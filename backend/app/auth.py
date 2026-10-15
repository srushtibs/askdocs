from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from .database import get_db
from . import models
from .security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class SignupIn(BaseModel):
    email: str
    password: str

@router.post("/signup", status_code=201)
def signup(data: SignupIn, db: Session = Depends(get_db)):
    if len(data.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if db.query(models.User).filter_by(email=data.email.lower()).first():
        raise HTTPException(400, "Email already registered")
    user = models.User(email=data.email.lower(), password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email}

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email=form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}
