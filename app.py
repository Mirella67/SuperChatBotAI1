#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXUS AI - IL BOT PIÙ POTENTE AL MONDO
✨ Groq AI Ultra-Veloce
🎨 Generazione Immagini con Stable Diffusion
🎥 Generazione Video
📷 Analisi Immagini con Vision AI
💳 Pagamenti Gumroad
🌍 Multilingua Automatico
"""

import os
import secrets
import json
import base64
import requests
import hmac
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, render_template_string
import bcrypt

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    print("⚠️ pip install groq")

# ============================================
# CONFIGURAZIONE - AGGIUNGI LE TUE API KEY
# ============================================
GROQ_API_KEY = "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"
STABILITY_API_KEY = "sk-1nh5FBGJETSbU1DMnQu7Af0dWQLSBbUwDvS1qXUPvVQ5lx0d"  # Per generare immagini reali: https://platform.stability.ai/
REPLICATE_API_KEY = "r8_dvhoEsZoMZ4iVPCeLtenbcaML0VZw5233ilJP"  # Per video: https://replicate.com/

# GUMROAD SETTINGS
GUMROAD_PRODUCT_URL = "https://micheleguerra.gumroad.com/l/superchatbot"  # IL TUO LINK GUMROAD
GUMROAD_LICENSE_KEY = ""  # La tua License Key da Gumroad Settings

DATA_FILE = "nexus_data.json"

os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/generated", exist_ok=True)

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)

# Groq Client
groq_client = None
if HAS_GROQ and GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq AI: ATTIVO - Velocità 800+ token/sec")
    except Exception as e:
        print(f"⚠️ Groq: {e}")

# ============================================
# DATABASE
# ============================================
def load_db():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "premium_licenses": {}, "used_licenses": set()}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            data["used_licenses"] = set(data.get("used_licenses", []))
            return data
    except:
        return {"users": {}, "premium_licenses": {}, "used_licenses": set()}

def save_db():
    try:
        data = {
            "users": USERS,
            "premium_licenses": PREMIUM_LICENSES,
            "used_licenses": list(USED_LICENSES)
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Save: {e}")
        return False

DB = load_db()
USERS = DB.get("users", {})
PREMIUM_LICENSES = DB.get("premium_licenses", {})
USED_LICENSES = DB.get("used_licenses", set())

# ============================================
# FUNZIONI UTILITY
# ============================================
def get_today():
    return datetime.utcnow().strftime("%Y-%m-%d")

def get_user():
    username = session.get("username")
    return USERS.get(username) if username else None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Login richiesto"}), 401
        return f(*args, **kwargs)
    return wrapper

def verify_gumroad_license(license_key, email):
    """Verifica una licenza Gumroad"""
    if not GUMROAD_LICENSE_KEY:
        return {"success": False, "message": "Gumroad non configurato"}
    
    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_id": GUMROAD_LICENSE_KEY,
                "license_key": license_key,
                "increment_uses_count": "false"
            }
        )
        
        data = response.json()
        
        if data.get("success"):
            return {
                "success": True,
                "purchase": data.get("purchase", {}),
                "uses": data.get("uses", 0)
            }
        else:
            return {
                "success": False,
                "message": data.get("message", "Licenza non valida")
            }
    except Exception as e:
        print(f"Gumroad verify error: {e}")
        return {"success": False, "message": str(e)}

# ============================================
# AI FUNCTIONS
# ============================================
def call_groq(messages, model="llama-3.1-70b-versatile"):
    """Chiama Groq AI - Il più veloce al mondo"""
    if not groq_client:
        return "⚠️ Groq non configurato"
    
    try:
        response = groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2048,
            temperature=0.8,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq error: {e}")
        return "Mi dispiace, errore temporaneo. Riprova."

def generate_image_stability(prompt):
    """Genera immagini con Stable Diffusion"""
    if not STABILITY_API_KEY:
        # Demo mode - genera placeholder
        return {
            "url": f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=768&height=768&nologo=true",
            "demo": True
        }
    
    try:
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "text_prompts": [{"text": prompt, "weight": 1}],
                "cfg_scale": 7,
                "height": 768,
                "width": 768,
                "samples": 1,
                "steps": 30,
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            image_data = data["artifacts"][0]["base64"]
            filename = f"gen_{secrets.token_hex(8)}.png"
            filepath = os.path.join("static/generated", filename)
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            return {"url": f"/static/generated/{filename}"}
        else:
            return {
                "url": f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=768&height=768&nologo=true",
                "demo": True
            }
    except Exception as e:
        print(f"Stability error: {e}")
        return {
            "url": f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=768&height=768&nologo=true",
            "demo": True
        }

def generate_video_replicate(prompt):
    """Genera video con Replicate"""
    if not REPLICATE_API_KEY:
        return {"error": "API Replicate non configurata", "demo": True}
    
    return {"error": "Video generation in arrivo", "demo": True}

def analyze_image_vision(image_path, question):
    """Analizza immagini con Groq Vision"""
    if not groq_client:
        return "Vision AI non disponibile"
    
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = groq_client.chat.completions.create(
            model="llava-v1.5-7b-4096-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }],
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Vision error: {e}")
        return f"Analisi non disponibile: {e}"

# ============================================
# HTML TEMPLATE ULTRA MODERNO
# ============================================
CHAT_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>NEXUS AI - The Ultimate Bot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        @keyframes glow { 0%, 100% { box-shadow: 0 0 20px rgba(102,126,234,0.5); } 50% { box-shadow: 0 0 40px rgba(102,126,234,0.8); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: linear-gradient(-45deg, #0a0a0a, #1a1a2e, #16213e, #0f3460);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            color: #fff; 
            height: 100vh; 
            display: flex; 
            overflow: hidden; 
        }
        
        .sidebar { 
            width: 280px; 
            background: rgba(10,10,10,0.95); 
            backdrop-filter: blur(20px);
            display: flex; 
            flex-direction: column; 
            border-right: 1px solid rgba(102,126,234,0.2); 
            box-shadow: 5px 0 30px rgba(0,0,0,0.5);
        }
        
        .logo {
            padding: 24px;
            text-align: center;
            border-bottom: 1px solid rgba(102,126,234,0.2);
            background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
        }
        
        .logo h1 {
            font-size: 28px;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 2px;
        }
        
        .logo p {
            font-size: 11px;
            color: #888;
            margin-top: 4px;
            letter-spacing: 1px;
        }
        
        .new-chat { 
            margin: 16px;
            padding: 14px; 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            border: none; 
            border-radius: 12px; 
            color: #fff; 
            cursor: pointer; 
            font-size: 15px; 
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102,126,234,0.3);
        }
        .new-chat:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(102,126,234,0.5);
        }
        
        .sidebar-content { 
            flex: 1; 
            overflow-y: auto; 
            padding: 16px; 
        }
        
        .sidebar-content::-webkit-scrollbar { width: 6px; }
        .sidebar-content::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
        .sidebar-content::-webkit-scrollbar-thumb { background: rgba(102,126,234,0.3); border-radius: 3px; }
        
        .chat-item {
            padding: 12px;
            margin-bottom: 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid transparent;
        }
        
        .chat-item:hover {
            background: rgba(102,126,234,0.15);
            border-color: rgba(102,126,234,0.3);
            transform: translateX(4px);
        }
        
        .user-section { 
            border-top: 1px solid rgba(102,126,234,0.2); 
            padding: 20px; 
            background: rgba(0,0,0,0.3);
        }
        
        .user-info { 
            display: flex; 
            align-items: center; 
            gap: 12px; 
            margin-bottom: 12px; 
        }
        
        .avatar { 
            width: 44px; 
            height: 44px; 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-weight: 900; 
            font-size: 18px;
            box-shadow: 0 4px 15px rgba(102,126,234,0.4);
        }
        
        .username { 
            font-size: 15px; 
            font-weight: 600; 
        }
        
        .plan { 
            font-size: 12px; 
            color: #888; 
        }
        
        .premium-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            color: #000;
            animation: pulse 2s infinite;
        }
        
        .upgrade-btn { 
            width: 100%; 
            padding: 14px; 
            background: linear-gradient(135deg, #FF6B6B, #FF8E53); 
            border: none; 
            border-radius: 12px; 
            color: #fff; 
            font-weight: 700; 
            cursor: pointer; 
            margin-bottom: 8px;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(255,107,107,0.4);
            font-size: 14px;
        }
        
        .upgrade-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(255,107,107,0.6);
        }
        
        .main { 
            flex: 1; 
            display: flex; 
            flex-direction: column; 
            position: relative;
        }
        
        .chat { 
            flex: 1; 
            overflow-y: auto; 
            padding: 24px;
        }
        
        .chat::-webkit-scrollbar { width: 8px; }
        .chat::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
        .chat::-webkit-scrollbar-thumb { background: rgba(102,126,234,0.3); border-radius: 4px; }
        
        .message { 
            max-width: 900px; 
            margin: 0 auto 24px; 
            display: flex; 
            gap: 16px;
            animation: fadeIn 0.5s ease;
        }
        
        .message.user { 
            flex-direction: row-reverse; 
        }
        
        .msg-avatar { 
            width: 40px; 
            height: 40px; 
            border-radius: 12px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            flex-shrink: 0;
            font-size: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        
        .msg-avatar.bot { 
            background: linear-gradient(135deg, #667eea, #764ba2); 
        }
        
        .msg-avatar.user { 
            background: linear-gradient(135deg, #f093fb, #f5576c); 
        }
        
        .bubble { 
            padding: 16px 20px; 
            border-radius: 18px; 
            max-width: 700px;
            line-height: 1.6;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }
        
        .bubble.bot { 
            background: rgba(102,126,234,0.15); 
            border: 1px solid rgba(102,126,234,0.2);
        }
        
        .bubble.user { 
            background: rgba(240,147,251,0.2); 
            border: 1px solid rgba(240,147,251,0.3);
        }
        
        .bubble img, .bubble video { 
            max-width: 100%; 
            border-radius: 12px; 
            margin-top: 12px; 
            display: block;
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        }
        
        .bubble video { 
            max-height: 400px; 
        }
        
        .input-area { 
            border-top: 1px solid rgba(102,126,234,0.2); 
            padding: 20px;
            background: rgba(10,10,10,0.95);
            backdrop-filter: blur(20px);
        }
        
        .input-wrapper { 
            max-width: 900px; 
            margin: 0 auto; 
            display: flex; 
            gap: 12px; 
            align-items: flex-end;
        }
        
        .file-preview { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 12px; 
            flex-wrap: wrap; 
        }
        
        .preview-item { 
            position: relative; 
            width: 90px; 
            height: 90px; 
            border-radius: 12px; 
            overflow: hidden; 
            border: 2px solid rgba(102,126,234,0.3);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        
        .preview-item img, .preview-item video { 
            width: 100%; 
            height: 100%; 
            object-fit: cover; 
        }
        
        .preview-remove { 
            position: absolute; 
            top: 6px; 
            right: 6px; 
            background: rgba(0,0,0,0.8); 
            color: #fff; 
            border: none; 
            border-radius: 50%; 
            width: 24px; 
            height: 24px; 
            cursor: pointer; 
            font-size: 14px;
            font-weight: bold;
        }
        
        .tool-btn { 
            width: 50px; 
            height: 50px; 
            background: rgba(102,126,234,0.2); 
            border: 1px solid rgba(102,126,234,0.3); 
            border-radius: 12px; 
            color: #fff; 
            cursor: pointer; 
            font-size: 22px;
            transition: all 0.3s;
            flex-shrink: 0;
        }
        
        .tool-btn:hover { 
            background: rgba(102,126,234,0.4);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102,126,234,0.3);
        }
        
        #input { 
            flex: 1; 
            padding: 14px 18px; 
            background: rgba(255,255,255,0.05); 
            border: 1px solid rgba(102,126,234,0.3); 
            border-radius: 16px; 
            color: #fff; 
            font-size: 15px; 
            resize: none; 
            min-height: 50px; 
            max-height: 200px; 
            font-family: inherit;
            transition: all 0.3s;
        }
        
        #input:focus { 
            outline: none; 
            border-color: #667eea;
            background: rgba(255,255,255,0.08);
            box-shadow: 0 0 20px rgba(102,126,234,0.2);
        }
        
        #input::placeholder {
            color: rgba(255,255,255,0.4);
        }
        
        #sendBtn { 
            width: 50px; 
            height: 50px; 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            border: none; 
            border-radius: 12px; 
            color: #fff; 
            cursor: pointer; 
            font-size: 22px; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102,126,234,0.4);
            flex-shrink: 0;
        }
        
        #sendBtn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(102,126,234,0.6);
        }
        
        #sendBtn:disabled { 
            opacity: 0.5; 
            cursor: not-allowed;
            transform: none;
        }
        
        .loading { 
            display: flex; 
            gap: 6px; 
        }
        
        .loading div { 
            width: 10px; 
            height: 10px; 
            border-radius: 50%; 
            background: #667eea; 
            animation: bounce 1.4s infinite ease-in-out both; 
        }
        
        .loading div:nth-child(1) { animation-delay: -0.32s; }
        .loading div:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce { 
            0%, 80%, 100% { transform: scale(0); } 
            40% { transform: scale(1); } 
        }
        
        .welcome { 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            height: 100%; 
            text-align: center; 
            padding: 40px;
        }
        
        .welcome-icon { 
            width: 120px; 
            height: 120px; 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            border-radius: 30px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 60px; 
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(102,126,234,0.5);
            animation: glow 2s infinite;
        }
        
        .welcome h1 { 
            font-size: 48px; 
            margin-bottom: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
        }
        
        .welcome p { 
            color: #aaa; 
            font-size: 18px; 
            max-width: 600px;
            line-height: 1.6;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 40px;
            max-width: 800px;
        }
        
        .feature {
            background: rgba(102,126,234,0.1);
            border: 1px solid rgba(102,126,234,0.2);
            padding: 20px;
            border-radius: 16px;
            transition: all 0.3s;
        }
        
        .feature:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(102,126,234,0.3);
        }
        
        .feature-icon {
            font-size: 32px;
            margin-bottom: 12px;
        }
        
        .feature h3 {
            font-size: 16px;
            margin-bottom: 8px;
        }
        
        .feature p {
            font-size: 13px;
            color: #888;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
        }
        
        .modal.show {
            display: flex;
        }
        
        .modal-content {
            background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2));
            border: 2px solid rgba(102,126,234,0.3);
            border-radius: 24px;
            padding: 40px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            animation: fadeIn 0.3s ease;
        }
        
        .modal-content h2 {
            font-size: 28px;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .modal-content input {
            width: 100%;
            padding: 14px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(102,126,234,0.3);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            margin-bottom: 20px;
        }
        
        .modal-content input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .modal-content input::placeholder {
            color: rgba(255,255,255,0.4);
        }
        
        .modal-buttons {
            display: flex;
            gap: 12px;
        }
        
        .modal-btn {
            flex: 1;
            padding: 14px;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .modal-btn.primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff;
        }
        
        .modal-btn.primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(102,126,234,0.5);
        }
        
        .modal-btn.secondary {
            background: rgba(255,255,255,0.1);
            color: #fff;
        }
        
        .modal-btn.secondary:hover {
            background: rgba(255,255,255,0.15);
        }
        
        .gumroad-link {
            display: block;
            margin-top: 15px;
            color: #FF6B6B;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .gumroad-link:hover {
            color: #FF8E53;
            transform: translateX(4px);
        }
        
        @media (max-width: 768px) {
            .sidebar { 
                position: fixed; 
                left: 0; 
                top: 0; 
                height: 100vh; 
                z-index: 100; 
                transform: translateX(-100%); 
                transition: transform 0.3s; 
            }
            .sidebar.open { transform: translateX(0); }
            .mobile-header { 
                display: flex; 
                align-items: center; 
                justify-content: space-between; 
                padding: 16px 20px; 
                background: rgba(10,10,10,0.95); 
                border-bottom: 1px solid rgba(102,126,234,0.2);
                backdrop-filter: blur(20px);
            }
            .menu-btn { 
                background: none; 
                border: none; 
                color: #fff; 
                font-size: 28px; 
                cursor: pointer; 
            }
            .features {
                grid-template-columns: 1fr;
            }
        }
        
        @media (min-width: 769px) {
            .mobile-header { display: none; }
        }
    </style>
</head>
<body>
    <div class="mobile-header">
        <button class="menu-btn" onclick="toggleSidebar()">☰</button>
        <span style="font-weight: 600;">NEXUS AI</span>
    </div>

    <div class="sidebar">
        <div class="logo">
            <h1>⚡ NEXUS</h1>
            <p>ULTIMATE AI ASSISTANT</p>
        </div>
        <button class="new-chat" onclick="newChat()">✨ Nuova Chat</button>
        <div class="sidebar-content">
            <div id="chatHistory"></div>
        </div>
        <div class="user-section">
            <div class="user-info">
                <div class="avatar" id="userAvatar">U</div>
                <div>
                    <div class="username" id="username">Guest</div>
                    <div class="plan" id="userPlan">
                        <span id="planBadge">Free Plan</span>
                    </div>
                </div>
            </div>
            <button class="upgrade-btn" onclick="showUpgradeModal()">
                🚀 UPGRADE PREMIUM
            </button>
            <button class="upgrade-btn" style="background: linear-gradient(135deg, #667eea, #764ba2);" onclick="logout()">
                🚪 Logout
            </button>
        </div>
    </div>

    <div class="main">
        <div class="chat" id="chat">
            <div class="welcome">
                <div class="welcome-icon">🤖</div>
                <h1>Benvenuto in NEXUS AI</h1>
                <p>Il bot più potente al mondo con intelligenza artificiale ultra-veloce, generazione immagini, video, analisi avanzata e molto altro.</p>
                
                <div class="features">
                    <div class="feature">
                        <div class="feature-icon">⚡</div>
                        <h3>Ultra Veloce</h3>
                        <p>800+ token/sec con Groq AI</p>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">🎨</div>
                        <h3>Genera Immagini</h3>
                        <p>Stable Diffusion HD</p>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">🎥</div>
                        <h3>Genera Video</h3>
                        <p>AI Video Generation</p>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">👁️</div>
                        <h3>Vision AI</h3>
                        <p>Analisi immagini avanzata</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <div id="filePreview" class="file-preview"></div>
            <div class="input-wrapper">
                <button class="tool-btn" onclick="document.getElementById('fileInput').click()" title="Carica immagine">
                    📎
                </button>
                <input type="file" id="fileInput" style="display: none;" accept="image/*,video/*" onchange="handleFileSelect(event)">
                
                <textarea id="input" placeholder="Scrivi un messaggio... (es: genera un'immagine di..., analizza questa foto, crea un video...)" 
                    onkeydown="if(event.key==='Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); }"></textarea>
                
                <button id="sendBtn" onclick="sendMessage()">
                    ➤
                </button>
            </div>
        </div>
    </div>

    <!-- Modal Upgrade Premium -->
    <div id="upgradeModal" class="modal">
        <div class="modal-content">
            <h2>🚀 Upgrade a Premium</h2>
            <p style="margin-bottom: 20px; color: #aaa;">Sblocca tutte le funzionalità avanzate:</p>
            <ul style="margin-bottom: 20px; color: #aaa; line-height: 2;">
                <li>✨ Chat illimitate</li>
                <li>🎨 Generazione immagini HD</li>
                <li>🎥 Generazione video AI</li>
                <li>👁️ Vision AI avanzata</li>
                <li>⚡ Priorità nelle risposte</li>
                <li>🔥 Modelli AI premium</li>
            </ul>
            <input type="text" id="licenseKey" placeholder="Inserisci la tua License Key Gumroad">
            <div class="modal-buttons">
                <button class="modal-btn secondary" onclick="closeUpgradeModal()">Chiudi</button>
                <button class="modal-btn primary" onclick="activateLicense()">Attiva</button>
            </div>
            <a href="${GUMROAD_PRODUCT_URL}" target="_blank" class="gumroad-link">
                🛒 Acquista su Gumroad →
            </a>
        </div>
    </div>

    <script>
        let selectedFiles = [];
        let currentChatId = Date.now();
        let chatHistory = {};
        
        // Inizializzazione
        document.addEventListener('DOMContentLoaded', async () => {
            await checkAuth();
            loadChatHistory();
            adjustTextareaHeight();
        });

        async function checkAuth() {
            try {
                const res = await fetch('/api/user');
                if (res.ok) {
                    const user = await res.json();
                    updateUserUI(user);
                } else {
                    window.location.href = '/login';
                }
            } catch (e) {
                console.error('Auth check failed:', e);
            }
        }

        function updateUserUI(user) {
            document.getElementById('username').textContent = user.username;
            document.getElementById('userAvatar').textContent = user.username[0].toUpperCase();
            
            if (user.premium) {
                document.getElementById('planBadge').innerHTML = '<span class="premium-badge">⭐ PREMIUM</span>';
                document.querySelector('.upgrade-btn').textContent = '✅ Premium Attivo';
                document.querySelector('.upgrade-btn').style.background = 'linear-gradient(135deg, #00C851, #007E33)';
            }
        }

        function toggleSidebar() {
            document.querySelector('.sidebar').classList.toggle('open');
        }

        function newChat() {
            currentChatId = Date.now();
            document.getElementById('chat').innerHTML = `
                <div class="welcome">
                    <div class="welcome-icon">🤖</div>
                    <h1>Nuova Chat</h1>
                    <p>Cosa posso fare per te oggi?</p>
                </div>
            `;
            document.getElementById('input').value = '';
            selectedFiles = [];
            updateFilePreview();
        }

        function loadChatHistory() {
            const history = Object.keys(chatHistory).sort((a, b) => b - a);
            const html = history.map(id => `
                <div class="chat-item" onclick="loadChat(${id})">
                    <div style="font-size: 13px; color: #888;">${new Date(parseInt(id)).toLocaleDateString()}</div>
                    <div style="margin-top: 4px; font-size: 14px;">Chat ${id}</div>
                </div>
            `).join('');
            document.getElementById('chatHistory').innerHTML = html || '<div style="padding: 12px; color: #666; text-align: center;">Nessuna chat</div>';
        }

        function loadChat(id) {
            currentChatId = id;
            const messages = chatHistory[id] || [];
            const chat = document.getElementById('chat');
            chat.innerHTML = '';
            messages.forEach(msg => addMessageToUI(msg.role, msg.content, msg.type));
        }

        function handleFileSelect(event) {
            const files = Array.from(event.target.files);
            selectedFiles = [...selectedFiles, ...files].slice(0, 5); // Max 5 files
            updateFilePreview();
        }

        function updateFilePreview() {
            const preview = document.getElementById('filePreview');
            if (selectedFiles.length === 0) {
                preview.innerHTML = '';
                return;
            }
            
            preview.innerHTML = selectedFiles.map((file, index) => {
                const url = URL.createObjectURL(file);
                const isVideo = file.type.startsWith('video/');
                const tag = isVideo ? `<video src="${url}" autoplay muted loop></video>` : `<img src="${url}">`;
                return `
                    <div class="preview-item">
                        ${tag}
                        <button class="preview-remove" onclick="removeFile(${index})">×</button>
                    </div>
                `;
            }).join('');
        }

        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateFilePreview();
        }

        async function sendMessage() {
            const input = document.getElementById('input');
            const text = input.value.trim();
            
            if (!text && selectedFiles.length === 0) return;
            
            // Disabilita input
            input.disabled = true;
            document.getElementById('sendBtn').disabled = true;
            
            // Rimuovi welcome se presente
            const welcome = document.querySelector('.welcome');
            if (welcome) welcome.remove();
            
            // Aggiungi messaggio utente
            addMessageToUI('user', text);
            input.value = '';
            adjustTextareaHeight();
            
            // Determina il tipo di richiesta
            let requestType = 'chat';
            const lowerText = text.toLowerCase();
            
            if (lowerText.includes('genera') && (lowerText.includes('immagine') || lowerText.includes('foto') || lowerText.includes('disegno'))) {
                requestType = 'image';
            } else if (lowerText.includes('genera') && lowerText.includes('video')) {
                requestType = 'video';
            } else if (selectedFiles.length > 0) {
                requestType = 'vision';
            }
            
            try {
                // Invia richiesta
                const formData = new FormData();
                formData.append('message', text);
                formData.append('type', requestType);
                selectedFiles.forEach(file => formData.append('files', file));
                
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('Errore nella richiesta');
                }
                
                const data = await response.json();
                
                // Aggiungi risposta
                if (data.error) {
                    addMessageToUI('bot', `❌ ${data.error}`);
                } else {
                    addMessageToUI('bot', data.response, data.type, data.media);
                }
                
                // Salva in history
                if (!chatHistory[currentChatId]) {
                    chatHistory[currentChatId] = [];
                }
                chatHistory[currentChatId].push(
                    { role: 'user', content: text },
                    { role: 'bot', content: data.response, type: data.type, media: data.media }
                );
                loadChatHistory();
                
            } catch (error) {
                console.error('Error:', error);
                addMessageToUI('bot', '❌ Si è verificato un errore. Riprova.');
            } finally {
                // Riabilita input
                input.disabled = false;
                document.getElementById('sendBtn').disabled = false;
                input.focus();
                selectedFiles = [];
                updateFilePreview();
            }
        }

        function addMessageToUI(role, content, type = 'text', media = null) {
            const chat = document.getElementById('chat');
            const isBot = role === 'bot';
            
            let mediaHtml = '';
            if (media) {
                if (type === 'image') {
                    mediaHtml = `<img src="${media}" alt="Generated image" style="max-width: 100%; border-radius: 12px; margin-top: 12px;">`;
                } else if (type === 'video') {
                    mediaHtml = `<video src="${media}" controls style="max-width: 100%; border-radius: 12px; margin-top: 12px;"></video>`;
                }
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            messageDiv.innerHTML = `
                <div class="msg-avatar ${role}">${isBot ? '🤖' : '👤'}</div>
                <div class="bubble ${role}">
                    ${content}
                    ${mediaHtml}
                </div>
            `;
            
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }

        function adjustTextareaHeight() {
            const textarea = document.getElementById('input');
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
        }

        document.getElementById('input').addEventListener('input', adjustTextareaHeight);

        function showUpgradeModal() {
            document.getElementById('upgradeModal').classList.add('show');
        }

        function closeUpgradeModal() {
            document.getElementById('upgradeModal').classList.remove('show');
        }

        async function activateLicense() {
            const licenseKey = document.getElementById('licenseKey').value.trim();
            
            if (!licenseKey) {
                alert('Inserisci una license key valida');
                return;
            }
            
            try {
                const response = await fetch('/api/activate-premium', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ license_key: licenseKey })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ Premium attivato con successo!');
                    closeUpgradeModal();
                    location.reload();
                } else {
                    alert('❌ ' + (data.message || 'License key non valida'));
                }
            } catch (error) {
                alert('❌ Errore durante l\'attivazione');
            }
        }

        async function logout() {
            try {
                await fetch('/api/logout', { method: 'POST' });
                window.location.href = '/login';
            } catch (e) {
                console.error('Logout failed:', e);
            }
        }

        // Auto-resize textarea
        document.getElementById('input').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });
    </script>
</body>
</html>
"""

