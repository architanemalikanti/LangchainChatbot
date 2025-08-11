# embedding_service.py - Fast vector matching for dating
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class EmbeddingMatcher:
    def __init__(self):
        self.setup_database()
        
    def setup_database(self):
        """Create tables for conversations and guy profiles"""
        conn = sqlite3.connect('dating_embeddings.db')
        cursor = conn.cursor()
        
        # Table for girl conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS girl_conversations (
                id INTEGER PRIMARY KEY,
                vent_text TEXT,
                embedding TEXT,  -- JSON string of vector
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for guy profiles with pre-computed embeddings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guy_profiles (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,  -- Full personality description
                embedding TEXT,    -- JSON string of vector
                profile_data TEXT  -- JSON string of full profile
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Pre-populate guy profiles if empty
        self.populate_guy_profiles()
    
    def get_embedding(self, text):
        """Get embedding from OpenAI API - FAST!"""
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",  # Fastest model
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def save_girl_conversation(self, vent_text):
        """Save girl's venting and create embedding"""
        # Get embedding
        embedding = self.get_embedding(vent_text)
        if not embedding:
            return None
            
        # Save to database
        conn = sqlite3.connect('dating_embeddings.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO girl_conversations (vent_text, embedding)
            VALUES (?, ?)
        ''', (vent_text, json.dumps(embedding)))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def populate_guy_profiles(self):
        """Pre-populate guy profiles with embeddings"""
        conn = sqlite3.connect('dating_embeddings.db')
        cursor = conn.cursor()
        
        # Check if already populated
        cursor.execute('SELECT COUNT(*) FROM guy_profiles')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        guys = [
            {
                "name": "Adrian",
                "description": "UX Designer and barista who loves coffee culture, gentle and nurturing personality, understands busy schedules from hackathons and studying, creative problem solver, brings aesthetic coffee during late night work sessions, emotionally supportive but gives space for independence, soft spoken with feminine energy, values work-life balance",
                "profile": {
                    "age": 24,
                    "occupation": "UX Designer & Part-time Barista",
                    "personality": "Soft-spoken creative with a nurturing side",
                    "traits": ["Gentle", "Creative", "Understanding", "Feminine energy"],
                    "compatibility_score": 94,
                    "emoji": "☕️"
                }
            },
            {
                "name": "Marcus",
                "description": "Software engineer and yoga instructor, tech-savvy with zen mindful energy, understands coding and development work, provides calming presence after stressful days, debugging partner and massage therapist, balanced masculine and feminine energy, career focused but wellness oriented",
                "profile": {
                    "age": 26,
                    "occupation": "Software Engineer & Yoga Instructor", 
                    "personality": "Tech-savvy with a zen, caring nature",
                    "traits": ["Intelligent", "Calm", "Supportive", "Tech-savvy"],
                    "compatibility_score": 92,
                    "emoji": "🧘‍♂️"
                }
            },
            {
                "name": "Jamie",
                "description": "Art student and plant parent, artistic soul with nurturing gentle spirit, soft boy aesthetic with caring heart, creates peaceful plant-filled spaces, intuitive about mental health needs, prefers slower pace than career driven lifestyle, values emotional connection over ambition",
                "profile": {
                    "age": 23,
                    "occupation": "Art Student & Plant Parent",
                    "personality": "Artistic soul with a nurturing, gentle spirit", 
                    "traits": ["Artistic", "Nurturing", "Gentle", "Intuitive"],
                    "compatibility_score": 88,
                    "emoji": "🌱"
                }
            },
            {
                "name": "Kai",
                "description": "Product manager and weekend chef, organized achiever with soft caring side, matches ambition but provides balance, meal prepping supportive partner, celebrates wins with homemade treats, career focused with work-life balance, understanding of busy schedules",
                "profile": {
                    "age": 25,
                    "occupation": "Product Manager & Weekend Chef",
                    "personality": "Organized achiever with a soft, caring side",
                    "traits": ["Ambitious", "Caring", "Organized", "Supportive"],
                    "compatibility_score": 90,
                    "emoji": "👨‍🍳"
                }
            },
            {
                "name": "River",
                "description": "Music producer and vintage collector, creative dreamer with old soul and gentle heart, soft indie boy vibe with caring energy, creates playlists for study sessions, calms stressed minds through music, artistic muse and emotional support, flexible creative schedule",
                "profile": {
                    "age": 22,
                    "occupation": "Music Producer & Vintage Collector",
                    "personality": "Creative dreamer with an old soul and gentle heart",
                    "traits": ["Creative", "Gentle", "Artistic", "Empathetic"],
                    "compatibility_score": 86,
                    "emoji": "🎵"
                }
            },
            {
                "name": "Elliot",
                "description": "Therapist and weekend photographer, emotionally intelligent with calming presence, trained to understand and support others, gentle feminine energy with emotional intelligence, handles independent personalities perfectly, values deep connections and mental health, professional helper",
                "profile": {
                    "age": 27,
                    "occupation": "Therapist & Weekend Photographer",
                    "personality": "Emotionally intelligent with a calming presence",
                    "traits": ["Emotionally intelligent", "Supportive", "Gentle", "Understanding"],
                    "compatibility_score": 95,
                    "emoji": "📸"
                }
            },
            {
                "name": "Arjun",
                "description": "Traditional alpha male bodybuilder and crypto bro, extremely masculine dominant personality, expects women to be submissive and traditional, obsessed with gym culture and protein shakes, dismissive of independent career women, believes men should lead relationships, toxic masculinity energy, hates when women are busy with work, wants traditional housewife who cooks and cleans, aggressive competitive nature, zero emotional intelligence, thinks femininity in men is weakness",
                "profile": {
                    "age": 28,
                    "occupation": "Personal Trainer & Crypto Investor",
                    "personality": "Ultra-masculine alpha male with traditional views",
                    "traits": ["Dominant", "Traditional", "Aggressive", "Inflexible"],
                    "compatibility_score": 5,
                    "emoji": "💪"
                }
            }
        ]
        
        # Create embeddings for each guy
        for guy in guys:
            embedding = self.get_embedding(guy["description"])
            if embedding:
                cursor.execute('''
                    INSERT INTO guy_profiles (name, description, embedding, profile_data)
                    VALUES (?, ?, ?, ?)
                ''', (
                    guy["name"],
                    guy["description"], 
                    json.dumps(embedding),
                    json.dumps(guy["profile"])
                ))
        
        conn.commit()
        conn.close()
        print("✅ Guy profiles populated with embeddings!")
    
    def find_matches(self, vent_text, top_k=6):
        """Find best matches using cosine similarity"""
        # Save conversation and get embedding
        conversation_id = self.save_girl_conversation(vent_text)
        if not conversation_id:
            return []
        
        # Get girl's embedding
        conn = sqlite3.connect('dating_embeddings.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT embedding FROM girl_conversations WHERE id = ?', (conversation_id,))
        girl_embedding = json.loads(cursor.fetchone()[0])
        
        # Get all guy embeddings
        cursor.execute('SELECT name, embedding, profile_data FROM guy_profiles')
        guys = cursor.fetchall()
        conn.close()
        
        matches = []
        for name, embedding_str, profile_str in guys:
            guy_embedding = json.loads(embedding_str)
            profile = json.loads(profile_str)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(
                [girl_embedding], 
                [guy_embedding]
            )[0][0]
            
            # Update compatibility score based on similarity
            profile['compatibility_score'] = int(similarity * 100)
            profile['name'] = name
            profile['similarity_score'] = similarity
            
            matches.append(profile)
        
        # Sort by similarity and return top matches
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches[:top_k]

# Global instance
matcher = EmbeddingMatcher() 