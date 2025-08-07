# app.py - Your Flask app
from flask import Flask, request, jsonify
from glowBrain import GlowAgent
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

app = Flask(__name__)

# Create Glow (only once when app starts)
glow = GlowAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def health_check():
    return "Glow is running! 🌟", 200

@app.route('/chat', methods=['POST'])
def chat_with_glow():
    user_message = request.json.get('message')
    glow_response = glow.chat(user_message)
    
    # Check if signup is complete
    if "launching the app" in glow_response.lower():
        return jsonify({
            "response": glow_response,
            "action": "launch_app"  # Tell your frontend to switch to contentview
        })
    
    return jsonify({"response": glow_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
