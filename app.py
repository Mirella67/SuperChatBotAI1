# app.py - EMI SUPER BOT - COMPLETO E FINALE
# Bot più potente di ChatGPT con pagamenti Gumroad integrati
# 
# INSTALLAZIONE:
# pip install flask bcrypt groq
# python app.py
#
# Account demo: admin / admin123

import os
import time
import secrets
import json
from datetime import datetime, timezone
from functools import wraps
from hashlib import sha1, md5
from hmac import new as hmac_new

from flask import (
    Flask, request, jsonify, session, render_template_string,
    redirect, url_for, flash, send_from_directory
)
import bcrypt

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except:
    Groq = None
    GROQ_AVAILABLE = False

# ========================================
# CONFIGURAZIONE - MODIFICA QUI
# ========================================
DATA_FILE = "data.json"
STATIC_UPLOADS = "static/uploads"
STATIC_GENERATED = "static/generated"

# Groq AI API (per chat intelligente)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

# Flask
FLASK_SECRET = os.getenv("FLASK_SECRET", secrets.token_urlsafe(32))
PORT = int(os.getenv("PORT", 10000))
DEBUG = os.getenv("DEBUG", "0") == "1"

# Gumroad - MODIFICA QUESTI
GUMROAD_PRODUCT_URL = "https://micheleguerra.gumroad.com/l/emi-premium"
GUMROAD_PING_SECRET = os.getenv("GUMROAD_SECRET", "")  # Opzionale per sicurezza

# ========================================
# APP SETUP
# ========================================
app = Flask(__name__)
app.secret_key = FLASK_SECRET

client = None
if GROQ_AVAILABLE and GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq AI: Attivo")
    except Exception as e:
        print(f"⚠️ Groq AI: {e}")
else:
    print("⚠️ Groq AI: Non disponibile (risposte demo)")

os.makedirs(STATIC_UPLOADS, exist_ok=True)
os.makedirs(STATIC_GENERATED, exist_ok=True)

# ========================================
# DATABASE (JSON FILE)
# ========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "valid_codes": [], "used_codes": [], "payments": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "valid_codes": [], "used_codes": [], "payments": []}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DATA, f, indent=2, ensure_ascii=False)
    except Exception as e:
        app.logger.error(f"Save error: {e}")

DATA = load_data()
USERS = DATA.get("users", {})
VALID_PREMIUM_CODES = set(DATA.get("valid_codes", []))
USED_PREMIUM_CODES = set(DATA.get("used_codes", []))
PAYMENTS = DATA.get("payments", [])

FREE_DAILY_LIMIT = 20
HISTORY_FREE = 8
HISTORY_PREMIUM = 40

# ========================================
# UTILITY FUNCTIONS
# ========================================
def now_ymd():
    return datetime.utcnow().strftime("%Y-%m-%d")

def reset_daily_if_needed(u):
    if not u:
        return
    today = now_ymd()
    if "daily_count" not in u:
        u["daily_count"] = {"date": today, "count": 0}
    dc = u["daily_count"]
    if dc.get("date") != today:
        dc["date"] = today
        dc["count"] = 0

def increment_daily(u):
    if not u:
        return 0
    reset_daily_if_needed(u)
    u["daily_count"]["count"] += 1
    return u["daily_count"]["count"]

def user_message_count(u):
    if not u:
        return 0
    reset_daily_if_needed(u)
    return u["daily_count"].get("count", 0)

def persist():
    DATA["users"] = USERS
    DATA["valid_codes"] = list(VALID_PREMIUM_CODES)
    DATA["used_codes"] = list(USED_PREMIUM_CODES)
    DATA["payments"] = PAYMENTS
    save_data()

# ========================================
# DECORATORS
# ========================================
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("welcome"))
        return f(*args, **kwargs)
    return wrapped

def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        uname = session.get("username")
        if not uname:
            return redirect(url_for("welcome"))
        u = USERS.get(uname)
        if u and u.get("is_admin"):
            return f(*args, **kwargs)
        return "Admin access required", 403
    return wrapped

# ========================================
# DEMO USER
# ========================================
if "admin" not in USERS:
    USERS["admin"] = {
        "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        "premium": True,
        "is_admin": True,
        "created_at": datetime.utcnow().isoformat(),
        "history": [],
        "daily_count": {"date": now_ymd(), "count": 0}
    }
    persist()
    print("✅ Demo user created: admin / admin123")

