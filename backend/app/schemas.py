from pydantic import BaseModel, ConfigDict
from datetime import datetime

# --- Auth & User ---
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str = "student"

class UserLogin(BaseModel):
    email: str
    password: str

class PasswordReset(BaseModel):
    email:str
    otp:str
    new_password:str


class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    clubs: list[ClubResponse] = [] 
    model_config = ConfigDict(from_attributes=True)

# --- Club ---
class ClubResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class ClubCreate(BaseModel):
    name: str


# --- Event ---
class EventCreate(BaseModel):
    title: str
    club_id: int
    start_time: datetime
    description: str
    rules: str
    is_featured: bool = False

class EventResponse(BaseModel):
    id: int
    title: str
    start_time: datetime
    description: str
    rules: str
    is_featured: bool
    attendance_submitted: bool = False 
    club: ClubResponse
    rsvp_count: int = 0
    model_config = ConfigDict(from_attributes=True)

# --- RSVP & Attendance ---
class RSVPResponse(BaseModel):
    id: int
    event: EventResponse
    model_config = ConfigDict(from_attributes=True)

class AttendanceMark(BaseModel):
    rsvp_id: int
    is_present: bool

class BotQuery(BaseModel):
    question: str

# --- Notifications ---

class NotificationResponse(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


#  --- Announcements ---

class AnnouncementCreate(BaseModel):
    title: str
    content: str

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    club_id: int
    club_name: str = ""
    model_config = ConfigDict(from_attributes=True)


# --- OTP ---
class OTPVerify(BaseModel):
    email: str
    otp: str

