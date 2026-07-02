import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()  # only for local .env file will not be used when migrating to cloud , comes with fastapi[standard] but can also be explicitly installed

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL: # if cannot find any url in the environment variables
    raise ValueError("DATABASE_URL environment variable is not set!")
    

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()