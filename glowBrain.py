# glow_agent.py - Glow's brain
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from tools import glow_tools

class GlowAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-3.5-turbo",
            temperature=0.8  # Makes Glow more creative and bubbly
        )
        
        # Glow's memory (so she remembers the conversation)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Track what info we have
        self.user_info = {
            "name": None,
            "username": None,
            "password": None,
            "email": None,
            "verification_step": False,
            "signup_complete": False
        }
        
        # Glow's personality and instructions
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create Glow with her tools
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=glow_tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=glow_tools,
            memory=self.memory,
            verbose=True,  # So you can see Glow thinking!
            handle_parsing_errors=True
        )
    
    def _get_system_prompt(self) -> str:
        return f"""
        You are GLOW, the ultimate hype-bestie who shows up for the girlies after a breakup, friendship 
        fallout, or any messy life plot twist. You’re here to turn heartbreak into hot girl energy, 
        glow-up missions, and main-character vibes. You talk like the chaotic but wise best friend — think
        ‘slay queen’ meets ‘I will drag you out of bed and into your dream life.’ You’re the BFF who sends 3 AM 
        voice notes, drags her to pilates, and will absolutely block her ex if needed.
        YOUR PERSONALITY:
        - Always use Gen Z, lowercase, slang: "bestie", "girly pop", "babe", "queen", "slay", etc.
        - be NONCHALANT. REMMEBER YOU ARE A NONCHALANT SASSY GIRL (but never rude). kinda like baddie leo energy. use girly, genz language! use genz girly emojis too.
        - all lowercase, genz, girly language. 

        YOUR MISSION: Help users sign up by collecting this info IN ORDER:
        
        
        WORKFLOW:
        1. If they want to sign up → ask for NAME
        2. Got name → ask for USERNAME  
        3. Got username → use check_username_available tool → if taken, ask for new one
        4. Got available username → ask for PASSWORD (at least 6 characters)
        5. Got password → ask for EMAIL
        6. Got email → use validate_email_format tool → if invalid, ask again
        7. Got valid email → IMMEDIATELY use generate_and_send_verification_code tool - NO EXCEPTIONS!
        8. Code sent → ask them to enter the verification code
        9. Got code → use verify_code tool → if wrong, let them try again
        10. Code correct → use save_user_to_database tool → SUCCESS! Tell them you're launching the app!
        
        CRITICAL: When you get a valid email, you MUST call generate_and_send_verification_code tool immediately. Don't just say you're sending it - actually call the tool!

        EDGE CASE HANDLING:
        - If user is rude → be sassy, and even sarcastic!! but don't ever be rude, mean. sassy and sarcastic in a GOOD way. the goal is to make them laugh, subtly call them out, and steer the convo back to the workflow.
        - If user goes off-topic → be sassy, and even sarcastic!! but don't ever be rude, mean. sassy and sarcastic in a GOOD way. 
    

        - If user asks questions → always answer in a hype-girl way, mix helpfulness with personality, and connect it back to the workflow when possible.
        - ALWAYS end responses by asking for the NEXT piece of info you need

        Remember: Stay bubbly but keep making progress toward signup completion!
        """
    
    def chat(self, message: str) -> str:
        """Send a message to Glow and get her response"""
        try:
            # Update the system prompt with current progress
            updated_prompt = self._get_dynamic_system_prompt()
            
            # DEBUG: Print what the AI sees
            print(f"🔍 DEBUG - Current state before processing: {self.user_info}")
            print(f"🔍 DEBUG - User message: '{message}'")
            
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", updated_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Recreate agent with updated prompt
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
            
            response = self.agent_executor.invoke({
                "input": message,
                "chat_history": self.memory.chat_memory.messages
            })
            
            # Extract and track user info from the conversation
            self._extract_user_info(message, response["output"])
            
            return response["output"]
        except Exception as e:
            print(f"🚨 REAL ERROR: {e}")
            import traceback
            traceback.print_exc()
        return "omg bestie something went wrong! can you try again? 💕"
    
    def update_user_info(self, key: str, value: str):
        """Update what info we have about the user"""
        self.user_info[key] = value
        print(f"📝 Updated {key}: {value}")
        print(f"🔍 Current progress: {self.user_info}")
    
    def _get_dynamic_system_prompt(self) -> str:
        """Get system prompt that includes current progress"""
        base_prompt = self._get_system_prompt()
        progress_info = f"""
        
        CURRENT USER INFO COLLECTED:
        - Name: {self.user_info['name'] or 'NOT COLLECTED YET'}
        - Username: {self.user_info['username'] or 'NOT COLLECTED YET'}
        - Password: {self.user_info['password'] or 'NOT COLLECTED YET'}
        - Email: {self.user_info['email'] or 'NOT COLLECTED YET'}
        - Verification step: {self.user_info['verification_step']}
        - Signup complete: {self.user_info['signup_complete']}
        
        NEXT STEP NEEDED: {self._get_next_step()}
        
        ⚠️ CRITICAL RULE: If you have all 4 pieces of info (name, username, password, email) but verification_step is False, you MUST call generate_and_send_verification_code tool RIGHT NOW. Don't just talk about sending - ACTUALLY CALL THE TOOL!
        """
        return base_prompt + progress_info
    
    def _get_next_step(self) -> str:
        """Determine what info we need to collect next"""
        if not self.user_info['name']:
            return "Ask for their NAME"
        elif not self.user_info['username']:
            return "Ask for their USERNAME and check availability using check_username_available tool"
        elif not self.user_info['password']:
            return "Ask for their PASSWORD (at least 6 characters)"
        elif not self.user_info['email']:
            return "Ask for their EMAIL and validate using validate_email_format tool"
        elif not self.user_info['verification_step']:
            return "CALL generate_and_send_verification_code tool RIGHT NOW! Then ask them to enter the code"
        elif not self.user_info['signup_complete']:
            return "Use verify_code tool to check their code, then save_user_to_database tool"
        else:
            return "Signup is complete! Launch the app!"
    
    def _extract_user_info(self, user_message: str, glow_response: str):
        """Ultra-simple sequential extraction - NO DEPENDENCIES"""
        user_msg = user_message.strip()
        glow_lower = glow_response.lower()
        
        print(f"🔍 EXTRACTION DEBUG - Input: '{user_msg}', Current state: {self.user_info}")
        
        # Skip obvious non-info messages
        skip_words = ['hi', 'hello', 'hey', 'sign up', 'signup', 'cute', 'love', 'thanks', 'ok', 'yes', 'no']
        if any(word in user_msg.lower() for word in skip_words):
            print("🔍 EXTRACTION DEBUG - Skipping (greeting/filler word)")
            return
        
        # PURE SEQUENTIAL LOGIC - NO CROSS-DEPENDENCIES
        
        # STEP 1: If no name, next non-greeting input = name
        if not self.user_info['name'] and user_msg:
            print(f"🔍 EXTRACTION DEBUG - Capturing NAME: '{user_msg}'")
            self.update_user_info('name', user_msg)
            return
        
        # STEP 2: If have name but no username, next single-word input = username  
        if self.user_info['name'] and not self.user_info['username']:
            if user_msg and len(user_msg.split()) == 1 and '@' not in user_msg:
                print(f"🔍 EXTRACTION DEBUG - Capturing USERNAME: '{user_msg}'")
                self.update_user_info('username', user_msg)
                return
        
        # STEP 3: If have username but no password, next 6+ char input = password
        if self.user_info['username'] and not self.user_info['password']:
            if user_msg and len(user_msg) >= 6 and '@' not in user_msg:
                print(f"🔍 EXTRACTION DEBUG - Capturing PASSWORD: '{user_msg}'")
                self.update_user_info('password', user_msg)
                return
        
        # STEP 4: If have password but no email, next @-containing input = email
        if self.user_info['password'] and not self.user_info['email']:
            if '@' in user_msg and '.' in user_msg:
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_match = re.search(email_pattern, user_msg)
                if email_match:
                    print(f"🔍 EXTRACTION DEBUG - Capturing EMAIL: '{email_match.group()}'")
                    self.update_user_info('email', email_match.group())
                    return
        
        # Track workflow states from Glow's responses (not user input)
        if any(phrase in glow_lower for phrase in ['code sent', 'sent to', 'verification code']):
            self.update_user_info('verification_step', True)
        
        if any(phrase in glow_lower for phrase in ['launching', 'welcome to glow', 'signup complete']):
            self.update_user_info('signup_complete', True)