from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session
from sqlalchemy import func  

from datetime import datetime, timedelta , timezone
from database import engine, get_db, Base
import models, schemas 
from auth import verify_password , get_password_hash , verify_admin_club_access , create_access_token , get_current_user , require_role 
from email_extention import send_email_stub , create_notification , cleanup_past_events

import io, csv , random


app = FastAPI(title="EventHub Secured API")

# Enable CORS for Azure Storage Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, we will replace "*" with your Azure Storage URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (In prod, use Alembic migrations instead)
Base.metadata.create_all(bind=engine)



# ==========================================
# 1. AUTH ENDPOINTS
# ==========================================
@app.post("/api/auth/register")
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):

    # Check if an active, verified user already exists
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")



    # Clear any old, expired, or pending OTPs for this email to avoid conflicts
    db.query(models.OTP).filter(models.OTP.email == user_data.email).delete()

    
    # Generate OTP and hash password
    otp_code = str(random.randint(100000, 999999))
    hashed_pw = get_password_hash(user_data.password)
    
    # Store pending user data in the OTP table instead of the User table
    otp_record = models.OTP(
        email=user_data.email,
        code=otp_code,
        expires_at=datetime.now() + timedelta(minutes=15),
        name=user_data.name,
        role=user_data.role,
        hashed_password=hashed_pw
    )
    db.add(otp_record)
    db.commit()
    send_email_stub(user_data.email, "Your OTP Code", f"Your OTP is {otp_code}. It expires in 15 minutes.", db)
    return {"status": "success", "message": "OTP sent to email. Please verify to create your account."}

