from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Literal

RoleType = Literal["Guest", "Regular", "Admin", "SuperAdmin"]

class UserBase(BaseModel):
    email: EmailStr
    role: RoleType = "Regular"

class UserCreate(UserBase):
    password: str = Field(min_length=8, description="Password must be at least 8 characters.")

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True