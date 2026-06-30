from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "STUDENT"

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Club Schemas
class ClubCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ClubResponse(ClubCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

# Event Schemas
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: datetime
    club_id: int

class EventResponse(EventCreate):
    id: int
    class Config:
        from_attributes = True