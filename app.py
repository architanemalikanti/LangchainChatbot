# app.py - Your Flask app
from flask import Flask, request, jsonify
from glowBrain import GlowAgent
from embedding_service import matcher
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

@app.route('/api/dating-matches', methods=['POST'])
def get_dating_matches():
    """NEW: Vector-based dating matches!"""
    try:
        vent_text = request.json.get('vent_text')
        if not vent_text:
            return jsonify({"error": "No vent text provided"}), 400
        
        # Get matches using vector similarity
        matches = matcher.find_matches(vent_text)
        
        return jsonify({
            "matches": matches,
            "message": "Found your perfect matches based on your vibe! ✨"
        })
    
    except Exception as e:
        print(f"Dating matches error: {e}")
        return jsonify({"error": "Failed to find matches"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
