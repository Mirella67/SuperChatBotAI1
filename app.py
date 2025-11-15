# app.py - EMI SUPER BOT (complete single-file)
# Save as app.py in project root. Requires: Flask, bcrypt, groq (optional)
# Comments in Italian.

import os
import time
import secrets
import json
from datetime import datetime
from functools import wraps
from hashlib import sha1
from hmac import new as hmac_new

from flask import (
    Flask, request, jsonify, session, render_template,
    redirect, url_for, send_from_directory, flash
)
import bcrypt

# If you use Groq, keep import; if not available it's optional.
try:
    from groq import Groq
except Exception:
    Groq = None

# ---------------------------
# CONFIG
# ---------------------------
DATA_FILE = "data.json"
STATIC_UPLOADS = "static/uploads"
STATIC_GENERATED = "static/generated"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
FLASK_SECRET = os.getenv("FLASK_SECRET", secrets.token_urlsafe(32))
ADMIN_PASSWORD_ENV = os.getenv("ADMIN_PASSWORD", None)
BUY_LINK = os.getenv("BUY_LINK", "https://micheleguerra.gumroad.com/")
GUMROAD_SECRET = os.getenv("GUMROAD_SECRET", None)
PORT = int(os.getenv("PORT", "10000"))
DEBUG = os.getenv("DEBUG", "0") == "1"

# App init
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = FLASK_SECRET
if Groq and GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

# Ensure static folders exist
os.makedirs(STATIC_UPLOADS, exist_ok=True)
os.makedirs(STATIC_GENERATED, exist_ok=True)

# ---------------------------
# Persistence helpers
# ---------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        app.logger.error("load_data error: %s", e)
        return {}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DATA, f, indent=2, ensure_ascii=False)
    except Exception as e:
        app.logger.error("save_data error: %s", e)

# Load initial data
DATA = load_data()
USERS = DATA.get("users", {})  # dict: username -> user dict
VALID_PREMIUM_CODES = set(DATA.get("valid_codes", []))
USED_PREMIUM_CODES = set(DATA.get("used_codes", []))

# defaults / limits
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "20"))
HISTORY_FREE = int(os.getenv("HISTORY_FREE", "8"))
HISTORY_PREMIUM = int(os.getenv("HISTORY_PREMIUM", "40"))

# ---------------------------
# Utility helpers
# ---------------------------
def now_ymd():
    return datetime.utcnow().strftime("%Y-%m-%d")

def reset_daily_if_needed(u):
    today = now_ymd()
    dc = u.setdefault("daily_count", {"date": today, "count": 0})
    if dc.get("date") != today:
        dc["date"] = today
        dc["count"] = 0

def increment_daily(u):
    reset_daily_if_needed(u)
    u["daily_count"]["count"] += 1
    return u["daily_count"]["count"]

def user_message_count(u):
    reset_daily_if_needed(u)
    return u["daily_count"]["count"]

def persist_users_and_codes():
    DATA["users"] = USERS
    DATA["valid_codes"] = list(VALID_PREMIUM_CODES)
    DATA["used_codes"] = list(USED_PREMIUM_CODES)
    save_data()

def canonical_pw_hash(pw_plain: str):
    return bcrypt.hashpw(pw_plain.encode(), bcrypt.gensalt()).decode()

def check_password_hash(maybe_hash, plaintext):
    # allow bytes or str
    if isinstance(maybe_hash, str):
        maybe_hash = maybe_hash.encode()
    return bcrypt.checkpw(plaintext.encode(), maybe_hash)

def generate_random_guest():
    return "guest_" + secrets.token_hex(4)

def get_preferred_lang():
    # use Accept-Language header for best-effort language
    al = request.headers.get("Accept-Language", "")
    if not al:
        return "en"
    # take first two letters of first tag
    try:
        lang = al.split(",")[0].split("-")[0].lower()
        return lang if lang else "en"
    except:
        return "en"

# ---------------------------
# Admin / login decorators
# ---------------------------
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
        # fallback to ADMIN_PASSWORD_ENV via query/header/form
        supplied = request.args.get("admin_pw") or request.form.get("admin_pw") or request.headers.get("X-Admin-Pw")
        if ADMIN_PASSWORD_ENV and supplied == ADMIN_PASSWORD_ENV:
            return f(*args, **kwargs)
        return "Admin access required", 403
    return wrapped

