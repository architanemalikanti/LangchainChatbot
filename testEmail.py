# clean_email_test.py
import os
from dotenv import load_dotenv

# Import your updated function
from tools import generate_and_send_verification_code

load_dotenv()

print("Testing clean email...")
result = generate_and_send_verification_code.invoke({"email": "apn32@cornell.edu"})
print(f"Result: {result}")