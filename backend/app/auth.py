from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
import os
from dotenv import load_dotenv


load_dotenv() # loading the env variables

SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = os.getenv("ALGORITHM") 
ACCESS_TOKEN_EXPIRE_MINUTES = 60



# fallback logic if the SECRET_KEY is not initialised in the .env file
if not SECRET_KEY or not ALGORITHM: 
    raise ValueError("CRITICAL ERROR: environment variable is not set!")



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def get_password_hash(password): return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError: raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None: raise credentials_exception

    return user

def require_role(required_role: str):
    async def role_checker(user: models.User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(status_code=403, detail="Not authorized for this action")
        return user
    return role_checker


def verify_admin_club_access(admin: models.User, club_id: int, db: Session):
    admin_club_ids = [c.id for c in admin.clubs]
    if club_id not in admin_club_ids:
        raise HTTPException(status_code=403, detail="Not authorized to manage this club's events")