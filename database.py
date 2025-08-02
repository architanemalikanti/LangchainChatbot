# database.py - This is like building Glow's filing cabinet
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import hashlib

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    username = Column(String(50), unique=True)  # This makes sure no duplicates!
    password_hash = Column(String(200))  # We store password safely
    email = Column(String(100), unique=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class VerificationCode(Base):
    __tablename__ = 'verification_codes'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    code = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)

# Create the database (like building the filing cabinet)
engine = create_engine('sqlite:///glow_app.db')  # Creates a file called glow_app.db
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)