@app.post("/api/auth/verify-otp", response_model=schemas.Token)
def verify_otp(data: schemas.OTPVerify, db: Session = Depends(get_db)):
    # Get the latest OTP record for this email
    otp_record = db.query(models.OTP).filter(models.OTP.email == data.email).order_by(models.OTP.id.desc()).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="No OTP found. Please register again.")
    if otp_record.expires_at < datetime.now():
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired. Please register again.")
    if otp_record.code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")
    
    # Safety check: ensure user wasn't created in the meantime
    if db.query(models.User).filter(models.User.email == data.email).first():
        db.query(models.OTP).filter(models.OTP.email == data.email).delete()
        db.commit()
        raise HTTPException(status_code=400, detail="Account already exists. Please login.")
        
    # Create the actual user account using the stored pending data
    new_user = models.User(
        email=otp_record.email,
        name=otp_record.name,
        role=otp_record.role,
        hashed_password=otp_record.hashed_password
    )

    db.add(new_user)
    
    # Clean up ALL OTPs for this email to save space

    db.query(models.OTP).filter(models.OTP.email == data.email).delete()
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(data={"sub": new_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}



@app.get("/api/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user






# Password reset endpoints -
@app.post("/api/auth/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Clear old OTPs for this email
    db.query(models.OTP).filter(models.OTP.email == email).delete()
    otp_code = str(random.randint(100000, 999999))
    
    # Reusing OTP model. Passing "FORGOT" as dummy data to satisfy schema without altering DB
    otp_record = models.OTP(
        email=email,
        code=otp_code,
        expires_at=datetime.now() + timedelta(minutes=15),
        name="FORGOT", role="FORGOT", hashed_password="FORGOT"
    )
    db.add(otp_record)
    db.commit()
    
    send_email_stub(email, "Password Reset OTP", f"Your OTP to reset your password is {otp_code}.", db)
    return {"status": "success", "message": "OTP sent to email."}

@app.post("/api/auth/reset-password")
def reset_password(data: schemas.PasswordReset, db: Session = Depends(get_db)):
    otp_record = db.query(models.OTP).filter(models.OTP.email == data.email).order_by(models.OTP.id.desc()).first()
    
    if not otp_record or otp_record.code != data.otp or otp_record.expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
        
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    user.hashed_password = get_password_hash(data.new_password)
    db.delete(otp_record)
    db.commit()
    
    return {"status": "success", "message": "Password reset successful."} 

# ==========================================
# 2. STUDENT ENDPOINTS
# ==========================================
@app.get("/api/events/upcoming", response_model=list[schemas.EventResponse])
def get_upcoming_events(search_query: str = None, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    cleanup_past_events(db)
    query = db.query(models.Event).filter(models.Event.start_time >= datetime.now())
    
    # Students only see events from clubs they joined
    if user.role == "student":
        joined_club_ids = [c.id for c in user.clubs]
        if not joined_club_ids: return [] 
        query = query.filter(models.Event.club_id.in_(joined_club_ids))
        
    if search_query:
        query = query.filter(models.Event.title.ilike(f"%{search_query}%"))
        
    events = query.all()
    return [{**schemas.EventResponse.model_validate(e).model_dump(), "rsvp_count": len(e.rsvps)} for e in events]

@app.post("/api/events/{event_id}/rsvp")
def rsvp_event(event_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(models.RSVP).filter(models.RSVP.user_id == user.id, models.RSVP.event_id == event_id).first():
        raise HTTPException(status_code=400, detail="Already RSVPed")
   
   
   # Inside rsvp_event function in main.py

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.start_time < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot RSVP to past events")
    



    db.add(models.RSVP(user_id=user.id, event_id=event_id))
    db.commit()
    # <--- PASS DB TO STUB ---
    send_email_stub(user.email, f"RSVP Confirmed: {event.title}", f"You are registered for {event.title}!", db)
    create_notification(db, user.id, f"RSVP Confirmed: You are registered for {event.title}!")
    return {"status": "success", "message": "RSVP confirmed"}

@app.delete("/api/events/{event_id}/rsvp")
def cancel_rsvp(event_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    rsvp = db.query(models.RSVP).filter(models.RSVP.user_id == user.id, models.RSVP.event_id == event_id).first()
    if not rsvp: raise HTTPException(status_code=404, detail="RSVP not found")
    
    # --- NEW GUARDRAILS ---
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event.attendance_submitted:
        raise HTTPException(status_code=400, detail="Cannot cancel RSVP. Attendance for this event has already been finalized.")
    if rsvp.attendance and rsvp.attendance.is_present:
        raise HTTPException(status_code=400, detail="Cannot cancel RSVP. Your attendance has already been marked.")
    # ----------------------

    db.delete(rsvp)
    db.commit()
    create_notification(db, user.id, f"RSVP Cancelled: You are no longer registered for {event.title}.")
    return {"status": "success", "message": "RSVP cancelled"}


@app.get("/api/users/me/rsvps", response_model=list[schemas.RSVPResponse])
def get_my_rsvps(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    cleanup_past_events(db)
    rsvps = (
        db.query(models.RSVP)
        .join(models.Event)
        .filter(
            models.RSVP.user_id == user.id,
            models.Event.start_time >= datetime.now(),
            models.Event.attendance_submitted == False
        )
        .all()
    )
    return rsvps

@app.post("/api/clubs/{club_id}/join")
def join_club(club_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "student": raise HTTPException(400, "Only students can join clubs")
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club: raise HTTPException(404, "Club not found")
    if club not in user.clubs:
        user.clubs.append(club)
        db.commit()
    return {"status": "success"}

@app.delete("/api/clubs/{club_id}/leave")
def leave_club(club_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club: raise HTTPException(404, "Club not found")
    if club in user.clubs:
        user.clubs.remove(club)
        db.commit()
    return {"status": "success", "message": "Left club"}




# ==========================================
# 3. ADMIN / CLUB ENDPOINTS
# ==========================================
@app.get("/api/clubs", response_model=list[schemas.ClubResponse])
def get_clubs(db: Session = Depends(get_db)):
    return db.query(models.Club).all()

@app.post("/api/admin/events")
def create_event(event: schemas.EventCreate, admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    verify_admin_club_access(admin, event.club_id, db)
    if event.start_time < datetime.now(timezone.utc) + timedelta(hours=3):
        raise HTTPException(status_code=400, detail="Event must start at least 3 hours from now")
    

    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    return {"status": "success", "event_id": db_event.id}

@app.delete("/api/admin/events/{event_id}")
def delete_event(event_id: int, admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    verify_admin_club_access(admin, event.club_id, db)
    
    if not event: 
        raise HTTPException(status_code=404, detail="Event not found")
        
    # --- NEW GUARDRAIL ---
    if event.attendance_submitted:
        raise HTTPException(status_code=400, detail="Cannot delete event. Attendance has already been finalized.")
    # ---------------------
        
    create_notification(db, admin.id, f"Event Deleted: You deleted the event '{event.title}'.")
    db.delete(event)
    db.commit()
    return {"status": "success", "message": "Event deleted"}

@app.get("/api/admin/events/{event_id}/rsvps")
def get_event_rsvps(event_id: int, admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    verify_admin_club_access(admin, event.club_id, db)

    if not event: raise HTTPException(404, "Event not found")
    return [{"rsvp_id": r.id, "user_name": r.user.name, "user_email": r.user.email,
             "is_present": r.attendance.is_present if r.attendance else False} for r in event.rsvps]

@app.post("/api/admin/events/{event_id}/attendance")
def mark_attendance(event_id: int, data: schemas.AttendanceMark, admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    verify_admin_club_access(admin, event.club_id, db)
    
    if not event: raise HTTPException(404, "Event not found")
    if event.attendance_submitted:
        raise HTTPException(400, "Attendance has already been submitted and locked for this event")
        
    rsvp = db.query(models.RSVP).filter(models.RSVP.id == data.rsvp_id, models.RSVP.event_id == event_id).first()
    if not rsvp: raise HTTPException(404, "RSVP not found")
    
    if not rsvp.attendance:
        rsvp.attendance = models.Attendance(rsvp_id=rsvp.id, is_present=data.is_present, checked_in_at=datetime.now())
    else:
        rsvp.attendance.is_present = data.is_present
    db.commit()
    
    
    return {"status": "success"}

@app.post("/api/admin/events/{event_id}/submit-attendance")
def submit_attendance(event_id: int, admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    verify_admin_club_access(admin, event.club_id, db)

    if not event: raise HTTPException(status_code=404, detail="Event not found")
    if event.attendance_submitted:
        raise HTTPException(status_code=400, detail="Attendance already submitted for this event")
        
    event.attendance_submitted = True
    db.commit()
    
    # 1. Notify the Admin
    create_notification(db, admin.id, f"Attendance Finalized: Attendance for '{event.title}' has been submitted and locked.")
    
    # 2. Notify ALL students who RSVP'd
    for rsvp in event.rsvps:
        is_present = rsvp.attendance.is_present if rsvp.attendance else False
        status_text = "Present" if is_present else "Absent"
        send_email_stub(
            rsvp.user.email, 
            f"Attendance Finalized: {event.title}", 
            f"Your attendance for {event.title} has been finalized as {status_text}.",
            db # <--- PASS DB TO STUB
        )
        create_notification(
            db, 
            rsvp.user.id, 
            f"Attendance Finalized: Your attendance for {event.title} has been marked as {status_text}."
        )
        
    return {"status": "success", "message": "Attendance submitted and locked"}


@app.get("/api/admin/stats")
def get_club_stats(admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    total_all_time = db.query(models.RSVP).count()
    
    # Calculate real RSVPs for the current month
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_rsvps_month = db.query(models.RSVP).filter(models.RSVP.created_at >= start_of_month).count()
    
    return {
        "total_rsvps_month": total_rsvps_month, 
        "total_all_time": total_all_time, 
        "message": f"{total_rsvps_month} RSVPs this month"
    }




# updating events via admin
@app.put("/api/admin/events/{event_id}")
def update_event(event_id: int, event_update: schemas.EventCreate, admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    
    verify_admin_club_access(admin, db_event.club_id, db)

    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # --- NEW GUARDRAIL ---
    if db_event.attendance_submitted:
        raise HTTPException(status_code=400, detail="Cannot edit event. Attendance has already been finalized.")
    # ---------------------
        
    if event_update.start_time < datetime.now(timezone.utc) + timedelta(hours=3):
        raise HTTPException(status_code=400, detail="Event must start at least 3 hours from now")
        
    for key, value in event_update.model_dump().items():
        setattr(db_event, key, value)
        
    create_notification(db, admin.id, f"Event Updated: You updated the event '{db_event.title}'.")
    db.commit()
    return {"status": "success", "message": "Event updated"}





# ==========================================
# 4. COORDINATOR ENDPOINTS
# ==========================================
@app.get("/api/coordinator/reports")
def get_coordinator_reports(coord: models.User = Depends(require_role("coordinator")), db: Session = Depends(get_db)):
    # 1. Real Events per club
    events_per_club_query = db.query(
        models.Club.name.label("club"),
        func.count(models.Event.id).label("count")
    ).outerjoin(models.Event, models.Club.id == models.Event.club_id)\
     .group_by(models.Club.id, models.Club.name).all()
    
    events_per_club = [{"club": row.club, "count": row.count} for row in events_per_club_query]

    # 2. Real Attendance Rate
    total_attendance_records = db.query(models.Attendance).count()
    total_present = db.query(models.Attendance).filter(models.Attendance.is_present == True).count()
    
    if total_attendance_records > 0:
        attendance_rate = f"{(total_present / total_attendance_records) * 100:.1f}%"
    else:
        attendance_rate = "0.0%"

    # 3. Real Top Events (by RSVP count)
    top_events_query = db.query(
        models.Event.title,
        func.count(models.RSVP.id).label("rsvp_count")
    ).join(models.RSVP, models.Event.id == models.RSVP.event_id)\
     .group_by(models.Event.id, models.Event.title)\
     .order_by(func.count(models.RSVP.id).desc())\
     .limit(3).all()
     
    top_events = [row.title for row in top_events_query]

    # 4. Additional Real Metrics
    total_rsvps = db.query(models.RSVP).count()
    active_events = db.query(models.Event).filter(
        models.Event.attendance_submitted == False,
        models.Event.start_time >= datetime.now()
    ).count()
    completed_events = db.query(models.Event).filter(models.Event.attendance_submitted == True).count()

    return {
        "events_per_club": events_per_club,
        "attendance_rate": attendance_rate,
        "top_events": top_events,
        "total_rsvps": total_rsvps,
        "active_events": active_events,
        "completed_events": completed_events
    }

@app.post("/api/clubs", response_model=schemas.ClubResponse)
def create_club(club_data: schemas.ClubCreate, coord: models.User = Depends(require_role("coordinator")), db: Session = Depends(get_db)):
    if db.query(models.Club).filter(models.Club.name == club_data.name).first():
        raise HTTPException(status_code=400, detail="Club name already exists")
    new_club = models.Club(name=club_data.name)
    db.add(new_club)
    db.commit()
    db.refresh(new_club)
    return new_club

@app.post("/api/clubs/{club_id}/assign-admin")
def assign_admin(club_id: int, admin_email: str, coord: models.User = Depends(require_role("coordinator")), db: Session = Depends(get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club: raise HTTPException(404, "Club not found")
    admin = db.query(models.User).filter(models.User.email == admin_email, models.User.role == "admin").first()
    if not admin: raise HTTPException(404, "Admin user not found")
    if club not in admin.clubs:
        admin.clubs.append(club)
        db.commit()
    return {"status": "success"}


@app.put("/api/clubs/{club_id}")
def update_club(club_id: int, club_data: schemas.ClubCreate, coord: models.User = Depends(require_role("coordinator")), db: Session = Depends(get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club: raise HTTPException(404, "Club not found")
    if db.query(models.Club).filter(models.Club.name == club_data.name, models.Club.id != club_id).first():
        raise HTTPException(400, "Club name already exists")
    club.name = club_data.name
    db.commit()
    return {"status": "success", "message": "Club updated"}

@app.delete("/api/clubs/{club_id}")
def delete_club(club_id: int, coord: models.User = Depends(require_role("coordinator")), db: Session = Depends(get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club: raise HTTPException(404, "Club not found")
    # Clean up relationships to avoid IntegrityError
    club.members.clear()
    events = db.query(models.Event).filter(models.Event.club_id == club_id).all()
    for e in events: db.delete(e)
    db.delete(club)
    db.commit()
    return {"status": "success", "message": "Club deleted"}

@app.delete("/api/clubs/{club_id}/revoke-admin")
def revoke_admin(club_id: int, admin_email: str, coord: models.User = Depends(require_role("coordinator")), db: Session = Depends(get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    admin = db.query(models.User).filter(models.User.email == admin_email, models.User.role == "admin").first()
    if not club or not admin: raise HTTPException(404, "Club or Admin not found")
    if club in admin.clubs:
        admin.clubs.remove(club)
        db.commit()
        return {"status": "success", "message": "Admin access revoked"}
    raise HTTPException(400, "Admin is not assigned to this club")


@app.post("/api/events/{event_id}/feature")
def toggle_featured(event_id: int, coord: models.User = Depends(require_role("coordinator")), db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event: raise HTTPException(404, "Event not found")
    event.is_featured = not event.is_featured
    db.commit()
    return {"status": "success", "is_featured": event.is_featured}



# ===============================================
# 5. NOTIFICATIONS, BOT & EXPORT , Announcements
# ===============================================
@app.get("/api/notifications", response_model=list[schemas.NotificationResponse])
def get_notifications(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Notification).filter(models.Notification.user_id == user.id).order_by(models.Notification.created_at.desc()).all()

@app.post("/api/bot/ask")
def ask_bot(query: schemas.BotQuery):
    q = query.question.lower()
    if "laptop" in q: return {"answer": "Yes! According to Tech Club Guidelines, bring your own laptop."}
    return {"answer": "Please check the specific club handbook for that detail."}

@app.get("/api/admin/events/{event_id}/export-csv")
def export_csv(event_id: int, admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Attended"])
    for r in event.rsvps:
        writer.writerow([r.user.name, r.user.email, "Yes" if r.attendance and r.attendance.is_present else "No"])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=attendance.csv"})


# Announcements

@app.post("/api/clubs/{club_id}/announcements")
def create_announcement(club_id: int, ann_data: schemas.AnnouncementCreate, admin: models.User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    verify_admin_club_access(admin, club_id, db)
    ann = models.Announcement(club_id=club_id, author_id=admin.id, title=ann_data.title, content=ann_data.content)
    db.add(ann)
    db.commit()
    return {"status": "success"}

@app.get("/api/announcements", response_model=list[schemas.AnnouncementResponse])
def get_announcements(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    club_ids = [c.id for c in user.clubs]
    if not club_ids and user.role == "student": return []
        
    query = db.query(models.Announcement).join(models.Club)
    if user.role != "coordinator":
        query = query.filter(models.Announcement.club_id.in_(club_ids))
        
    anns = query.order_by(models.Announcement.created_at.desc()).all()
    
    result = []
    for a in anns:
        res = schemas.AnnouncementResponse.model_validate(a).model_dump()
        res["club_name"] = a.club.name
        result.append(res)
    return result



# toggling the email send logic:
@app.put("/api/system/toggle-email")
def toggle_email(toggle : bool, db : Session = Depends(get_db)):
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_quota = db.query(models.EmailQuota).filter(models.EmailQuota.date == today_str).first()
    
    if not today_quota:
        today_quota = models.EmailQuota(date=today_str, count=0)
        db.add(today_quota)
        db.commit()
        db.refresh(today_quota)

    today_quota.is_valid = toggle
        
    db.commit()
    return {"Email Recieving Status":today_quota.is_valid}

# ==========================================
# SYSTEM / AUTO-CALLED ENDPOINTS
# ==========================================
# We can trigger this via an Azure Logic App, Cron Job, or GitHub Actions every hour

@app.post("/api/system/send-reminders")
def send_24h_reminders(db: Session = Depends(get_db)):
    now = datetime.now()
    window_start = now + timedelta(hours=23)
    window_end = now + timedelta(hours=25)
    
    # should only be triggered once a day. else raise an error



    # Find events happening in ~24h that haven't had reminders sent yet
    events = db.query(models.Event).filter(
        models.Event.start_time.between(window_start, window_end),
        models.Event.reminder_sent == False
    ).all()
    
    for event in events:
        for rsvp in event.rsvps:
            send_email_stub(
                rsvp.user.email,
                f"Reminder: {event.title} is tomorrow!",
                f"Don't forget, {event.title} is starting soon.",
                db
            )
        event.reminder_sent = True
        
    if events:
        db.commit()
        
    return {"status": "success", "reminders_sent": True}





# ==========================================
# SEED DATA
# ==========================================
@app.on_event("startup")
def seed_data():
    db = next(get_db())
    if db.query(models.Club).count() == 0:
        db.add_all([models.Club(name="Tech Club"), models.Club(name="Lit Club")])
        db.commit()
        db.add_all([
            models.Event(title="AI/ML Hackathon", club_id=1, start_time=datetime(2026, 7, 10, 17, 0), description="Build AI.", rules="Bring laptop.", is_featured=True),
            models.Event(title="Debate Championship", club_id=2, start_time=datetime(2026, 7, 13, 15, 0), description="Debate.", rules="Formal attire.", is_featured=False)
        ])
        db.commit()
    db.close()