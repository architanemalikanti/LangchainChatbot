# database.py - This is like building Glow's filing cabinet
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import hashlib
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    username = Column(String(50), unique=True) # This makes sure no duplicates!
    password_hash = Column(String(200)) # We store password safely
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
# Use DATABASE_URL from environment if available (production), otherwise use SQLite (local development)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///glow_app.db')

# Fix for SQLite file path in production (if using SQLite)
if DATABASE_URL.startswith('sqlite:///') and not DATABASE_URL.startswith('sqlite:////'):
    # Make sure SQLite file is in a writable directory
    DATABASE_URL = 'sqlite:////tmp/glow_app.db'

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)