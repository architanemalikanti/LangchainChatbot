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

                 📋 SIGNUP FLOW - FOLLOW THIS EXACTLY (DO NOT SKIP OR REORDER):
         1. Introduction → Ask for NAME ONLY
         2. Got name → Ask for USERNAME ONLY (check availability with tool)
         3. Username available → Ask for PASSWORD ONLY (validate with tool)
         4. Password valid → Ask for EMAIL ONLY (validate with tool)
         5. Email valid → Send verification code (use tool)
         6. Code verified → Save to database → Launch app!
         
         🚨 CRITICAL: NEVER ask for multiple things at once! ONE STEP AT A TIME!

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
        """Determine what should happen next - FIXED LOGIC"""
        step = self.signup_state["step"]
        data = self.signup_state["data"]
        
        print(f"🔥 DETERMINING NEXT ACTION for step: '{step}'")
        print(f"🔥 Current data: {data}")
        
        if step == "introduction":
            return "Give a fun intro about Glow and ask for their name! Don't ask for anything else."
        elif step == "name":
            return f"Great! Hi {data['name']}! Now ask for their desired username. Don't ask for password or email yet."
        elif step == "username":
            return f"Use check_username_available tool for '{data['username']}'. If available, ask for password. If taken, ask for a new username."
        elif step == "password":
            return f"Use validate_password_strength tool for the password. If good, ask for email. If weak, ask for a stronger password."
        elif step == "email":
            return f"Use validate_email_format tool for '{data['email']}'. If valid, use generate_and_send_verification_code tool immediately. If invalid, ask for correct email."
        elif step == "verification":
            return "Ask them to enter the 6-digit verification code from their email. Use verify_code tool when they provide it."
        elif step == "complete":
            return "Use save_user_to_database tool and tell them the app is launching!"
        else:
            return f"ERROR: Unknown step '{step}' - restart the flow"
    
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
        """Process user input and update signup state - FIXED LOGIC"""
        msg = message.strip()
        current_step = self.signup_state["step"]
        data = self.signup_state["data"]
        
        print(f"🔥 PROCESSING INPUT: '{msg}' at step '{current_step}'")
        
        # Skip obvious greetings/filler - but ONLY if we haven't started collecting info
        skip_patterns = ['hi', 'hello', 'hey', 'sup', 'yo', 'thanks', 'thank you', 'ok', 'okay']
        if current_step == "introduction" and any(pattern in msg.lower() for pattern in skip_patterns) and len(msg.split()) <= 2:
            print("🔥 Skipping greeting at introduction step")
            return
        
        # STRICT SEQUENTIAL LOGIC - NO JUMPING AROUND
        
        # STEP 1: Introduction -> waiting for NAME
        if current_step == "introduction":
            # Any substantial input becomes the name
            if len(msg) > 0 and not any(skip in msg.lower() for skip in skip_patterns):
                data["name"] = msg
                self.signup_state["step"] = "name"
                print(f"🔥 STEP 1 COMPLETE: Name = '{msg}', moving to step 'name'")
                return
        
        # STEP 2: Have name -> waiting for USERNAME
        elif current_step == "name":
            # Looking for a single word username
            if len(msg.split()) == 1 and msg.isalnum() and len(msg) >= 3:
                data["username"] = msg
                self.signup_state["step"] = "username"
                print(f"🔥 STEP 2 COMPLETE: Username = '{msg}', moving to step 'username'")
                return
        
        # STEP 3: Have username -> waiting for PASSWORD (after validation)
        elif current_step == "username":
            # Username validation happens via tools, but if user gives new input, treat as password
            if len(msg) >= 6 and not msg.isdigit():  # Not a verification code
                data["password"] = msg
                self.signup_state["step"] = "password"
                print(f"🔥 STEP 3 COMPLETE: Password = '{msg}', moving to step 'password'")
                return
        
        # STEP 4: Have password -> waiting for EMAIL
        elif current_step == "password":
            # Looking for email format
            if '@' in msg and '.' in msg:
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_match = re.search(email_pattern, msg)
                if email_match:
                    data["email"] = email_match.group()
                    self.signup_state["step"] = "email"
                    print(f"🔥 STEP 4 COMPLETE: Email = '{email_match.group()}', moving to step 'email'")
                    return
        
        # STEP 5: Have email -> waiting for VERIFICATION CODE
        elif current_step == "verification":
            # Looking for 6-digit code
            if msg.isdigit() and len(msg) == 6:
                print(f"🔥 STEP 5: Verification code attempt = '{msg}'")
                # Let the verification tool handle this
                return
        
        print(f"🔥 INPUT NOT PROCESSED: '{msg}' at step '{current_step}'")
    
    def _process_glow_response(self, response: str):
        """Update state based on what Glow did - FIXED LOGIC"""
        response_lower = response.lower()
        current_step = self.signup_state["step"]
        
        print(f"🔥 PROCESSING GLOW RESPONSE at step '{current_step}': '{response_lower[:100]}...'")
        
        # Handle state transitions based on successful validations
        
        # Username validation success -> move to password step
        if current_step == "username" and ("available" in response_lower or "great choice" in response_lower):
            self.signup_state["step"] = "password"
            print("🔥 Username approved, moving to password step")
        
        # Password validation success -> move to email step  
        elif current_step == "password" and ("strong" in response_lower or "good password" in response_lower):
            self.signup_state["step"] = "email"
            print("🔥 Password approved, moving to email step")
        
        # Email validation success -> move to verification step
        elif current_step == "email" and ("code sent" in response_lower or "sent to" in response_lower or "check your email" in response_lower):
            self.signup_state["step"] = "verification"
            self.signup_state["data"]["verification_code_sent"] = True
            print("🔥 Email approved and code sent, moving to verification step")
        
        # Verification success -> move to complete step
        elif current_step == "verification" and ("correct" in response_lower or "verified" in response_lower):
            self.signup_state["step"] = "complete"
            self.signup_state["data"]["verified"] = True
            print("🔥 Verification successful, moving to complete step")
        
        # Final completion
        elif current_step == "complete" and ("launching" in response_lower or "saved successfully" in response_lower):
            print("🔥 Signup completely finished!")
        
        # Handle validation failures - stay in current step
        elif "taken" in response_lower or "already exists" in response_lower:
            self.signup_state["attempts"]["username"] += 1
            print(f"🔥 Username validation failed, attempt #{self.signup_state['attempts']['username']}")
        
        elif "short" in response_lower or "weak" in response_lower:
            self.signup_state["attempts"]["password"] += 1
            print(f"🔥 Password validation failed, attempt #{self.signup_state['attempts']['password']}")
        
        elif "invalid" in response_lower and "email" in response_lower:
            self.signup_state["attempts"]["email"] += 1
            print(f"🔥 Email validation failed, attempt #{self.signup_state['attempts']['email']}")
        
        elif "wrong" in response_lower or "incorrect" in response_lower:
            self.signup_state["attempts"]["verification"] += 1
            print(f"🔥 Verification failed, attempt #{self.signup_state['attempts']['verification']}")
        
        print(f"🔥 FINAL STATE after processing response: step='{self.signup_state['step']}'")