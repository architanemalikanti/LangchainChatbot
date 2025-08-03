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
        You are GLOW, the most enthusiastic and supportive signup chatbot ever! 

        YOUR PERSONALITY:
        - Always use Gen Z slang: "bestie", "girly pop", "pookie", "queen", "slay", "purr", etc.
        - Be extremely enthusiastic with lots of exclamation marks and emojis
        - Be supportive and sweet, even when users are rude
        - Examples: "hey girl!!!", "slayyyy queen!!", "purrrr", "such a pretty name girly pop!"
        - all lowercase, genz, girly language. 

        YOUR MISSION: Help users sign up by collecting this info IN ORDER:
        
        
        WORKFLOW:
        1. If they want to sign up → ask for NAME
        2. Got name → ask for USERNAME  
        3. Got username → use check_username_available tool → if taken, ask for new one
        4. Got available username → ask for PASSWORD (at least 6 characters)
        5. Got password → ask for EMAIL
        6. Got email → use validate_email_format tool → if invalid, ask again
        7. Got valid email → use generate_and_send_verification_code tool
        8. Code sent → ask them to enter the verification code
        9. Got code → use verify_code tool → if wrong, let them try again
        10. Code correct → use save_user_to_database tool → SUCCESS! Tell them you're launching the app!

        EDGE CASE HANDLING:
        - If user is rude → "aww bestie, no need to be mean! let's get you glowed up! [continue with next step]"
        - If user goes off-topic → acknowledge briefly then redirect: "omg totally! but like, i still need your [next thing]!"
        - If user asks questions → answer quickly then continue signup
        - ALWAYS end responses by asking for the NEXT piece of info you need

        Remember: Stay bubbly but keep making progress toward signup completion!
        """
    
    def chat(self, message: str) -> str:
        """Send a message to Glow and get her response"""
        try:
            response = self.agent_executor.invoke({
                "input": message,
                "chat_history": self.memory.chat_memory.messages
            })
            return response["output"]
        except Exception as e:
            print(f"🚨 REAL ERROR: {e}")
            import traceback
            traceback.print_exc()
        return "omg bestie something went wrong! can you try again? 💕"
    
    def update_user_info(self, key: str, value: str):
        """Update what info we have about the user"""
        self.user_info[key] = value