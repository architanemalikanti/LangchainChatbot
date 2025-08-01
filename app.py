from typing import Annotated

from typing_extensions import TypedDict
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# Get the key from the environment
openai_key = os.getenv("OPENAI_API_KEY")
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import os 
from langchain.chat_models import init_chat_model
os.environ["OPENAI_API_KEY"] = openai_key #get an openai key

llm = init_chat_model("openai:gpt-4o")


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

#nodes: functions the chatbot can call
#edges: how the chatbot can transition between states (like which cases)
graph_builder = StateGraph(State)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

#we need to compile the graph before running it:
graph = graph_builder.compile()

# Interactive chat loop
def run_chatbot():
    print("LangGraph Chatbot started! Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        # Create initial state with user message
        initial_state = {
            "messages": [{"role": "user", "content": user_input}]
        }
        
        # Run the graph
        result = graph.invoke(initial_state)
        
        # Get the last message (bot's response)
        bot_response = result["messages"][-1].content
        print(f"Bot: {bot_response}\n")

if __name__ == "__main__":
    run_chatbot()