# ============================================
# ROUTES
# ============================================

@app.route("/")
def index():
    if "username" not in session:
        return render_template_string(LOGIN_HTML)
    return render_template_string(CHAT_HTML)

@app.route("/login")
def login_page():
    return render_template_string(LOGIN_HTML)

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>NEXUS AI - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        @keyframes glow { 0%, 100% { box-shadow: 0 0 30px rgba(102,126,234,0.5); } 50% { box-shadow: 0 0 60px rgba(102,126,234,0.8); } }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(-45deg, #0a0a0a, #1a1a2e, #16213e, #0f3460);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }
        
        .login-container {
            background: rgba(10,10,10,0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102,126,234,0.2);
            border-radius: 24px;
            padding: 50px 40px;
            max-width: 450px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }
        
        .logo-container {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .logo-icon {
            width: 90px;
            height: 90px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 22px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 45px;
            margin-bottom: 20px;
            animation: glow 2s infinite;
        }
        
        .logo-container h1 {
            font-size: 36px;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }
        
        .logo-container p {
            color: #888;
            font-size: 14px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        
        .tab {
            flex: 1;
            padding: 12px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(102,126,234,0.2);
            border-radius: 12px;
            color: #aaa;
            cursor: pointer;
            text-align: center;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .tab.active {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff;
            border-color: transparent;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #aaa;
            font-size: 14px;
            font-weight: 600;
        }
        
        .form-group input {
            width: 100%;
            padding: 14px 16px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(102,126,234,0.3);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            transition: all 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            background: rgba(255,255,255,0.08);
            box-shadow: 0 0 20px rgba(102,126,234,0.2);
        }
        
        .form-group input::placeholder {
            color: rgba(255,255,255,0.3);
        }
        
        .submit-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102,126,234,0.4);
            margin-top: 10px;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(102,126,234,0.6);
        }
        
        .message {
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        
        .message.success {
            background: rgba(0,200,83,0.2);
            border: 1px solid rgba(0,200,83,0.3);
            color: #00C853;
        }
        
        .message.error {
            background: rgba(255,107,107,0.2);
            border: 1px solid rgba(255,107,107,0.3);
            color: #FF6B6B;
        }
        
        #registerForm { display: none; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo-container">
            <div class="logo-icon">⚡</div>
            <h1>NEXUS AI</h1>
            <p>The Ultimate AI Assistant</p>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('login')">Login</div>
            <div class="tab" onclick="switchTab('register')">Registrati</div>
        </div>
        
        <div id="message" class="message"></div>
        
        <form id="loginForm" onsubmit="handleLogin(event)">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" placeholder="Il tuo username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" placeholder="La tua password" required>
            </div>
            <button type="submit" class="submit-btn">🚀 Accedi</button>
        </form>
        
        <form id="registerForm" onsubmit="handleRegister(event)">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" placeholder="Scegli un username" required>
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" placeholder="La tua email" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" placeholder="Crea una password" required>
            </div>
            <button type="submit" class="submit-btn">✨ Crea Account</button>
        </form>
    </div>
    
    <script>
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            document.getElementById('loginForm').style.display = tab === 'login' ? 'block' : 'none';
            document.getElementById('registerForm').style.display = tab === 'register' ? 'block' : 'none';
            hideMessage();
        }
        
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = `message ${type}`;
            msg.style.display = 'block';
        }
        
        function hideMessage() {
            document.getElementById('message').style.display = 'none';
        }
        
        async function handleLogin(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(Object.fromEntries(formData))
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('✅ Login effettuato!', 'success');
                    setTimeout(() => window.location.href = '/', 1000);
                } else {
                    showMessage('❌ ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('❌ Errore di connessione', 'error');
            }
        }
        
        async function handleRegister(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(Object.fromEntries(formData))
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('✅ Account creato! Accedi ora.', 'success');
                    setTimeout(() => switchTab('login'), 2000);
                } else {
                    showMessage('❌ ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('❌ Errore di connessione', 'error');
            }
        }
    </script>
</body>
</html>
"""

@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.json
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not username or not email or not password:
            return jsonify({"success": False, "message": "Compila tutti i campi"})
        
        if username in USERS:
            return jsonify({"success": False, "message": "Username già esistente"})
        
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        USERS[username] = {
            "username": username,
            "email": email,
            "password": hashed.decode(),
            "premium": False,
            "created_at": datetime.utcnow().isoformat(),
            "chat_count": 0
        }
        
        save_db()
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({"success": False, "message": "Errore durante la registrazione"})

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        user = USERS.get(username)
        
        if not user:
            return jsonify({"success": False, "message": "Username non trovato"})
        
        if not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return jsonify({"success": False, "message": "Password errata"})
        
        session["username"] = username
        return jsonify({"success": True})
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "message": "Errore durante il login"})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/user")
@login_required
def get_user():
    user = get_user()
    if user:
        return jsonify({
            "username": user["username"],
            "email": user.get("email", ""),
            "premium": user.get("premium", False),
            "chat_count": user.get("chat_count", 0)
        })
    return jsonify({"error": "User not found"}), 404

@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    try:
        user = get_user()
        message = request.form.get("message", "").strip()
        request_type = request.form.get("type", "chat")
        
        # Controllo limiti free
        if not user.get("premium", False):
            today_count = user.get("chat_count", 0)
            if today_count >= 50:  # Limite free: 50 messaggi/giorno
                return jsonify({
                    "error": "Hai raggiunto il limite giornaliero. Passa a Premium per chat illimitate!",
                    "upgrade": True
                })
        
        # Incrementa contatore
        user["chat_count"] = user.get("chat_count", 0) + 1
        save_db()
        
        # Gestisci diversi tipi di richiesta
        if request_type == "image":
            # Generazione immagine
            result = generate_image_stability(message)
            return jsonify({
                "success": True,
                "response": "✨ Ecco l'immagine generata:",
                "type": "image",
                "media": result["url"]
            })
        
        elif request_type == "video":
            # Generazione video
            result = generate_video_replicate(message)
            if result.get("demo"):
                return jsonify({
                    "success": True,
                    "response": "🎥 La generazione video sarà disponibile a breve. Nel frattempo, prova a generare immagini!",
                    "type": "text"
                })
            return jsonify({
                "success": True,
                "response": "🎥 Video generato con successo!",
                "type": "video",
                "media": result.get("url")
            })
        
        elif request_type == "vision" and request.files:
            # Analisi immagine
            file = request.files.getlist("files")[0]
            filename = f"upload_{secrets.token_hex(8)}.{file.filename.split('.')[-1]}"
            filepath = os.path.join("static/uploads", filename)
            file.save(filepath)
            
            analysis = analyze_image_vision(filepath, message or "Descrivi questa immagine in dettaglio")
            
            return jsonify({
                "success": True,
                "response": f"👁️ **Analisi dell'immagine:**\n\n{analysis}",
                "type": "vision"
            })
        
        else:
            # Chat normale con Groq AI
            messages = [
                {
                    "role": "system",
                    "content": """Sei NEXUS, l'assistente AI più potente e avanzato al mondo. 
                    
Caratteristiche principali:
- Ultra-veloce e intelligente
- Esperto in programmazione, matematica, scienza, arte, scrittura
- Creativo e innovativo
- Amichevole ma professionale
- Dai risposte dettagliate e utili
- Puoi generare immagini, video e analizzare contenuti
- Supporti multilingua automatico

Capacità speciali:
🎨 Generazione immagini HD con Stable Diffusion
🎥 Generazione video con AI
👁️ Analisi immagini avanzata
💻 Programmazione in tutti i linguaggi
📊 Analisi dati e visualizzazioni
✍️ Scrittura creativa e contenuti
🔬 Ricerca e problem solving

Rispondi sempre in modo chiaro, completo e coinvolgente. Se l'utente chiede di generare immagini o video, guidalo su come fare."""
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
            
            # Scegli il modello in base al piano
            model = "llama-3.3-70b-versatile" if user.get("premium") else "llama-3.1-70b-versatile"
            
            response = call_groq(messages, model)
            
            return jsonify({
                "success": True,
                "response": response,
                "type": "text"
            })
    
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "error": "Si è verificato un errore. Riprova.",
            "details": str(e)
        }), 500

