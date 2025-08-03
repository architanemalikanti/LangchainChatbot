# tools.py - Glow's toolkit
import hashlib
import random
import re
from sqlalchemy.orm import Session
from database import SessionLocal, User, VerificationCode
from langchain.tools import tool
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

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
    """Generate a 6-digit code and send it via email"""
    
    # Clean the email parameter to remove any problematic characters
    email = email.replace('\xa0', '').replace('\u00a0', '').strip()
    
    # Step 1: Generate the secret code
    code = str(random.randint(100000, 999999))
    
    # Step 2: Store code in database (same as before)
    db = SessionLocal()
    try:
        # Remove old codes for this email
        db.query(VerificationCode).filter(VerificationCode.email == email).delete()
        
        # Add new code
        new_code = VerificationCode(email=email, code=code)
        db.add(new_code)
        db.commit()
        
        # Step 3: NOW SEND THE REAL EMAIL! 
        success = send_verification_email(email, code)
        
        if success:
            print(f"✅ Real email sent to {email}")
            return "sent"
        else:
            print(f"❌ Failed to send email to {email}")
            return "failed"
            
    finally:
        db.close()

def send_verification_email(to_email: str, code: str) -> bool:
    try:
        load_dotenv()
        
        sender_email = os.getenv("GLOW_EMAIL")
        sender_password = os.getenv("GLOW_EMAIL_PASSWORD")
        
        # Clean credentials of any problematic Unicode characters
        if sender_email:
            sender_email = sender_email.replace('\xa0', '').replace('\u00a0', '').strip()
        
        if sender_password:
            sender_password = sender_password.replace('\xa0', '').replace('\u00a0', '').strip()
        
        if not sender_email or not sender_password:
            print("Missing email credentials!")
            return False
        
        # Create a simple MIME text message with explicit UTF-8 encoding
        body = f"bestieeee your glow code is {code}\nenter it rn so we can get this glow up started\n\nok see u inside babe\n\n- glow"
        
        # Remove any problematic Unicode characters
        import unicodedata
        body = unicodedata.normalize('NFKD', body)
        body = ''.join(c for c in body if ord(c) < 128)  # Keep only ASCII characters
        
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "your glow code is here bestie"
        
        # Send email
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            # Get the message as bytes with explicit UTF-8 encoding
            message_bytes = msg.as_bytes()
            server.sendmail(sender_email, to_email, message_bytes)
        
        print("Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"Email error: {e}")
        return False


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