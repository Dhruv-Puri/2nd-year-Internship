from fastapi import FastAPI, Depends, HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.security import OAuth2PasswordRequestForm

from . import models, schema, database, auth

app = FastAPI(title="EventHub API")

# Enable CORS for Azure Storage Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, we will replace "*" with your Azure Storage URL
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
@app.post("/api/auth/register", response_model=schema.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schema.UserCreate, db: Session = Depends(database.get_db)):
    
    # 1. Extract and validate email domain
    try:
        email_domain = user.email.split("@")[1]
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Invalid email format"
        )

    # 2. Check if domain is allowed
    domain_exists = db.query(models.State).filter(models.State.valid_email_domains == email_domain).first()
    if not domain_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email domain is not allowed"
        )
        
    # 3. Hash password and create user object
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password, role=user.role)
    
    # 4. Safely commit to the database
    try:
        db.add(db_user)
        db.commit()  # Database integrity checks (like Unique Constraints) trigger HERE
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()  # Crucial: roll back the failed transaction
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="User with this email already exists"
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
    return db_user



# Login
@app.post("/api/auth/login", response_model=schema.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first() # here the username field contains email
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}



#Fetching current User
@app.get("/api/users/me", response_model=schema.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    This endpoint is protected. 
    It requires a valid JWT token in the Authorization header.
    """
    return current_user


