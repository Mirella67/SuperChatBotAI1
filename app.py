# ============================================
# EMI SUPER BOT - IL BOT PIÙ POTENTE AL MONDO
# Supera ChatGPT, Claude, Gemini combinati
# ============================================
#
# INSTALLAZIONE RAPIDA:
# 1. pip install flask bcrypt groq
# 2. python app.py
# 3. Apri http://localhost:10000
#
# Account demo: admin / admin123
# ============================================

import os
import time
import secrets
import json
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, request, jsonify, session, render_template_string, redirect, url_for, flash
import bcrypt

try:
    from groq import Groq
    GROQ_OK = True
except:
    GROQ_OK = False

# ============================================
# CONFIGURAZIONE
# ============================================
DATA_FILE = "data.json"
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/generated", exist_ok=True)

GROQ_API_KEY = "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"
GUMROAD_URL = "https://micheleguerra.gumroad.com/l/emi-premium"

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)

client = None
if GROQ_OK and GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ AI Engine: Active")
    except:
        print("⚠️ AI Engine: Demo mode")

# ============================================
# DATABASE
# ============================================
def load():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "codes": [], "used": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "codes": [], "used": []}

def save():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(DB, f, indent=2)
    except Exception as e:
        print(f"❌ Save error: {e}")

DB = load()
USERS = DB.get("users", {})
CODES = set(DB.get("codes", []))
USED = set(DB.get("used", []))

# ============================================
# UTILITY
# ============================================
def today():
    return datetime.utcnow().strftime("%Y-%m-%d")

def persist():
    DB["users"] = USERS
    DB["codes"] = list(CODES)
    DB["used"] = list(USED)
    save()

def login_required(f):
    @wraps(f)
    def wrap(*a, **k):
        if "user" not in session:
            return redirect(url_for("welcome"))
        return f(*a, **k)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*a, **k):
        u = session.get("user")
        if not u or not USERS.get(u, {}).get("admin"):
            return "Admin only", 403
        return f(*a, **k)
    return wrap

# ============================================
# DEMO USER
# ============================================
if "admin" not in USERS:
    USERS["admin"] = {
        "pw": bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
        "premium": True,
        "admin": True,
        "history": [],
        "count": {"date": today(), "n": 0}
    }
    persist()
    print("✅ Demo: admin / admin123")

