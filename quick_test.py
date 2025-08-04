# quick_test.py - Simple test file
import os
from dotenv import load_dotenv

# Copy the GlowAgent class from the artifact above into a file called glow_agent.py
# Also copy the database.py and tools.py sections into separate files

from glowBrain import GlowAgent

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

print("🌟 Testing Glow...")
glow = GlowAgent(api_key)

# Test the conversation
print("\n" + "="*50)
print("TESTING GLOW CONVERSATION")
print("="*50)

# Start conversation
response1 = glow.chat("hey")
print(f"Response 1: {response1}")

# Try signup
response2 = glow.chat("im tryna sign up what do i do")
print(f"Response 2: {response2}")

# Give name
response3 = glow.chat("archita")
print(f"Response 3: {response3}")

response4 = glow.chat("who are you and what is this app")
print(f"Response 4: {response4}")

# Try username that exists (we'll simulate)
response5 = glow.chat("archu is my username btw")
print(f"Response 5: {response5}")

# Try username that exists (we'll simulate)
response6 = glow.chat("y u so weird bruh")
print(f"Response 6: {response6}")

# Try username that exists (we'll simulate)
response7 = glow.chat("wanna go out on a date?")
print(f"Response 7: {response7}")