# ---------------------------
# Initial demo users (if not present)
# ---------------------------
def ensure_demo_users():
    changed = False
    if "admin" not in USERS:
        pw = "sB5Zj_@=ymQ!QGmd"
        USERS["admin"] = {
            "password_hash": bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode(),
            "premium": True,
            "is_admin": True,
            "created_at": datetime.utcnow().isoformat(),
            "history": [],
            "daily_count": {"date": now_ymd(), "count": 0}
        }
        changed = True
    if "utente1" not in USERS:
        pw = "efKgOaM^H0Uiq*"
        USERS["utente1"] = {
            "password_hash": bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode(),
            "premium": False,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "history": [],
            "daily_count": {"date": now_ymd(), "count": 0}
        }
        changed = True
    if "premiumtester" not in USERS:
        pw = "CtBVZ2)i!j4AosyT"
        USERS["premiumtester"] = {
            "password_hash": bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode(),
            "premium": True,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "history": [],
            "daily_count": {"date": now_ymd(), "count": 0}
        }
        changed = True
    if changed:
        persist_users_and_codes()

ensure_demo_users()

# ---------------------------
# History cleanup: non-premium older than 30 days
# ---------------------------
def cleanup_history(username):
    u = USERS.get(username)
    if not u:
        return
    if u.get("premium"):
        return  # premium keep forever
    cutoff = time.time() - (30 * 24 * 60 * 60)
    if "history" in u:
        u["history"] = [m for m in u["history"] if m.get("ts", 0) >= cutoff]
        persist_users_and_codes()

# ---------------------------
# Routes: welcome / guest / auth
# ---------------------------
@app.route("/", methods=["GET"])
def welcome():
    # show landing with Login / Register / Entra come ospite
    # detect lang and store in session
    session.setdefault("lang", get_preferred_lang())
    return render_template("welcome.html", lang=session.get("lang", "en"))