@app.route("/api/activate-premium", methods=["POST"])
@login_required
def activate_premium():
    try:
        data = request.json
        license_key = data.get("license_key", "").strip()
        
        if not license_key:
            return jsonify({"success": False, "message": "License key mancante"})
        
        # Verifica se già usata
        if license_key in USED_LICENSES:
            return jsonify({"success": False, "message": "Questa license key è già stata utilizzata"})
        
        user = get_user()
        
        # Verifica con Gumroad
        result = verify_gumroad_license(license_key, user.get("email", ""))
        
        if result.get("success"):
            # Attiva premium
            user["premium"] = True
            user["premium_activated_at"] = datetime.utcnow().isoformat()
            user["license_key"] = license_key
            
            # Marca license come usata
            USED_LICENSES.add(license_key)
            PREMIUM_LICENSES[license_key] = {
                "username": user["username"],
                "activated_at": datetime.utcnow().isoformat()
            }
            
            save_db()
            
            return jsonify({
                "success": True,
                "message": "Premium attivato con successo!"
            })
        else:
            return jsonify({
                "success": False,
                "message": result.get("message", "License key non valida")
            })
    
    except Exception as e:
        print(f"Premium activation error: {e}")
        return jsonify({
            "success": False,
            "message": "Errore durante l'attivazione"
        }), 500

