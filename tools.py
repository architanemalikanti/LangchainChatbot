# tools.py - Glow's toolkit
import random
import re
from sqlalchemy.orm import Session
from database import SessionLocal, User, VerificationCode
from langchain.tools import tool

@tool
def check_username_available(username: str) -> str:
    """Check if a username is available"""
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return "taken"
        else:
            return "available"
    finally:
        db.close()

@tool 
def validate_email_format(email: str) -> str:
    """Check if email format is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return "valid"
    else:
        return "invalid"

@tool
def generate_and_send_verification_code(email: str) -> str:
    """Generate a 6-digit code and 'send' it via email"""
    # Generate random 6-digit code
    code = str(random.randint(100000, 999999))
    
    # Store in database
    db = SessionLocal()
    try:
        # Remove old codes for this email
        db.query(VerificationCode).filter(VerificationCode.email == email).delete()
        
        # Add new code
        new_code = VerificationCode(email=email, code=code)
        db.add(new_code)
        db.commit()
        
        # In real app, you'd send email here
        # For now, we'll just print it (like a fake email)
        print(f"📧 FAKE EMAIL TO {email}: Your verification code is {code}")
        
        return f"sent_code_{code}"  # Return the code so we can see it
    finally:
        db.close()

@tool
def verify_code(email: str, entered_code: str) -> str:
    """Check if the verification code is correct"""
    db = SessionLocal()
    try:
        code_record = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code == entered_code,
            VerificationCode.used == False
        ).first()
        
        if code_record:
            # Mark as used
            code_record.used = True
            db.commit()
            return "correct"
        else:
            return "incorrect"
    finally:
        db.close()

@tool
def save_user_to_database(name: str, username: str, password: str, email: str) -> str:
    """Save the completed user signup to database"""
    db = SessionLocal()
    try:
        # Hash the password (like putting it in a secret code)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        new_user = User(
            name=name,
            username=username, 
            password_hash=password_hash,
            email=email,
            verified=True
        )
        db.add(new_user)
        db.commit()
        return "saved_successfully"
    finally:
        db.close()

# List of all Glow's tools
glow_tools = [
    check_username_available,
    validate_email_format, 
    generate_and_send_verification_code,
    verify_code,
    save_user_to_database
]