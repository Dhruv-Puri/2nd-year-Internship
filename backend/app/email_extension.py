import app.models as models
import os
from sqlalchemy.orm import Session 
from datetime import datetime
from dotenv import load_dotenv


load_dotenv() # loading the environment variables


# getting the connection String - 
connection_string = os.getenv("ACS_CONNECTION_STRING")
sender_email = os.getenv("SENDER_EMAIL")


# ==========================================
# EMAIL STUBS (Mini-Extension)
# ==========================================


def send_email_stub(reciever_email: str, subject: str, body: str, db: Session):
    # --- RATE LIMITING LOGIC ---
    today_str = datetime.now().strftime("%Y-%m-%d")
    quota = db.query(models.EmailQuota).filter(models.EmailQuota.date == today_str).first()
    if not quota:
        quota = models.EmailQuota(date=today_str, count=0)
        db.add(quota)
    
    if quota.count >= 10 or quota.is_valid == False :
        print(f"Email quota exceeded for {today_str}. Skipping email to {reciever_email}.")
        print(f"\n{'='*50}\n📧 EMAIL STUB TRIGGERED (QUOTA EXCEEDED)\nTo: {reciever_email}\nSubject: {subject}\nBody: {body}\n{'='*50}\n")
        return

    try:
        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(connection_string)
        message = {
             "senderAddress": sender_email,
             "recipients":  {
                 "to": [{"address": reciever_email}],
             },
             "content": {
                 "subject": subject,
                 "plainText": body,
             }
         }
        poller = client.begin_send(message)
        result = poller.result()
        print("Email sent successfully!")
        
        quota.count += 1
        db.commit()
    except Exception as ex:
        print(f"\n\n{"*"*50}\n\nError sending email: {ex}\n\n{"*"*50}\n\n")
        

    print(f"\n{'='*50}\n📧 EMAIL STUB TRIGGERED\nTo: {reciever_email}\nSubject: {subject}\nBody: {body}\n{'='*50}\n")


# Notifications - 

def create_notification(db: Session, user_id: int, message: str):
    notif = models.Notification(user_id=user_id, message=message)
    db.add(notif)
    db.commit()


def cleanup_past_events(db: Session):
    past_events = db.query(models.Event).filter(models.Event.start_time < datetime.now()).all()
    for event in past_events:
        # Notify users who RSVPed that they missed the event
        for rsvp in event.rsvps:
            create_notification(db, rsvp.user_id, f"Event Missed: The time for {event.title} has passed.")
        db.delete(event)
    if past_events:
        db.commit()