# ============================================
# TEMPLATES
# ============================================
WELCOME = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EMI SUPER BOT</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui,-apple-system,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}.box{background:#fff;padding:40px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.3);max-width:400px;width:100%}h1{font-size:2.5rem;color:#667eea;text-align:center;margin-bottom:10px}p{color:#666;text-align:center;margin-bottom:30px}.btn{width:100%;padding:15px;margin:10px 0;border:none;border-radius:10px;font-size:16px;font-weight:600;cursor:pointer;text-decoration:none;display:block;text-align:center;transition:all .3s}.primary{background:#667eea;color:#fff}.primary:hover{background:#5568d3;transform:translateY(-2px)}.secondary{background:#10a37f;color:#fff}.secondary:hover{background:#0d8c6d}.guest{background:transparent;color:#667eea;border:2px solid #667eea}.guest:hover{background:#667eea;color:#fff}
</style></head><body><div class="box"><h1>🤖 EMI SUPER BOT</h1><p>The world's most powerful AI</p><a href="/register" class="btn secondary">✨ Create Account</a><a href="/login" class="btn primary">🔐 Login</a><form action="/guest" method="post"><button type="submit" class="btn guest">👤 Guest Mode</button></form></div></body></html>"""

AUTH = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{title}}</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui,-apple-system,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center}.box{background:#fff;padding:40px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.3);max-width:400px;width:90%}h1{font-size:2rem;color:#667eea;text-align:center;margin-bottom:30px}.flash{background:#fee;color:#c33;padding:15px;border-radius:8px;margin-bottom:15px;text-align:center}input{width:100%;padding:15px;margin:10px 0;border:2px solid #e0e0e0;border-radius:10px;font-size:16px}input:focus{outline:none;border-color:#667eea}button{width:100%;padding:15px;margin:15px 0 10px;border:none;border-radius:10px;background:#667eea;color:#fff;font-size:16px;font-weight:600;cursor:pointer}button:hover{background:#5568d3}a{display:block;text-align:center;color:#667eea;text-decoration:none;margin-top:15px}
</style></head><body><div class="box"><h1>{{title}}</h1>
{% with messages = get_flashed_messages() %}
{% if messages %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endif %}
{% endwith %}
<form method="post">
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<button>{{btn}}</button>
</form><a href="/">← Back</a></div></body></html>"""

CHAT = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EMI SUPER BOT</title>
<script>
window.userData = {
  username: "{{user}}",
  premium: {{premium|tojson}},
  isGuest: {{guest|tojson}},
  history: {{history|tojson}},
  freeLimit: {{limit}},
  used: {{used}},
  gumroad: "{{gumroad}}"
};
</script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#343541;color:#ececf1;height:100vh;display:flex;flex-direction:column;overflow:hidden}
.sidebar{position:fixed;left:0;top:0;width:260px;height:100vh;background:#171717;display:flex;flex-direction:column;z-index:100;transition:transform .3s}
.sidebar-top{padding:10px}
.new-btn{background:transparent;border:1px solid rgba(255,255,255,.2);color:#ececf1;padding:12px;border-radius:10px;cursor:pointer;display:flex;align-items:center;gap:10px;font-size:14px;width:100%}
.new-btn:hover{background:rgba(255,255,255,.1)}
.sidebar-content{flex:1;overflow-y:auto}
.user-section{border-top:1px solid rgba(255,255,255,.1);padding:10px}
.user-btn{display:flex;align-items:center;gap:10px;padding:12px;color:#ececf1;font-size:14px;cursor:pointer;background:transparent;border:none;width:100%;border-radius:8px}
.user-btn:hover{background:rgba(255,255,255,.1)}
.avatar{width:32px;height:32px;border-radius:50%;background:#19c37d;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;color:#fff;flex-shrink:0}
.user-info{flex:1;min-width:0}
.user-name{font-weight:500;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.user-plan{font-size:12px;color:#8e8ea0}
.divider{height:1px;background:rgba(255,255,255,.1);margin:4px 0}
.upgrade-btn{background:rgba(25,195,125,.1);color:#19c37d;font-weight:500}
.upgrade-btn:hover{background:rgba(25,195,125,.15)}
.main{margin-left:260px;flex:1;display:flex;flex-direction:column;height:100vh}
.chat{flex:1;overflow-y:auto;padding:20px}
.msg{padding:20px;margin:10px auto;max-width:800px;width:100%;display:flex;gap:15px}
.msg.user{background:#343541}
.msg.bot{background:#444654}
.msg-avatar{width:40px;height:40px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0}
.msg-content{flex:1;line-height:1.6;white-space:pre-wrap;word-wrap:break-word}
.msg-content strong{font-weight:600;color:#fff}
.msg-content img,.msg-content video{max-width:300px;border-radius:8px;margin-top:8px}
.input-area{border-top:1px solid #565869;padding:15px;background:#343541}
.input-box{max-width:800px;margin:0 auto;position:relative}
.input-wrap{display:flex;gap:8px;align-items:flex-end}
#msg{flex:1;padding:12px 50px 12px 12px;border:1px solid #565869;border-radius:12px;background:#40414f;color:#ececf1;font-size:16px;resize:none;min-height:52px;max-height:200px;font-family:inherit}
#msg:focus{outline:none;border-color:#8e8ea0}
.tool-btn{width:44px;height:44px;border:none;border-radius:8px;background:transparent;color:#8e8ea0;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
.tool-btn:hover{background:rgba(255,255,255,.1)}
#send{position:absolute;right:8px;bottom:8px;width:40px;height:40px;border:none;border-radius:8px;background:#19c37d;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:20px}
#send:hover{background:#15a76a}
#send:disabled{background:#565869;cursor:not-allowed}
.preview{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.preview-item{position:relative;max-width:100px;max-height:100px;border-radius:8px;overflow:hidden;border:1px solid #565869}
.preview-item img,.preview-item video{width:100%;height:100%;object-fit:cover}
.preview-remove{position:absolute;top:4px;right:4px;background:rgba(0,0,0,.7);color:#fff;border:none;border-radius:50%;width:20px;height:20px;cursor:pointer;font-size:12px}
.loading{display:flex;gap:5px;padding:8px 0}
.loading div{width:8px;height:8px;border-radius:50%;background:#8e8ea0;animation:bounce 1.4s infinite ease-in-out both}
.loading div:nth-child(1){animation-delay:-.32s}
.loading div:nth-child(2){animation-delay:-.16s}
@keyframes bounce{0%,80%,100%{transform:scale(0)}40%{transform:scale(1)}}
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);z-index:1000;align-items:center;justify-content:center;padding:20px}
.modal.show{display:flex}
.modal-box{background:#202123;padding:30px;border-radius:16px;max-width:500px;width:100%;max-height:90vh;overflow-y:auto}
.modal h2{color:#ececf1;margin-bottom:15px;font-size:24px}
.modal p{color:#8e8ea0;margin-bottom:20px;line-height:1.6}
.price-card{background:#2a2b32;border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:20px;margin:15px 0}
.price-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:15px}
.price-title{font-size:20px;font-weight:600;color:#ececf1}
.price-badge{background:#19c37d;color:#fff;padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600}
.price-amount{font-size:32px;font-weight:700;color:#ececf1;margin-bottom:8px}
.price-period{color:#8e8ea0;font-size:14px;margin-bottom:20px}
.modal ul{list-style:none;margin:15px 0 20px}
.modal li{padding:12px 0 12px 30px;position:relative;color:#ececf1;line-height:1.5}
.modal li:before{content:"✓";position:absolute;left:0;color:#19c37d;font-weight:bold;font-size:18px}
.modal input{width:100%;padding:12px;margin:15px 0;border:1px solid rgba(255,255,255,.2);border-radius:8px;background:#40414f;color:#ececf1;font-size:14px}
.modal input:focus{outline:none;border-color:#19c37d}
.modal-btns{display:flex;gap:10px;margin-top:20px}
.modal button{flex:1;padding:14px;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:14px;transition:all .2s}
.btn-buy{background:#19c37d;color:#fff}
.btn-buy:hover{background:#17a86f}
.btn-code{background:transparent;border:1px solid rgba(255,255,255,.2);color:#ececf1}
.btn-code:hover{background:rgba(255,255,255,.1)}
.btn-close{background:transparent;border:1px solid rgba(255,255,255,.2);color:#ececf1}
.btn-close:hover{background:rgba(255,255,255,.1)}
@media (max-width:768px){
.sidebar{width:100%;transform:translateX(-100%)}
.sidebar.open{transform:translateX(0)}
.main{margin-left:0}
.mobile-header{display:flex;align-items:center;justify-content:space-between;padding:15px;background:#343541;border-bottom:1px solid rgba(255,255,255,.1)}
.mobile-btn{background:transparent;border:none;color:#ececf1;font-size:24px;cursor:pointer;padding:8px}
.mobile-title{font-size:16px;font-weight:600}
.overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:99}
.overlay.show{display:block}
}
@media (min-width:769px){
.mobile-header,.overlay{display:none!important}
}
</style>
</head>
<body>
<div class="mobile-header">
<button class="mobile-btn" onclick="toggleSidebar()">☰</button>
<div class="mobile-title">EMI SUPER BOT</div>
<button class="mobile-btn" onclick="newChat()">+</button>
</div>
<div class="overlay" id="overlay" onclick="closeSidebar()"></div>
<div class="sidebar" id="sidebar">
<div class="sidebar-top">
<button class="new-btn" onclick="newChat()">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
<path d="M12 5v14M5 12h14"/></svg><span>New chat</span>
</button>
</div>
<div class="sidebar-content"></div>
<div class="user-section">
{% if guest %}
<button class="user-btn" onclick="location.href='/register'">
<div class="avatar">?</div>
<div class="user-info"><div class="user-name">Sign up</div></div>
</button>
<div class="divider"></div>
<button class="user-btn" onclick="location.href='/login'"><span>Log in</span></button>
{% else %}
<button class="user-btn">
<div class="avatar">{{user[0].upper()}}</div>
<div class="user-info">
<div class="user-name">{{user}}</div>
<div class="user-plan">{% if premium %}EMI Plus{% else %}Free{% endif %}</div>
</div>
</button>
<div class="divider"></div>
{% if not premium %}
<button class="user-btn upgrade-btn" onclick="showUpgrade()">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg><span>Upgrade</span>
</button>
<div class="divider"></div>
{% endif %}
<button class="user-btn" onclick="location.href='/logout'">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></svg><span>Logout</span>
</button>
{% endif %}
</div>
</div>
<div class="main">
<div class="chat" id="chat"></div>
<div class="input-area">
<div class="input-box">
<div class="preview" id="preview"></div>
<div class="input-wrap">
<button class="tool-btn" onclick="attachFile()" title="Upload image/video">📷</button>
<button class="tool-btn" onclick="generateImg()" title="Generate AI image">🎨</button>
<input type="file" id="file" accept="image/*,video/*" multiple style="display:none">
<textarea id="msg" placeholder="Message EMI SUPER BOT..." rows="1"></textarea>
<button id="send">▲</button>
</div>
</div>
</div>
</div>
<div class="modal" id="modal">
<div class="modal-box">
<h2>Upgrade to EMI Plus</h2>
<p>Unlock the full power of the world's best AI</p>
<div class="price-card">
<div class="price-header">
<div class="price-title">EMI SUPER BOT Plus</div>
<div class="price-badge">BEST VALUE</div>
</div>
<div class="price-amount">€15<span style="font-size:16px;font-weight:400;color:#8e8ea0">/month</span></div>
<div class="price-period">Cancel anytime</div>
<ul>
<li>Unlimited messages - no limits</li>
<li>Most powerful 70B AI model</li>
<li>Perfect accuracy - zero errors</li>
<li>Extended 40-pair history</li>
<li>Priority response speed</li>
<li>Image & video support</li>
<li>AI image generation</li>
<li>Early feature access</li>
</ul>
<div class="modal-btns">
<button class="btn-buy" onclick="buyNow()">💳 Buy Now</button>
<button class="btn-code" onclick="showCode()">Have code?</button>
</div>
</div>
<div id="codeBox" style="display:none">
<input type="text" id="code" placeholder="Enter activation code">
<button class="btn-buy" onclick="activateCode()" style="width:100%">Activate</button>
</div>
<button class="btn-close" onclick="hideModal()" style="margin-top:15px;width:100%">Cancel</button>
</div>
</div>
<script>
const d=window.userData;
const chat=document.getElementById('chat');
const msg=document.getElementById('msg');
const send=document.getElementById('send');
const preview=document.getElementById('preview');
const file=document.getElementById('file');
const modal=document.getElementById('modal');
let files=[];

// Load history
if(d.history && d.history.length){
  d.history.forEach(m=>{
    addMsg(m.role,m.content);
  });
}

// Auto-resize textarea
msg.addEventListener('input',()=>{
  msg.style.height='auto';
  msg.style.height=msg.scrollHeight+'px';
});

// Send on Enter
msg.addEventListener('keydown',e=>{
  if(e.key==='Enter' && !e.shiftKey){
    e.preventDefault();
    sendMsg();
  }
});

// Send button
send.addEventListener('click',sendMsg);

// File input
file.addEventListener('change',e=>{
  Array.from(e.target.files).forEach(f=>{
    if(f.type.startsWith('image/') || f.type.startsWith('video/')){
      files.push(f);
      showPreview(f);
    }
  });
});

function showPreview(f){
  const reader=new FileReader();
  reader.onload=e=>{
    const div=document.createElement('div');
    div.className='preview-item';
    if(f.type.startsWith('image/')){
      div.innerHTML=`<img src="${e.target.result}"><button class="preview-remove" onclick="removeFile('${f.name}')">×</button>`;
    }else{
      div.innerHTML=`<video src="${e.target.result}"></video><button class="preview-remove" onclick="removeFile('${f.name}')">×</button>`;
    }
    preview.appendChild(div);
  };
  reader.readAsDataURL(f);
}

function removeFile(name){
  files=files.filter(f=>f.name!==name);
  preview.innerHTML='';
  files.forEach(showPreview);
  file.value='';
}

function attachFile(){
  file.click();
}

async function generateImg(){
  const prompt=window.prompt('Describe the image to generate:');
  if(!prompt)return;
  addMsg('user',`🎨 Generate: ${prompt}`);
  const load=showLoading();
  try{
    const r=await fetch('/generate',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({prompt})
    });
    const data=await r.json();
    removeLoading(load);
    if(data.url){
      addMsg('bot',`Here's your image:<br><img src="${data.url}" style="max-width:400px;border-radius:12px;margin-top:8px">`);
    }else{
      addMsg('bot','❌ Generation failed. Try again.');
    }
  }catch(err){
    removeLoading(load);
    addMsg('bot','❌ Error generating image.');
  }
}

async function sendMsg(){
  const text=msg.value.trim();
  if(!text && !files.length)return;
  
  send.disabled=true;
  msg.disabled=true;
  
  let urls=[];
  if(files.length){
    for(const f of files){
      const fd=new FormData();
      fd.append('file',f);
      try{
        const r=await fetch('/upload',{method:'POST',body:fd});
        const data=await r.json();
        if(data.url)urls.push(data.url);
      }catch(err){console.error(err)}
    }
  }
  
  let full=text;
  if(urls.length){
    full+='\n\n'+urls.map(u=>`[File: ${u}]`).join('\n');
  }
  
  let userHtml=text;
  if(urls.length){
    userHtml+='<br>'+urls.map(u=>{
      if(u.match(/\.(jpg|jpeg|png|gif|webp)$/i)){
        return `<img src="${u}">`;
      }else if(u.match(/\.(mp4|webm|mov)$/i)){
        return `<video src="${u}" controls></video>`;
      }
      return `<a href="${u}">File</a>`;
    }).join('');
  }
  
  addMsg('user',userHtml);
  msg.value='';
  msg.style.height='auto';
  files=[];
  preview.innerHTML='';
  file.value='';
  
  const load=showLoading();
  
  try{
    const r=await fetch('/chat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:full})
    });
    const data=await r.json();
    removeLoading(load);
    if(data.error){
      addMsg('bot','❌ '+data.error);
    }else{
      addMsg('bot',data.reply);
    }
  }catch(err){
    removeLoading(load);
    addMsg('bot','❌ Connection error. Try again.');
  }
  
  send.disabled=false;
  msg.disabled=false;
  msg.focus();
}

function addMsg(role,content){
  const div=document.createElement('div');
  div.className='msg '+role;
  const formatted=role==='bot'?formatBot(content):content;
  div.innerHTML=`
    <div class="msg-avatar">${role==='user'?'👤':'🤖'}</div>
    <div class="msg-content">${formatted}</div>
  `;
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
}

function formatBot(txt){
  return txt
    .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
    .replace(/\n\n/g,'</p><p>')
    .replace(/\n•/g,'<br>•')
    .replace(/\n\d+\./g,'<br>$&')
    .replace(/\n-/g,'<br>-');
}

function showLoading(){
  const div=document.createElement('div');
  div.className='msg bot';
  div.id='load-'+Date.now();
  div.innerHTML=`
    <div class="msg-avatar">🤖</div>
    <div class="loading"><div></div><div></div><div></div></div>
  `;
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
  return div.id;
}

function removeLoading(id){
  const el=document.getElementById(id);
  if(el)el.remove();
}

function newChat(){
  location.reload();
}

function toggleSidebar(){
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('show');
}

function closeSidebar(){
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('overlay').classList.remove('show');
}

function showUpgrade(){
  modal.classList.add('show');
}

function hideModal(){
  modal.classList.remove('show');
  document.getElementById('codeBox').style.display='none';
}

function buyNow(){
  window.open(d.gumroad,'_blank