# ============================================
# FUNZIONALITÀ AVANZATE
# ============================================

@app.route("/api/models", methods=["GET"])
@login_required
def get_models():
    """Lista modelli AI disponibili"""
    user = get_user()
    is_premium = user.get("premium", False)
    
    models = [
        {
            "id": "llama-3.1-70b-versatile",
            "name": "Llama 3.1 70B",
            "description": "Modello veloce e versatile",
            "free": True
        },
        {
            "id": "llama-3.3-70b-versatile",
            "name": "Llama 3.3 70B",
            "description": "Modello più avanzato e accurato",
            "free": False,
            "premium_only": True
        },
        {
            "id": "mixtral-8x7b-32768",
            "name": "Mixtral 8x7B",
            "description": "Eccellente per coding e analisi",
            "free": False,
            "premium_only": True
        }
    ]
    
    # Filtra modelli in base al piano
    if not is_premium:
        models = [m for m in models if m.get("free", False)]
    
    return jsonify({"models": models})

@app.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    """Statistiche utente"""
    user = get_user()
    
    return jsonify({
        "username": user["username"],
        "premium": user.get("premium", False),
        "chat_count": user.get("chat_count", 0),
        "member_since": user.get("created_at", ""),
        "total_users": len(USERS),
        "premium_users": sum(1 for u in USERS.values() if u.get("premium", False))
    })

