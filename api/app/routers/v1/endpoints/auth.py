from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.routers.deps import get_current_user
from app.db.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate(email=payload.email, password=payload.password)
    return TokenResponse(access_token=service.build_token(user))


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)):
    return current_user

