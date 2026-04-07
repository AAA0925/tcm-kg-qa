from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"  # 普通用户
    ADMIN = "admin"  # 管理员

class UserBase(BaseModel):
    username: str
    email: str
    role: UserRole = UserRole.USER

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.USER

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None

class ProfileUpdate(BaseModel):
    username: str
    email: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str
