from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey , Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base




user_clubs = Table(
    'user_clubs',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('club_id', Integer, ForeignKey('clubs.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    role = Column(String, default="student")
    hashed_password = Column(String)
    notifications = relationship("Notification", back_populates="user")
    clubs = relationship("Club", secondary=user_clubs, back_populates="members")

class Club(Base):
    __tablename__ = "clubs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    members = relationship("User", secondary=user_clubs, back_populates="clubs")
    announcements = relationship("Announcement", back_populates="club", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    start_time = Column(DateTime)
    description = Column(String)
    rules = Column(String)
    is_featured = Column(Boolean, default=False)
    attendance_submitted = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False) 
    
    
    club = relationship("Club")
    # Added cascade so deleting an event deletes its RSVPs
    rsvps = relationship("RSVP", back_populates="event", cascade="all, delete-orphan")

class RSVP(Base):
    __tablename__ = "rsvps"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    event = relationship("Event", back_populates="rsvps")
    # Added cascade so deleting an RSVP deletes its attendance record
    attendance = relationship("Attendance", back_populates="rsvp", uselist=False, cascade="all, delete-orphan")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    rsvp_id = Column(Integer, ForeignKey("rsvps.id"), unique=True)
    is_present = Column(Boolean, default=False)
    checked_in_at = Column(DateTime)
    rsvp = relationship("RSVP", back_populates="attendance")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="notifications")


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    club = relationship("Club", back_populates="announcements")
    author = relationship("User")


class OTP(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    code = Column(String)
    expires_at = Column(DateTime)
    
    # Store pending registration data here temporarily
    name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)

class EmailQuota(Base):
    __tablename__ = "email_quotas"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True) # Stores "YYYY-MM-DD"
    count = Column(Integer, default=0)
    is_valid = Column(Boolean , default=True)



# State will save the variables state of the program after the container would stop , eg- valid_email_domains.

# class State(Base):
#     __tablename__ = "variables_state"
#     university_name = Column(String,primary_key=True)
#     valid_email_domains = Column(String,nullable=False)
    