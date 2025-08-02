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
response2 = glow.chat("im tryna sign up")
print(f"Response 2: {response2}")

# Give name
response3 = glow.chat("archita")
print(f"Response 3: {response3}")

# Try username that exists (we'll simulate)
response4 = glow.chat("archu")
print(f"Response 4: {response4}")