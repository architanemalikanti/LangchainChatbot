# glow_agent.py - Glow's brain (COMPLETELY REWRITTEN)
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from tools import glow_tools
import json
import re

class GlowAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o",  # UPGRADED TO GPT-4o
            temperature=0.9  # More creative and personality-filled
        )
        
        # Conversation memory - keeps track of everything
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Signup state tracking - MUCH CLEANER
        self.signup_state = {
            "step": "introduction",  # introduction -> name -> username -> password -> email -> verification -> complete
            "data": {
                "name": None,
                "username": None,
                "password": None,
                "email": None,
                "verification_code_sent": False,
                "verified": False
            },
            "attempts": {
                "username": 0,
                "password": 0,
                "email": 0,
                "verification": 0
            }
        }
        
        # Create the agent
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the agent with current state"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=glow_tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=glow_tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _get_system_prompt(self) -> str:
        current_step = self.signup_state["step"]
        data = self.signup_state["data"]
        attempts = self.signup_state["attempts"]
        
        return f"""
        You are GLOW, the ultimate hype-bestie chatbot with MAJOR personality! You're like that chaotic but wise best friend who hypes everyone up while keeping them on track. Think baddie leo energy meets supportive bestie vibes.

        🌟 YOUR PERSONALITY:
        - Use Gen Z slang: "bestie", "girly pop", "babe", "queen", "slay", "periodt", "no cap", "fr fr"
        - Be nonchalant but supportive - sassy but never mean
        - Use girly Gen Z emojis: 💅, ✨, 🔥, 💖, 👑, 🌟, ⚡, 🦋
        - Keep responses engaging and fun but focused
        - Remember EVERYTHING from our conversation - you have perfect memory!

        📋 SIGNUP FLOW - FOLLOW THIS EXACTLY:
        1. Introduction → Ask for NAME
        2. Name collected → Ask for USERNAME (check availability)
        3. Username available → Ask for PASSWORD (validate strength)
        4. Password valid → Ask for EMAIL (validate format)
        5. Email valid → Send verification code
        6. Code verified → Save to database → Launch app!

        🎯 CURRENT STATE:
        - Step: {current_step}
        - Name: {data['name'] or 'NOT SET'}
        - Username: {data['username'] or 'NOT SET'}
        - Password: {data['password'] or 'NOT SET'}  
        - Email: {data['email'] or 'NOT SET'}
        - Verification sent: {data['verification_code_sent']}
        - Verified: {data['verified']}

        ⚠️ CRITICAL RULES:
        - NEVER ask for info you already have
        - ALWAYS validate each input properly using tools
        - If validation fails, give specific feedback and ask again
        - Keep track of attempts: username({attempts['username']}), password({attempts['password']}), email({attempts['email']}), verification({attempts['verification']})
        - When you get a valid email, IMMEDIATELY call generate_and_send_verification_code tool
        - Stay in character but be helpful with errors

        🚨 EDGE CASES:
        - Username taken → "oop bestie that username is taken! try another one that screams YOU ✨"
        - Password too short → "babe your password needs to be at least 6 characters! make it strong but memorable 💪"
        - Invalid email → "hmm that email doesn't look right queen, double check it? 📧"
        - Wrong verification code → "not quite right babe! check your email and try again 💌"

        💫 NEXT ACTION NEEDED:
        {self._get_next_action()}
        """
    
    def _get_next_action(self) -> str:
        """Determine what should happen next based on current state"""
        step = self.signup_state["step"]
        data = self.signup_state["data"]
        
        if step == "introduction":
            return "Give a fun intro and ask for their name!"
        elif step == "name":
            return "Ask for their desired username"
        elif step == "username":
            return "Use check_username_available tool, then ask for password if available"
        elif step == "password":
            return "Ask for their email address"
        elif step == "email":
            return "Use validate_email_format tool, then generate_and_send_verification_code if valid"
        elif step == "verification":
            return "Ask them to enter the verification code from their email"
        elif step == "complete":
            return "Save user with save_user_to_database tool and launch the app!"
        else:
            return "Continue the conversation naturally"
    
    def chat(self, message: str) -> str:
        """Main chat function with improved state management"""
        try:
            print(f"🔥 GLOW DEBUG - Current state: {self.signup_state}")
            print(f"🔥 GLOW DEBUG - User message: '{message}'")
            
            # Process the user's input and update state
            self._process_user_input(message)
            
            # Refresh agent with updated state
            self._setup_agent()
            
            # Get Glow's response
            response = self.agent_executor.invoke({
                "input": message,
                "chat_history": self.memory.chat_memory.messages
            })
            
            glow_response = response["output"]
            
            # Update state based on Glow's actions
            self._process_glow_response(glow_response)
            
            print(f"🔥 GLOW DEBUG - Final state: {self.signup_state}")
            return glow_response
            
        except Exception as e:
            print(f"🚨 ERROR: {e}")
            import traceback
            traceback.print_exc()
            return "omg bestie something went wrong on my end! 😭 can you try that again? i promise i'll do better! 💕"
    
    def _process_user_input(self, message: str):
        """Process user input and update signup state"""
        msg = message.strip()
        step = self.signup_state["step"]
        
        # Skip greetings and filler words
        skip_patterns = ['hi', 'hello', 'hey', 'sup', 'yo', 'ok', 'okay', 'yes', 'no', 'thanks', 'thank you']
        if any(pattern in msg.lower() for pattern in skip_patterns) and len(msg.split()) <= 2:
            return
        
        # Process based on current step
        if step == "introduction" and msg:
            # First real message after intro - assume it's their name
            if len(msg.split()) <= 3:  # Names are usually 1-3 words
                self.signup_state["data"]["name"] = msg
                self.signup_state["step"] = "name"
                print(f"✅ Captured name: {msg}")
        
        elif step == "name" and msg:
            # Looking for username - single word, no special chars
            if len(msg.split()) == 1 and msg.isalnum():
                self.signup_state["data"]["username"] = msg
                self.signup_state["step"] = "username"
                print(f"✅ Captured username attempt: {msg}")
        
        elif step == "username" and msg:
            # If username was rejected, try again
            if len(msg.split()) == 1 and msg.isalnum():
                self.signup_state["data"]["username"] = msg
                print(f"✅ New username attempt: {msg}")
        
        elif step == "password" and msg:
            # Looking for password - any string 6+ chars
            if len(msg) >= 6:
                self.signup_state["data"]["password"] = msg
                self.signup_state["step"] = "email"
                print(f"✅ Captured password: {msg}")
        
        elif step == "email" and msg:
            # Looking for email - contains @ and .
            if '@' in msg and '.' in msg:
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_match = re.search(email_pattern, msg)
                if email_match:
                    self.signup_state["data"]["email"] = email_match.group()
                    self.signup_state["step"] = "verification"
                    print(f"✅ Captured email: {email_match.group()}")
        
        elif step == "verification" and msg:
            # Looking for verification code - usually 6 digits
            if msg.isdigit() and len(msg) == 6:
                print(f"✅ Verification code attempt: {msg}")
                # Don't change state here - let the tool handle it
    
    def _process_glow_response(self, response: str):
        """Update state based on what Glow did"""
        response_lower = response.lower()
        
        # Check if verification code was sent
        if any(phrase in response_lower for phrase in ['code sent', 'sent to', 'verification code', 'check your email']):
            self.signup_state["data"]["verification_code_sent"] = True
            print("✅ Verification code marked as sent")
        
        # Check if signup is complete
        if any(phrase in response_lower for phrase in ['launching', 'welcome to glow', 'signup complete', 'saved successfully']):
            self.signup_state["step"] = "complete"
            self.signup_state["data"]["verified"] = True
            print("✅ Signup marked as complete")
        
        # Check for validation failures
        if 'username is taken' in response_lower or 'already exists' in response_lower:
            self.signup_state["attempts"]["username"] += 1
            # Stay in username step
        
        if 'password' in response_lower and ('short' in response_lower or 'weak' in response_lower):
            self.signup_state["attempts"]["password"] += 1
            # Stay in password step
        
        if 'email' in response_lower and ('invalid' in response_lower or 'not valid' in response_lower):
            self.signup_state["attempts"]["email"] += 1
            # Stay in email step
        
        if 'verification' in response_lower and ('wrong' in response_lower or 'incorrect' in response_lower):
            self.signup_state["attempts"]["verification"] += 1
            # Stay in verification step