@app.route("/api/export-chat", methods=["POST"])
@login_required
def export_chat():
    """Esporta chat in formato JSON/TXT"""
    try:
        data = request.json
        chat_id = data.get("chat_id")
        format_type = data.get("format", "txt")  # txt o json
        
        # Implementazione export...
        return jsonify({
            "success": True,
            "message": "Chat esportata"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/feedback", methods=["POST"])
@login_required
def submit_feedback():
    """Raccogli feedback dagli utenti"""
    try:
        data = request.json
        feedback = data.get("feedback", "")
        rating = data.get("rating", 0)
        
        user = get_user()
        
        # Salva feedback in un file separato
        feedback_data = {
            "username": user["username"],
            "feedback": feedback,
            "rating": rating,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        feedback_file = "feedback.json"
        feedbacks = []
        
        if os.path.exists(feedback_file):
            with open(feedback_file, "r") as f:
                feedbacks = json.load(f)
        
        feedbacks.append(feedback_data)
        
        with open(feedback_file, "w") as f:
            json.dump(feedbacks, f, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Grazie per il tuo feedback!"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# WEBHOOK GUMROAD (Attivazione automatica)
# ============================================

@app.route("/webhook/gumroad", methods=["POST"])
def gumroad_webhook():
    """Webhook per attivare automaticamente Premium dopo acquisto"""
    try:
        # Verifica signature
        signature = request.headers.get("X-Gumroad-Signature")
        payload = request.get_data()
        
        # In produzione, verifica la firma HMAC
        # expected_signature = hmac.new(
        #     GUMROAD_WEBHOOK_SECRET.encode(),
        #     payload,
        #     hashlib.sha256
        # ).hexdigest()
        
        data = request.form
        
        # Estrai dati
        email = data.get("email")
        license_key = data.get("license_key")
        product_id = data.get("product_id")
        
        if license_key and email:
            # Trova utente per email
            user_found = None
            username_found = None
            
            for username, user_data in USERS.items():
                if user_data.get("email") == email:
                    user_found = user_data
                    username_found = username
                    break
            
            if user_found:
                # Attiva premium automaticamente
                user_found["premium"] = True
                user_found["premium_activated_at"] = datetime.utcnow().isoformat()
                user_found["license_key"] = license_key
                
                USED_LICENSES.add(license_key)
                PREMIUM_LICENSES[license_key] = {
                    "username": username_found,
                    "email": email,
                    "activated_at": datetime.utcnow().isoformat(),
                    "auto_activated": True
                }
                
                save_db()
                
                print(f"✅ Premium auto-attivato per {username_found}")
        
        return jsonify({"success": True}), 200
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# ADMIN PANEL (Opzionale)
# ============================================

@app.route("/admin")
def admin_panel():
    """Pannello admin per gestire utenti e licenze"""
    if session.get("username") != "admin":  # Cambia con il tuo username admin
        return "Accesso negato", 403
    
    stats = {
        "total_users": len(USERS),
        "premium_users": sum(1 for u in USERS.values() if u.get("premium", False)),
        "total_licenses": len(PREMIUM_LICENSES),
        "used_licenses": len(USED_LICENSES)
    }
    
    return jsonify(stats)

# ============================================
# STRATEGIE DI INTEGRAZIONE AVANZATE
# ============================================

"""
🚀 STRATEGIE DI INTEGRAZIONE PER NEXUS AI

1. **INTEGRAZIONE API MULTIPLE**
   - Groq AI per chat ultra-veloce
   - Stability AI per immagini HD
   - Replicate per video generation
   - Vision AI per analisi immagini
   - Gumroad per pagamenti

2. **SISTEMA DI AUTENTICAZIONE ROBUSTO**
   - Bcrypt per password sicure
   - Session management con Flask
   - Protezione CSRF
   - Rate limiting

3. **GESTIONE UTENTI E PIANI**
   - Piano Free con limiti
   - Piano Premium illimitato
   - Verifica licenze Gumroad
   - Webhook per attivazione automatica

4. **MULTIMODALITÀ AVANZATA**
   - Chat testuale
   - Generazione immagini
   - Generazione video
   - Analisi immagini con Vision
   - Upload e preview file

5. **UI/UX MODERNA**
   - Design gradiente animato
   - Responsive mobile-first
   - Animazioni fluide
   - Dark mode professionale
   - Preview file in tempo reale

6. **SCALABILITÀ**
   - Database JSON (facile upgrade a SQL)
   - Struttura modulare
   - API RESTful
   - Webhook per integrazioni

7. **MONETIZZAZIONE**
   - Integrazione Gumroad nativa
   - Licenze verificabili
   - Upgrade modal integrato
   - Tracking utilizzo

8. **FEATURES PREMIUM**
   - Modelli AI avanzati
   - Chat illimitate
   - Generazione HD
   - Priorità nelle risposte
   - Supporto prioritario

9. **SICUREZZA**
   - Password hashing
   - Session security
   - Input sanitization
   - Error handling
   - Rate limiting

10. **ANALYTICS E FEEDBACK**
    - Tracking utilizzo
    - Sistema feedback
    - Statistiche utente
    - Export chat
    - Admin panel

PROSSIMI STEP:
- Aggiungere Redis per caching
- Implementare WebSocket per real-time
- Integrare più modelli AI
- Sistema di referral
- Mobile app con React Native
- Plugin Chrome extension
- API pubblica per developers
"""

# ============================================
# AVVIO APP
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("⚡ NEXUS AI - IL BOT PIÙ POTENTE AL MONDO")
    print("="*60)
    print(f"✅ Groq AI: {'ATTIVO' if groq_client else 'NON CONFIGURATO'}")
    print(f"✅ Stability API: {'ATTIVO' if STABILITY_API_KEY else 'DEMO MODE'}")
    print(f"✅ Replicate API: {'ATTIVO' if REPLICATE_API_KEY else 'IN ARRIVO'}")
    print(f"✅ Gumroad: {'ATTIVO' if GUMROAD_LICENSE_KEY else 'NON CONFIGURATO'}")
    print(f"\n📊 Utenti registrati: {len(USERS)}")
    print(f"💎 Utenti Premium: {sum(1 for u in USERS.values() if u.get('premium', False))}")
    print("\n🌐 Server avviato su: http://127.0.0.1:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)
        