@app.route("/guest", methods=["POST"])
def guest():
    # create transient guest session: do NOT persist chat history for guests
    uname = generate_random_guest()
    session["username"] = uname
    session["is_guest"] = True
    # no persistent user entry in USERS
    session.setdefault("lang", get_preferred_lang())
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = (request.form.get("username") or "").strip()
        pw = (request.form.get("password") or "")
        if not uname or not pw:
            flash("Username and password required")
            return render_template("auth.html", title="Register", button="Create account", extra=None)
        if uname in USERS:
            flash("Username already exists")
            return render_template("auth.html", title="Register", button="Create account", extra=None)
        USERS[uname] = {
            "password_hash": bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode(),
            "premium": False,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "history": [],
            "daily_count": {"date": now_ymd(), "count": 0}
        }
        persist_users_and_codes()
        session["username"] = uname
        session.pop("is_guest", None)
        return redirect(url_for("home"))
    # GET
    session.setdefault("lang", get_preferred_lang())
    return render_template("auth.html", title="Register", button="Create account", extra=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = (request.form.get("username") or "").strip()
        pw = (request.form.get("password") or "")
        if not uname or not pw:
            flash("Username and password required")
            return render_template("auth.html", title="Login", button="Login", extra=None)
        u = USERS.get(uname)
        if not u:
            flash("Invalid credentials")
            return render_template("auth.html", title="Login", button="Login", extra=None)
        ph = u.get("password_hash")
        if isinstance(ph, str):
            ph = ph.encode()
        if ph and bcrypt.checkpw(pw.encode(), ph):
            session["username"] = uname
            session.pop("is_guest", None)
            # cleanup old history for non-premium
            cleanup_history(uname)
            return redirect(url_for("home"))
        flash("Invalid credentials")
        return render_template("auth.html", title="Login", button="Login", extra=None)
    session.setdefault("lang", get_preferred_lang())
    return render_template("auth.html", title="Login", button="Login", extra=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("welcome"))

# ---------------------------
# Home & chat endpoints
# ---------------------------
@app.route("/home")
@login_required
def home_redirect():
    return redirect(url_for("home"))

@app.route("/chat-page")
@login_required
def chat_page():
    # older route compatibility; show home
    return redirect(url_for("home"))

@app.route("/home/", methods=["GET"])
@login_required
def home():
    uname = session.get("username")
    is_guest = session.get("is_guest", False)
    u = USERS.get(uname) if not is_guest else None
    plan = "premium" if (u and u.get("premium")) else "free"
    used = user_message_count(u) if u else 0
    history = []
    if u:
        history = [{"role": m["role"], "content": m["content"]} for m in u.get("history", [])[-(HISTORY_PREMIUM*2):]]
    # pass buy_link and language
    return render_template("home.html",
                           username=(uname if not is_guest else None),
                           plan=plan,
                           premium=(u.get("premium") if u else False),
                           created_at=(u.get("created_at") if u else ""),
                           buy_link=BUY_LINK,
                           history=history,
                           free_limit=FREE_DAILY_LIMIT,
                           used_today=used,
                           lang=session.get("lang", "en"),
                           is_guest=is_guest)

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    uname = session.get("username")
    is_guest = session.get("is_guest", False)
    u = USERS.get(uname) if not is_guest else None
    if not is_guest and not u:
        return jsonify({"error": "User not found"}), 400

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    # daily free limit for non premium
    if (not is_guest) and (not u.get("premium")):
        count = increment_daily(u)
        if count > FREE_DAILY_LIMIT:
            return jsonify({"error": "Free daily limit reached. Upgrade to premium."}), 429

    # prepare history
    max_pairs = HISTORY_PREMIUM if (u and u.get("premium")) else HISTORY_FREE
    recent = (u.get("history", []) if u else [])[-(max_pairs*2):]
    ctx = [{"role": "system", "content": "Sei EMI SUPER BOT. Rispondi nella stessa lingua dell'utente."}]
    for m in recent:
        ctx.append({"role": m["role"], "content": m["content"]})
    ctx.append({"role": "user", "content": message})

    # select model (if Groq client available)
    model = "llama-3.1-70b" if (u and u.get("premium")) else "llama-3.1-8b-instant"
    ai_text = None
    if client:
        try:
            resp = client.chat.completions.create(model=model, messages=ctx)
            ai_text = resp.choices[0].message.content
        except Exception as exc:
            app.logger.error("Model API error: %s", exc)
            ai_text = "Errore interno modello. Prova più tardi."
    else:
        # fallback: simple echo / placeholder reply
        ai_text = f"(simulated reply) I understood: {message[:200]}"

    # store history (unless guest)
    if not is_guest:
        now_ts = time.time()
        u.setdefault("history", []).append({"role": "user", "content": message, "ts": now_ts})
        u.setdefault("history", []).append({"role": "bot", "content": ai_text, "ts": time.time()})
        # trim to keep size
        max_items = (HISTORY_PREMIUM if u.get("premium") else HISTORY_FREE) * 2
        if len(u["history"]) > max_items:
            u["history"] = u["history"][-max_items:]
        persist_users_and_codes()

    return jsonify({"reply": ai_text})

# ---------------------------
# Upload endpoints (images / videos)
# ---------------------------
ALLOWED_IMG = {"png", "jpg", "jpeg", "gif", "svg", "webp"}
ALLOWED_VIDEO = {"mp4", "webm", "mov", "ogg"}

def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    # multipart form with 'file' and optional 'caption'
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400
    filename = f.filename
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    if allowed_file(filename, ALLOWED_IMG.union(ALLOWED_VIDEO)):
        safe_name = secrets.token_hex(8) + "." + ext
        dest = os.path.join(STATIC_UPLOADS, safe_name)
        f.save(dest)
        url = url_for("static", filename=f"uploads/{safe_name}", _external=True)
        uname = session.get("username")
        is_guest = session.get("is_guest", False)
        if not is_guest:
            u = USERS.get(uname)
            u.setdefault("history", []).append({"role": "user", "content": f"[uploaded file] {url}", "ts": time.time()})
            persist_users_and_codes()
        return jsonify({"ok": True, "url": url})
    else:
        return jsonify({"error": "File type not allowed"}), 400

# ---------------------------
# Simple image generator (placeholder: creates colored SVG)
# ---------------------------
@app.route("/generate-image", methods=["POST"])
@login_required
def generate_image():
    data = request.get_json() or {}
    prompt = (data.get("prompt") or "abstract").strip()[:200]
    # create a simple SVG image with prompt text and random color
    color = data.get("color") or ("#" + secrets.token_hex(3))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">
  <rect width="100%" height="100%" fill="{color}"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
    font-family="Arial" font-size="48" fill="#ffffff">{prompt[:40]}</text>
</svg>'''
    fname = f"gen_{int(time.time())}_{secrets.token_hex(4)}.svg"
    path = os.path.join(STATIC_GENERATED, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    url = url_for("static", filename=f"generated/{fname}", _external=True)
    uname = session.get("username")
    if not session.get("is_guest", False):
        u = USERS.get(uname)
        u.setdefault("history", []).append({"role": "bot", "content": f"[generated image] {url}", "ts": time.time()})
        persist_users_and_codes()
    return jsonify({"ok": True, "url": url})

# ---------------------------
# Admin: list users / generate/revoke codes
# ---------------------------
@app.route("/admin")
@admin_required
def admin():
    uv = {}
    for k, v in USERS.items():
        uv[k] = {"premium": v.get("premium"), "is_admin": v.get("is_admin"), "created_at": v.get("created_at")}
    return render_template("admin.html", users=uv, codes=sorted(list(VALID_PREMIUM_CODES)), used=USED_PREMIUM_CODES)

@app.route("/admin/generate_codes", methods=["POST"])
@admin_required
def admin_generate_codes():
    n = int(request.form.get("n", "3"))
    n = max(1, min(n, 200))
    created = []
    for _ in range(n):
        code = secrets.token_hex(6)
        VALID_PREMIUM_CODES.add(code)
        created.append(code)
    persist_users_and_codes()
    return jsonify({"created": created})

@app.route("/admin/toggle_premium/<username>", methods=["POST"])
@admin_required
def admin_toggle_premium(username):
    if username not in USERS:
        return "no user", 400
    USERS[username]["premium"] = not USERS[username].get("premium", False)
    persist_users_and_codes()
    return redirect(url_for("admin"))

@app.route("/admin/delete_user/<username>", methods=["POST"])
@admin_required
def admin_delete_user(username):
    if username in USERS:
        del USERS[username]
        persist_users_and_codes()
    return redirect(url_for("admin"))

@app.route("/admin/revoke_code", methods=["POST"])
@admin_required
def admin_revoke_code():
    code = request.form.get("code")
    if code in VALID_PREMIUM_CODES:
        VALID_PREMIUM_CODES.remove(code)
        persist_users_and_codes()
    return redirect(url_for("admin"))

# ---------------------------
# Upgrade endpoint: submit code or buy link
# ---------------------------
@app.route("/upgrade", methods=["POST"])
@login_required
def upgrade():
    uname = session.get("username")
    code = (request.form.get("code") or "").strip()
    if not code:
        flash("No code provided")
        return redirect(url_for("home"))
    if code in USED_PREMIUM_CODES:
        flash("Code already used")
        return redirect(url_for("home"))
    if code not in VALID_PREMIUM_CODES:
        flash("Invalid code")
        return redirect(url_for("home"))
    USED_PREMIUM_CODES.add(code)
    USERS[uname]["premium"] = True
    persist_users_and_codes()
    flash("Upgraded to premium. Thanks!")
    return redirect(url_for("home"))

# ---------------------------
# Gumroad webhook skeleton (demo)
# ---------------------------
def verify_gumroad_signature(payload_bytes, sig_header):
    if not GUMROAD_SECRET:
        return True
    if not sig_header:
        return False
    computed = hmac_new(GUMROAD_SECRET.encode(), payload_bytes, sha1).hexdigest()
    return computed == sig_header

@app.route("/webhook/gumroad", methods=["POST"])
def gumroad_webhook():
    payload = request.get_data()
    sig = request.headers.get("X-Gumroad-Signature") or request.headers.get("x-gumroad-signature")
    if GUMROAD_SECRET and not verify_gumroad_signature(payload, sig):
        return "invalid signature", 403
    # create code for demo
    code = secrets.token_hex(6)
    VALID_PREMIUM_CODES.add(code)
    persist_users_and_codes()
    return jsonify({"ok": True, "code": code})

# ---------------------------
# Health
# ---------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok", "ts": time.time()})

# ---------------------------
# Error handlers (logs)
# ---------------------------
@app.errorhandler(500)
def internal_error(e):
    app.logger.exception("Internal server error:")
    return render_template("500.html") if os.path.exists("templates/500.html") else ("Internal Server Error", 500)

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    # ensure DATA reflects current USERS and codes before run
    persist_users_and_codes()
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
