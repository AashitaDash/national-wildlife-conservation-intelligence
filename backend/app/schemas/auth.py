from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None


class UserBase(BaseModel):
    email: str
    full_name: str
    organization: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role_name: Optional[str] = "VIEWER"


class UserLogin(BaseModel):
    email: str
    password: str


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    is_active: bool
    role_id: int
    role: Optional[RoleResponse] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