# ========================================
# HTML TEMPLATES
# ========================================
WELCOME_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EMI SUPER BOT</title><style>*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1rem}
.container{background:#fff;padding:3rem;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);max-width:450px;width:100%}
h1{font-size:2.5rem;color:#667eea;margin-bottom:0.5rem;text-align:center}
p{color:#666;text-align:center;margin-bottom:2rem}
.btn{width:100%;padding:1rem;margin:0.5rem 0;border:none;border-radius:10px;font-size:1rem;font-weight:600;cursor:pointer;transition:all 0.3s;text-decoration:none;display:block;text-align:center}
.btn-primary{background:#667eea;color:#fff}.btn-primary:hover{background:#5568d3;transform:translateY(-2px)}
.btn-secondary{background:#10a37f;color:#fff}.btn-secondary:hover{background:#0d8c6d}
.btn-guest{background:transparent;color:#667eea;border:2px solid #667eea}.btn-guest:hover{background:#667eea;color:#fff}
</style></head><body><div class="container"><h1>🤖 EMI SUPER BOT</h1>
<p>The world's most powerful AI assistant</p>
<a href="/register" class="btn btn-secondary">✨ Create Account</a>
<a href="/login" class="btn btn-primary">🔐 Login</a>
<form action="/guest" method="post"><button type="submit" class="btn btn-guest">👤 Continue as Guest</button></form>
</div></body></html>"""

AUTH_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{title}} - EMI SUPER BOT</title><style>*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}
.container{background:#fff;padding:3rem;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);max-width:450px;width:90%}
h1{font-size:2rem;color:#667eea;margin-bottom:2rem;text-align:center}
.flash{background:#fee;color:#c33;padding:1rem;border-radius:8px;margin-bottom:1rem;text-align:center}
input{width:100%;padding:1rem;margin:0.5rem 0;border:2px solid #e0e0e0;border-radius:10px;font-size:1rem}
input:focus{outline:none;border-color:#667eea}
button{width:100%;padding:1rem;margin:1rem 0 0.5rem 0;border:none;border-radius:10px;background:#667eea;color:#fff;font-size:1rem;font-weight:600;cursor:pointer}
button:hover{background:#5568d3}
a{display:block;text-align:center;color:#667eea;text-decoration:none;margin-top:1rem}
</style></head><body><div class="container"><h1>{{title}}</h1>
{% with messages = get_flashed_messages() %}
{% if messages %}{% for msg in messages %}<div class="flash">{{msg}}</div>{% endfor %}{% endif %}
{% endwith %}
<form method="post">
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">{{button}}</button>
</form><a href="/">← Back</a></div></body></html>"""

CHAT_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EMI SUPER BOT</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#343541;color:#ececf1;height:100vh;display:flex;flex-direction:column;overflow:hidden}
.sidebar{position:fixed;left:0;top:0;width:260px;height:100vh;background:#171717;display:flex;flex-direction:column;z-index:100}
.sidebar-top{padding:8px}
.new-chat-btn{background:transparent;border:1px solid rgba(255,255,255,0.2);color:#ececf1;padding:10px;border-radius:10px;cursor:pointer;display:flex;align-items:center;justify-content:flex-start;gap:12px;font-size:14px;width:100%}
.new-chat-btn:hover{background:rgba(255,255,255,0.1)}
.sidebar-content{flex:1;overflow-y:auto;padding:8px}
.user-section{border-top:1px solid rgba(255,255,255,0.1)}
.user-menu-item{display:flex;align-items:center;gap:12px;padding:12px;color:#ececf1;font-size:14px;cursor:pointer;background:transparent;border:none;width:100%;text-align:left}
.user-menu-item:hover{background:rgba(255,255,255,0.1)}
.user-profile-btn{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;cursor:pointer;background:transparent;border:none;width:100%;color:#ececf1}
.user-profile-btn:hover{background:rgba(255,255,255,0.1)}
.user-avatar{width:32px;height:32px;border-radius:50%;background:#19c37d;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;color:white;flex-shrink:0}
.user-details{flex:1;min-width:0}
.user-name{font-weight:500;font-size:14px;color:#ececf1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.user-email{font-size:12px;color:#8e8ea0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.menu-divider{height:1px;background:rgba(255,255,255,0.1);margin:4px 0}
.upgrade-menu-item{background:rgba(25,195,125,0.1);color:#19c37d;font-weight:500}
.upgrade-menu-item:hover{background:rgba(25,195,125,0.15)}
.main{margin-left:260px;flex:1;display:flex;flex-direction:column;height:100vh}
.chat-container{flex:1;overflow-y:auto;padding:2rem 1rem}
.message{padding:1.5rem;margin:0.5rem auto;max-width:800px;width:100%;display:flex;gap:1.5rem}
.message.user{background:#343541}
.message.bot{background:#444654}
.avatar{width:40px;height:40px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;flex-shrink:0}
.message-content{flex:1;line-height:1.6;white-space:pre-wrap;word-wrap:break-word}
.message-content strong{font-weight:600;color:#fff}
.input-area{border-top:1px solid #565869;padding:1rem;background:#343541}
.input-container{max-width:800px;margin:0 auto;position:relative}
.input-wrapper{display:flex;gap:0.5rem;align-items:flex-end}
#messageInput{flex:1;padding:1rem 3rem 1rem 1rem;border:1px solid #565869;border-radius:12px;background:#40414f;color:#ececf1;font-size:1rem;resize:none;min-height:52px;max-height:200px;font-family:inherit}
#messageInput:focus{outline:none;border-color:#8e8ea0}
.attach-btn{width:44px;height:44px;border:none;border-radius:8px;background:transparent;color:#8e8ea0;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}
.attach-btn:hover{background:rgba(255,255,255,0.1)}
#sendBtn{position:absolute;right:0.5rem;bottom:0.5rem;width:40px;height:40px;border:none;border-radius:8px;background:#19c37d;color:white;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.2rem}
#sendBtn:hover{background:#15a76a}
#sendBtn:disabled{background:#565869;cursor:not-allowed}
.file-preview{display:flex;gap:0.5rem;margin-bottom:0.5rem;flex-wrap:wrap}
.file-preview-item{position:relative;max-width:100px;max-height:100px;border-radius:8px;overflow:hidden;border:1px solid #565869}
.file-preview-item img,.file-preview-item video{width:100%;height:100%;object-fit:cover}
.file-preview-remove{position:absolute;top:4px;right:4px;background:rgba(0,0,0,0.7);color:white;border:none;border-radius:50%;width:20px;height:20px;cursor:pointer;font-size:12px}
.message img,.message video{max-width:300px;border-radius:8px;margin-top:0.5rem}
.loading{display:flex;gap:0.3rem;padding:0.5rem 0}
.loading div{width:8px;height:8px;border-radius:50%;background:#8e8ea0;animation:bounce 1.4s infinite ease-in-out both}
.loading div:nth-child(1){animation-delay:-0.32s}
.loading div:nth-child(2){animation-delay:-0.16s}
@keyframes bounce{0%,80%,100%{transform:scale(0)}40%{transform:scale(1)}}
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:1000;align-items:center;justify-content:center}
.modal.active{display:flex}
.modal-content{background:#202123;padding:2rem;border-radius:16px;max-width:500px;width:90%;max-height:90vh;overflow-y:auto}
.modal h2{color:#ececf1;margin-bottom:1rem;font-size:1.5rem}
.modal p{color:#8e8ea0;margin-bottom:1.5rem;line-height:1.6}
.pricing-card{background:#2a2b32;border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:1.5rem;margin:1rem 0}
.pricing-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem}
.pricing-title{font-size:1.25rem;font-weight:600;color:#ececf1}
.pricing-badge{background:#19c37d;color:white;padding:0.25rem 0.75rem;border-radius:12px;font-size:0.75rem;font-weight:600}
.pricing-price{font-size:2rem;font-weight:700;color:#ececf1;margin-bottom:0.5rem}
.pricing-period{color:#8e8ea0;font-size:0.9rem;margin-bottom:1.5rem}
.modal ul{list-style:none;margin:1rem 0 1.5rem 0}
.modal li{padding:0.75rem 0;padding-left:2rem;position:relative;color:#ececf1;line-height:1.5}
.modal li:before{content:"✓";position:absolute;left:0;color:#19c37d;font-weight:bold;font-size:1.2rem}
.modal input{width:100%;padding:0.75rem;margin:1rem 0;border:1px solid rgba(255,255,255,0.2);border-radius:8px;background:#40414f;color:#ececf1;font-size:14px}
.modal input:focus{outline:none;border-color:#19c37d}
.modal-buttons{display:flex;gap:0.75rem;margin-top:1.5rem}
.modal button{flex:1;padding:0.875rem;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:14px;transition:all 0.2s}
.modal .btn-buy{background:#19c37d;color:white}
.modal .btn-buy:hover{background:#17a86f}
.modal .btn-code{background:transparent;border:1px solid rgba(255,255,255,0.2);color:#ececf1}
.modal .btn-code:hover{background:rgba(255,255,255,0.1)}
.modal .btn-close{background:transparent;border:1px solid rgba(255,255,255,0.2);color:#ececf1}
.modal .btn-close:hover{background:rgba(255,255,255,0.1)}
@media (max-width:768px){
.sidebar{width:100%;transform:translateX(-100%);transition:transform 0.3s;z-index:200}
.sidebar.mobile-open{transform:translateX(0)}
.main{margin-left:0}
.mobile-header{display:flex;align-items:center;justify-content:space-between;padding:1rem;background:#343541;border-bottom:1px solid rgba(255,255,255,0.1)}
.mobile-menu-btn{background:transparent;border:none;color:#ececf1;font-size:1.5rem;cursor:pointer;padding:0.5rem}
.mobile-title{font-size:1rem;font-weight:600;color:#ececf1}
.mobile-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:199}
.mobile-overlay.active{display:block}
}
@media (min-width:769px){
.mobile-header{display:none}
.mobile-overlay{display:none!important}
}
</style></head><body>
<div class="mobile-header">
<button class="mobile-menu-btn" onclick="toggleMobileSidebar()">☰</button>
<div class="mobile-title">EMI SUPER BOT</div>
<button class="mobile-menu-btn" onclick="location.reload()">+</button>
</div>
<div class="mobile-overlay" id="mobileOverlay" onclick="closeMobileSidebar()"></div>
<div class="sidebar" id="sidebar">
<div class="sidebar-top">
<button type="button" class="new-chat-btn" onclick="location.reload()">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
<path d="M12 5v14M5 12h14"/></svg><span>New chat</span>
</button>
</div>
<div class="sidebar-content"></div>
<div class="user-section">
{% if is_guest %}
<button type="button" class="user-profile-btn" onclick="location.href='/register'">
<div class="user-avatar">?</div>
<div class="user-details"><div class="user-name">Sign up</div></div>
</button>
<div class="menu-divider"></div>
<button type="button" class="user-menu-item" onclick="location.href='/login'">
<span>Log in</span>
</button>
{% else %}
<button type="button" class="user-profile-btn">
<div class="user-avatar">{{username[0].upper()}}</div>
<div class="user-details">
<div class="user-name">{{username}}</div>
<div class="user-email">{% if premium %}EMI Plus{% else %}Free plan{% endif %}</div>
</div>
</button>
<div class="menu-divider"></div>
{% if not premium %}
<button type="button" class="user-menu-item upgrade-menu-item" onclick="showPremium()">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
<span>Upgrade plan</span>
</button>
<div class="menu-divider"></div>
{% endif %}
<button type="button" class="user-menu-item" onclick="location.href='/logout'">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></svg>
<span>Log out</span>
</button>
{% endif %}
</div>
</div>
<div class="main">
<div class="chat-container" id="chatContainer">
{% for msg in history %}
<div class="message {{msg.role}}">
<div class="avatar">{{'👤' if msg.role=='user' else '🤖'}}</div>
<div class="message-content">{{msg.content}}</div>
</div>
{% endfor %}
</div>
<div class="input-area">
<div class="input-container">
<div class="file-preview" id="filePreview"></div>
<div class="input-wrapper">
<button type="button" class="attach-btn" onclick="handleAttachClick()" title="Attach images or videos">📷</button>
<button type="button" class="attach-btn" onclick="handleGenerateClick()" title="Generate image with AI">🎨</button>
<input type="file" id="fileInput" accept="image/*,video/*" multiple style="display:none">
<textarea id="messageInput" placeholder="Message EMI SUPER BOT..." rows="1"></textarea>
<button type="button" id="sendBtn">▲</button>
</div>
</div>
</div>
</div>
<div class="modal" id="premiumModal">
<div class="modal-content">
<h2>Upgrade to EMI Plus</h2>
<p>Get unlimited access with our most powerful AI model</p>
<div class="pricing-card">
<div class="pricing-header">
<div class="pricing-title">EMI SUPER BOT Plus</div>
<div class="pricing-badge">RECOMMENDED</div>
</div>
<div class="pricing-price">€15<span style="font-size:1rem;font-weight:400;color:#8e8ea0;">/mese</span></div>
<div class="pricing-period">Fatturazione mensile</div>
<ul>
<li>Unlimited messages with 70B AI model</li>
<li>Zero errors - Perfect accuracy guaranteed</li>
<li>Real-time information and web search</li>
<li>Extended conversation history (40 pairs)</li>
<li>Priority response time</li>
<li>Image and video support</li>
<li>Early access to new features</li>
</ul>
<div class="modal-buttons">
<button type="button" class="btn-buy" onclick="window.open('{{buy_link}}','_blank')">
💳 Buy via Gumroad
</button>
<button type="button" class="btn-code" onclick="showCodeInput()">
Have a code?
</button>
</div>
</div>
<div id="codeInput" style="display:none">
<input type="text" id="premiumCode" placeholder="Enter your activation code">
<button type="button" class="btn-buy" onclick="redeemCode()" style="width:100%">Activate</button>
</div>
<button type="button" class="btn-close" onclick="hidePremium()" style="margin-top:1rem;width:100%">Cancel</button>
</div>
</div>
<script>
const chatContainer=document.getElementById('chatContainer');
const messageInput=document.getElementById('messageInput');
const sendBtn=document.getElementById('sendBtn');
const filePreview=document.getElementById('filePreview');
const fileInput=document.getElementById('fileInput');
let selectedFiles=[];
sendBtn.addEventListener('click',sendMessage);
fileInput.addEventListener('change',handleFileSelect);
function handleAttachClick(){fileInput.click()}
function handleGenerateClick(){generateImage()}
function handleFileSelect(e){
const files=Array.from(e.target.files);
files.forEach(file=>{
if(file.type.startsWith('image/')||file.type.startsWith('video/')){
selectedFiles.push(file);
displayFilePreview(file);
}
});
}
function displayFilePreview(file){
const reader=new FileReader();
reader.onload=function(e){
const item=document.createElement('div');
item.className='file-preview-item';
if(file.type.startsWith('image/')){
item.innerHTML=`<img src="${e.target.result}"><button class="file-preview-remove" onclick="removeFile('${file.name}')">×</button>`;
}else if(file.type.startsWith('video/')){
item.innerHTML=`<video src="${e.target.result}"></video><button class="file-preview-remove" onclick="removeFile('${file.name}')">×</button>`;
}
filePreview.appendChild(item);
};
reader.readAsDataURL(file);
}
function removeFile(fileName){
selectedFiles=selectedFiles.filter(f=>f.name!==fileName);
filePreview.innerHTML='';
selectedFiles.forEach(f=>displayFilePreview(f));
fileInput.value='';
}
messageInput.addEventListener('input',function(){
this.style.height='auto';
this.style.height=this.scrollHeight+'px';
});
messageInput.addEventListener('keydown',function(e){
if(e.key==='Enter'&&!e.shiftKey){
e.preventDefault();
sendMessage();
}
});
async function sendMessage(){
const message=messageInput.value.trim();
if(!message&&selectedFiles.length===0)return;
sendBtn.disabled=true;
messageInput.disabled=true;
let fileUrls=[];
if(selectedFiles.length>0){
for(const file of selectedFiles){
const formData=new FormData();
formData.append('file',file);
try{
const res=await fetch('/upload',{method:'POST',body:formData});
const data=await res.json();
if(data.url)fileUrls.push(data.url);
}catch(err){console.error('Upload error:',err)}
}
}
let fullMessage=message;
if(fileUrls.length>0){
fullMessage+='\n\n'+fileUrls.map(url=>`[Attached: ${url}]`).join('\n');
}
let userContent=message;
if(fileUrls.length>0){
userContent+='<br>'+fileUrls.map(url=>{
if(url.match(/\.(jpg|jpeg|png|gif|webp)$/i)){
return `<img src="${url}">`;
}else if(url.match(/\.(mp4|webm|mov)$/i)){
return `<video src="${url}" controls></video>`;
}
return `<a href="${url}" target="_blank">View file</a>`;
}).join('');
}
addMessage('user',userContent);
messageInput.value='';
messageInput.style.height='auto';
