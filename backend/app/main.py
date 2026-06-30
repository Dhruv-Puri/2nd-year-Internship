from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from . import models, schema, database, auth

app = FastAPI(title="EventHub API")

# Enable CORS for Azure Storage Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your Azure Storage URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (In prod, use Alembic migrations instead)
models.Base.metadata.create_all(bind=database.engine)

# --- MINI EXTENSION: Notifications ---
def send_email_notification(email: str, subject: str, message: str):
    # stub for sending email (will integrate SendGrid API here later)
    print(f"Sending Email to {email} | Subject: {subject} | Body: {message}")


# ENDPOINTS 

# Register User
@app.post("/register", response_model=schema.UserResponse)
def register(user: schema.UserCreate, db: Session = Depends(database.get_db)):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login
@app.post("/login", response_model=schema.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

