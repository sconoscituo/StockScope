from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import PlanType


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    plan: PlanType
    telegram_chat_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    telegram_chat_id: Optional[str] = None


class PlanUpgrade(BaseModel):
    plan: PlanType


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
