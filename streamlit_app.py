import streamlit as st
import streamlit.components.v1 as components
import requests
import time

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & ELEGANT ALL-WHITE THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Chef AI — Culinary Companion",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Elegant All-White Design System
ELEGANT_WHITE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;1,9..144,600&family=Playfair+Display:ital,wght@0,600;0,700;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

/* Force Clean All-White Canvas */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

[data-testid="stHeader"] {
    background-color: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(8px);
}

.block-container {
    padding-top: 2.2rem !important;
    padding-bottom: 2.5rem !important;
}

/* Headings with Rich Editorial Serifs */
h1 {
    font-family: 'Playfair Display', 'Fraunces', serif !important;
    color: #0F172A !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
}

h2, h3 {
    font-family: 'Playfair Display', 'Fraunces', serif !important;
    color: #1E293B !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

h4, h5, h6 {
    font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
    color: #334155 !important;
    font-weight: 600 !important;
}

p, span, label {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #334155;
}

/* Sidebar: Crisp Editorial White with Subtle Slate Border */
[data-testid="stSidebar"] {
    background-color: #FAFAFA !important;
    border-right: 1px solid #E2E8F0 !important;
    box-shadow: 1px 0 10px rgba(0, 0, 0, 0.02) !important;
}

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #0F172A !important;
}

[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
    color: #475569 !important;
}

/* Elegant Cards styling using Streamlit bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 20px !important;
    padding: 24px 28px !important;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.02) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #CBD5E1 !important;
    box-shadow: 0 12px 30px -4px rgba(15, 23, 42, 0.09) !important;
    transform: translateY(-2px);
}

/* Active Step Hero Card */
.step-hero-card {
    background: #FFFFFF;
    border: 1px solid #FED7AA;
    border-left: 6px solid #EA580C;
    border-radius: 18px;
    padding: 26px 30px;
    margin-bottom: 22px;
    box-shadow: 0 6px 24px -2px rgba(234, 88, 12, 0.08), 0 2px 6px rgba(0,0,0,0.02);
}

/* Badges & Pills in Harmonious Culinary Colors */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 30px;
    font-family: 'Outfit', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}

.badge-pakistani {
    background: #ECFDF5;
    color: #047857;
    border: 1px solid #A7F3D0;
}

.badge-time {
    background: #FFFBEB;
    color: #B45309;
    border: 1px solid #FDE68A;
}

.badge-servings {
    background: #EFF6FF;
    color: #1D4ED8;
    border: 1px solid #BFDBFE;
}

.badge-active {
    background: #FEF3C7;
    color: #D97706;
    border: 1px solid #FCD34D;
}

.badge-step-num {
    background: #FFF7ED;
    color: #C2410C;
    border: 1px solid #FFEDD5;
    font-weight: 800;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 16px !important;
    padding: 14px 18px !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Fraunces', 'Playfair Display', serif !important;
    color: #EA580C !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'Outfit', sans-serif !important;
    color: #64748B !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* Progress Bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #EA580C 0%, #F59E0B 100%) !important;
    border-radius: 10px !important;
}

/* Primary Button Styling (Vibrant Saffron/Terracotta, readable bold white text) */
button[kind="primary"] {
    background: linear-gradient(135deg, #EA580C 0%, #C2410C 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 12px 24px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 14px rgba(234, 88, 12, 0.25) !important;
    transition: all 0.2s ease !important;
}

button[kind="primary"] *, 
button[kind="primary"] p, 
button[kind="primary"] span, 
button[kind="primary"] div,
[data-testid="stSidebar"] button[kind="primary"] *,
[data-testid="stSidebar"] button[kind="primary"] p {
    color: #FFFFFF !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
}

button[kind="primary"]:hover {
    background: linear-gradient(135deg, #C2410C 0%, #9A3412 100%) !important;
    box-shadow: 0 6px 20px rgba(234, 88, 12, 0.35) !important;
    transform: translateY(-1px) !important;
}

/* Secondary Button Styling */
button[kind="secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 12px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    transition: all 0.18s ease !important;
}

button[kind="secondary"] *,
button[kind="secondary"] p,
button[kind="secondary"] span {
    color: #1E293B !important;
}

button[kind="secondary"]:hover {
    background-color: #FFF7ED !important;
    border-color: #FDBA74 !important;
    color: #EA580C !important;
}

button[kind="secondary"]:hover * {
    color: #EA580C !important;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 18px !important;
    padding: 18px 22px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03) !important;
}

[data-testid="stChatMessage"] p {
    color: #1E293B !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}

/* Chat Input Bar */
[data-testid="stChatInput"] {
    border-radius: 16px !important;
    border: 1px solid #CBD5E1 !important;
    background-color: #FFFFFF !important;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #EA580C !important;
    box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.15) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: transparent !important;
    border-bottom: 2px solid #F1F5F9 !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    color: #64748B !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 18px !important;
}

.stTabs [aria-selected="true"] {
    color: #EA580C !important;
    border-bottom: 3px solid #EA580C !important;
}

/* Decision Status Tags in Chat */
.decision-tag {
    display: inline-block;
    font-family: 'Outfit', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 12px;
    border-radius: 20px;
    margin-top: 8px;
}
.tag-execute { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
.tag-answer  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.tag-clarify { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }

/* Checkboxes */
[data-testid="stCheckbox"] label span {
    font-size: 0.94rem !important;
    color: #1E293B !important;
}
</style>
"""
st.markdown(ELEGANT_WHITE_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# APPLICATION STATE
# -----------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "recipe_name" not in st.session_state:
    st.session_state.recipe_name = None
if "current_step_number" not in st.session_state:
    st.session_state.current_step_number = 1
if "current_instruction" not in st.session_state:
    st.session_state.current_instruction = ""
if "total_steps" not in st.session_state:
    st.session_state.total_steps = 1
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_status" not in st.session_state:
    st.session_state.session_status = None
if "ingredients" not in st.session_state:
    st.session_state.ingredients = []
if "steps_list" not in st.session_state:
    st.session_state.steps_list = []
if "est_duration" not in st.session_state:
    st.session_state.est_duration = None
if "pending_quick_message" not in st.session_state:
    st.session_state.pending_quick_message = None
if "servings" not in st.session_state:
    st.session_state.servings = 4
if "timer_auto_start" not in st.session_state:
    st.session_state.timer_auto_start = False
if "timer_action" not in st.session_state:
    st.session_state.timer_action = None
if "timer_nonce" not in st.session_state:
    st.session_state.timer_nonce = 0
if "last_processed_audio_hash" not in st.session_state:
    st.session_state.last_processed_audio_hash = None

# -----------------------------------------------------------------------------
# SIDEBAR / NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
        <div style="width:40px; height:40px; border-radius:10px; background:#FEF3C7; display:flex; align-items:center; justify-content:center; font-size:22px; border:1px solid #FDE68A;">
            👨‍🍳
        </div>
        <div>
            <h2 class="editorial-serif" style="margin:0; font-size:22px; color:#0F172A;">Chef AI</h2>
            <div style="font-size:12px; color:#64748B; font-weight:500;">Desi Culinary Assistant</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

import os

DEFAULT_PRODUCTION_API_URL = "https://chef-zce2.onrender.com/api/v1"

# Resolve backend URL securely without exposing API endpoint in public UI:
# Priority 1: Environment variable (API_BASE_URL)
# Priority 2: Streamlit secrets (st.secrets["API_BASE_URL"])
# Priority 3: Hidden query parameter for debug (?api_url=... or ?api_host=...)
# Priority 4: Auto-detect local backend if active on 127.0.0.1:8000, else default to production Render
raw_api_url = os.environ.get("API_BASE_URL", "").strip()

if not raw_api_url and hasattr(st, "secrets") and "API_BASE_URL" in st.secrets:
    raw_api_url = str(st.secrets["API_BASE_URL"]).strip()

if not raw_api_url and "api_url" in st.query_params:
    raw_api_url = str(st.query_params["api_url"]).strip()
elif not raw_api_url and "api_host" in st.query_params:
    raw_api_url = str(st.query_params["api_host"]).strip()

if not raw_api_url:
    try:
        local_probe = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=0.3)
        if local_probe.status_code == 200:
            raw_api_url = "http://127.0.0.1:8000/api/v1"
        else:
            raw_api_url = DEFAULT_PRODUCTION_API_URL
    except Exception:
        raw_api_url = DEFAULT_PRODUCTION_API_URL

# Normalize URL: strip whitespace and trailing slashes
raw_host = raw_api_url.rstrip("/")
if not raw_host.endswith("/api/v1"):
    API_BASE_URL = f"{raw_host}/api/v1"
else:
    API_BASE_URL = raw_host

def probe_backend(timeout: float = 3.0):
    """Probe the health endpoint with a configurable timeout."""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=timeout)
        if r.status_code == 200:
            return True, r.json().get("version", "0.1.0")
    except Exception:
        pass
    return False, None

@st.cache_data(ttl=25, show_spinner=False)
def check_health_cached():
    return probe_backend(timeout=2.5)

# Fast non-blocking cached probe
is_healthy, app_ver = check_health_cached()
is_remote_cloud = ("onrender.com" in API_BASE_URL) or ("127.0.0.1" not in API_BASE_URL and "localhost" not in API_BASE_URL)

if not is_healthy and is_remote_cloud:
    # Cloud server (Render free tier) spins down after 15 mins of inactivity.
    # Provide an automatic, animated warm-up experience with auto-retry.
    st.sidebar.markdown('<span class="badge-pill" style="background:#FEF3C7; color:#B45309; border:1px solid #FDE68A;">⚡ Waking Up Server...</span>', unsafe_allow_html=True)
    st.sidebar.caption("Render free instance is booting up (~30s).")

    warmup_box = st.empty()
    with warmup_box.container():
        st.markdown(
            """
            <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:16px; padding:20px 24px; margin-bottom:24px;">
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="font-size:28px;">⚡</div>
                    <div>
                        <h3 style="margin:0; font-size:18px; color:#92400E; font-family:'Playfair Display', serif;">Waking up Chef AI Cloud Backend...</h3>
                        <p style="margin:6px 0 0 0; font-size:14px; color:#B45309; line-height:1.5;">
                            Render free instances spin down after 15 minutes of inactivity to conserve resources.
                            Your server is booting up right now. <b>This page will connect automatically once ready — no need to refresh!</b>
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        boot_progress = st.progress(15, text="Connecting to cloud server and initializing database...")
        # Poll up to 7 attempts (approx 25 seconds)
        for step in range(1, 8):
            time.sleep(3.5)
            boot_progress.progress(min(15 + step * 12, 95), text=f"Booting application services... ({step * 4}s)")
            healthy_now, ver_now = probe_backend(timeout=3.5)
            if healthy_now:
                is_healthy = True
                app_ver = ver_now
                boot_progress.progress(100, text="Connected successfully! Loading recipes...")
                time.sleep(0.4)
                st.cache_data.clear()
                warmup_box.empty()
                st.rerun()

    if not is_healthy:
        st.warning("The cloud server is taking a little longer to wake up. Click the button below to check connection:")
        if st.button("🔄 Connect Now", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

elif is_healthy:
    st.sidebar.markdown(f'<span class="badge-pill" style="background:#F0FDF4; color:#15803D; border:1px solid #BBF7D0;">● System Online v{app_ver}</span>', unsafe_allow_html=True)
else:
    # Truly local disconnected instance
    st.sidebar.markdown('<span class="badge-pill" style="background:#FEF2F2; color:#B91C1C; border:1px solid #FECACA;">● Backend Disconnected</span>', unsafe_allow_html=True)
    st.sidebar.caption("Run: `.venv\\Scripts\\python -m uvicorn app.main:app --reload`")

st.sidebar.markdown(
    """
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:10px 14px; margin-top:8px; margin-bottom:12px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:#475569; font-weight:700;">🎙️ Hands-Free Assistant</div>
        <div style="font-size:13px; font-weight:600; color:#0F172A; margin-top:2px;">Chef Voice AI</div>
        <div style="font-size:11px; color:#64748B;">Instant Urdu & English Recognition</div>
    </div>
    """,
    unsafe_allow_html=True
)

@st.cache_data(ttl=120, show_spinner=False)
def fetch_recipes_cached():
    try:
        res = requests.get(f"{API_BASE_URL}/recipes", timeout=12)
        if res.status_code == 200:
            return res.json().get("items", [])
    except Exception:
        pass
    return []

def fetch_recipes():
    return fetch_recipes_cached()

def is_timer_start_request(user_msg: str, last_assistant_msg: str = "") -> bool:
    """Robust detection of timer start intent across English, Urdu, and Roman Urdu."""
    if not user_msg:
        return False
    low_u = user_msg.strip().lower()
    clean_u = re.sub(r"[^\w\s]", " ", low_u)
    clean_u = " ".join(clean_u.split())

    # 1. Any mention of timer with activation / action words
    has_timer_word = any(w in clean_u.split() for w in ["timer", "taimar", "time"])
    timer_start_verbs = [
        "start", "shuru", "laga", "lagao", "lagado", "lagade", "chala", "chalao", "chalado", "chalade",
        "on", "kardo", "karduhu", "kar do", "karo", "karde", "chalain", "chalein", "run", "play", "set"
    ]
    if has_timer_word and any(w in clean_u for w in timer_start_verbs):
        return True

    # 2. Standalone start / timer commands
    direct_commands = [
        "timer", "start timer", "timer start", "start the timer", "set timer", "set a timer",
        "timer on", "timer please", "run timer", "timer chalao", "timer shuru", "timer lagao",
        "timer lagado", "timer shuru kardo", "timer start kardo", "timer start karduhu"
    ]
    if any(clean_u == cmd or clean_u.startswith(cmd) for cmd in direct_commands):
        return True

    # 3. Affirmation if the previous assistant message asked about starting a timer
    low_last = last_assistant_msg.lower() if last_assistant_msg else ""
    timer_offered = any(phrase in low_last for phrase in [
        "start the timer", "timer shuru", "shall i start", "kya main", "timer for"
    ])
    if timer_offered:
        affirmations = [
            "yes", "yeah", "yup", "yep", "sure", "ok", "okay", "haan", "ha", "ji", "jee",
            "kardo", "kar do", "karduhu", "kar dain", "theek hai", "bilkul", "start", "shuru",
            "chalain", "chalo", "go", "go ahead", "please", "yes please", "haan ji", "haan kardo"
        ]
        tokens = clean_u.split()
        if any(clean_u == a or clean_u.startswith(a) for a in affirmations) or (tokens and tokens[0] in affirmations):
            return True

    return False

def is_timer_pause_request(user_msg: str) -> bool:
    """Detect pause timer intent."""
    if not user_msg:
        return False
    clean_u = re.sub(r"[^\w\s]", " ", user_msg.strip().lower())
    clean_u = " ".join(clean_u.split())
    return any(p in clean_u for p in ["pause timer", "timer pause", "timer roko", "stop timer", "pause the timer", "timer rok do", "roko timer"])

def is_timer_reset_request(user_msg: str) -> bool:
    """Detect reset timer intent."""
    if not user_msg:
        return False
    clean_u = re.sub(r"[^\w\s]", " ", user_msg.strip().lower())
    clean_u = " ".join(clean_u.split())
    return any(p in clean_u for p in ["reset timer", "timer reset", "restart timer", "timer restart", "timer dobara", "timer phirse", "reset the timer"])

def start_new_session(recipe_id: int, servings_count: int):
    try:
        with st.spinner("Initializing cooking session with Chef AI..."):
            res = requests.post(
                f"{API_BASE_URL}/sessions",
                json={"recipe_id": recipe_id, "servings": servings_count},
                timeout=60
            )
        if res.status_code == 201:
            data = res.json()
            steps = data.get("steps", [])
            st.session_state.session_id = data["id"]
            st.session_state.recipe_name = data["recipe_name"]
            st.session_state.session_status = data["status"]
            st.session_state.current_step_number = data.get("current_step_number", 1)
            st.session_state.total_steps = len(steps) if steps else 1
            st.session_state.steps_list = steps
            st.session_state.ingredients = data.get("ingredients", [])
            st.session_state.servings = servings_count

            curr = data.get("current_step")
            if curr:
                st.session_state.current_instruction = curr.get("instruction", "")
                st.session_state.est_duration = curr.get("estimated_duration_seconds")
            else:
                st.session_state.current_instruction = ""
                st.session_state.est_duration = None

            # Persist session to URL query parameter for browser refresh recovery
            st.query_params["session_id"] = str(data["id"])

            step1_dur = curr.get("estimated_duration_seconds") if curr else None
            timer_ask = ""
            if step1_dur and step1_dur >= 60:
                mins = round(step1_dur / 60)
                timer_ask = f"\n\n⏱️ **Shall I start the timer for {mins} minutes?**"
            elif step1_dur and step1_dur > 0:
                timer_ask = f"\n\n⏱️ **Shall I start the timer for {step1_dur} seconds?**"

            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": f"**Assalam-o-Alaikum!** I'm your dedicated Chef companion for **{data['recipe_name']}** ({servings_count} servings).\n\nWhenever you're ready, let's begin with **Step 1**: {st.session_state.current_instruction}{timer_ask}\n\n*(Feel free to talk to me naturally in English, Urdu, or Roman Urdu!)*",
                    "decision": "session_start"
                }
            ]
            st.toast(f"Cooking Session #{data['id']} Ready!", icon="✨")
        else:
            st.sidebar.error(f"Failed to start session: {res.text}")
    except Exception as e:
        st.sidebar.error(f"Request failed: {e}")

def load_session(session_id: int) -> bool:
    """Restore an active session and full chat history on page refresh."""
    try:
        res = requests.get(f"{API_BASE_URL}/sessions/{session_id}", timeout=25)
        if res.status_code == 200:
            data = res.json()
            steps = data.get("steps", [])
            st.session_state.session_id = data["id"]
            st.session_state.recipe_name = data["recipe_name"]
            st.session_state.session_status = data["status"]
            st.session_state.current_step_number = data.get("current_step_number", 1)
            st.session_state.total_steps = len(steps) if steps else 1
            st.session_state.steps_list = steps
            st.session_state.ingredients = data.get("ingredients", [])
            st.session_state.servings = data.get("servings", 4)

            curr = data.get("current_step")
            if curr:
                st.session_state.current_instruction = curr.get("instruction", "")
                st.session_state.est_duration = curr.get("estimated_duration_seconds")
            elif data.get("status") == "COMPLETED":
                st.session_state.current_instruction = "🎉 Recipe Completed! Nosh-e-Jaan / Enjoy your meal!"
                st.session_state.est_duration = None
            else:
                st.session_state.current_instruction = ""
                st.session_state.est_duration = None

            st.query_params["session_id"] = str(data["id"])

            # Retrieve persisted conversation messages from backend
            try:
                msg_res = requests.get(f"{API_BASE_URL}/sessions/{session_id}/messages", timeout=25)
                if msg_res.status_code == 200:
                    saved = msg_res.json()
                    if saved:
                        st.session_state.chat_history = [
                            {
                                "role": m["role"],
                                "content": m["content"],
                                "decision": m.get("decision_type"),
                            }
                            for m in saved
                        ]
                    else:
                        st.session_state.chat_history = [
                            {
                                "role": "assistant",
                                "content": f"**Assalam-o-Alaikum!** Resumed cooking session for **{data['recipe_name']}** ({st.session_state.servings} servings).\n\nLet's continue from **Step {st.session_state.current_step_number}**. Feel free to talk to me naturally in **English, Urdu, or Roman Urdu**!",
                                "decision": "session_start",
                            }
                        ]
            except Exception:
                pass
            return True
        else:
            if "session_id" in st.query_params:
                del st.query_params["session_id"]
            return False
    except Exception as e:
        if "session_id" in st.query_params:
            del st.query_params["session_id"]
        return False

# -----------------------------------------------------------------------------
# AUTO-RESTORE SESSION FROM URL QUERY PARAMETERS ON PAGE RELOAD / REFRESH
# -----------------------------------------------------------------------------
if st.session_state.session_id is None and "session_id" in st.query_params:
    try:
        raw_sid = st.query_params["session_id"]
        if raw_sid:
            load_session(int(raw_sid))
    except (ValueError, TypeError):
        if "session_id" in st.query_params:
            del st.query_params["session_id"]

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS & RECIPE SELECTION
# -----------------------------------------------------------------------------
if st.session_state.session_id:
    st.sidebar.markdown(
        f"""
        <div style="background:#FFF7ED; border:1px solid #FFEDD5; border-radius:14px; padding:14px 16px; margin-top:14px; margin-bottom:12px;">
            <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.06em; color:#C2410C; font-weight:700;">Active Cooking Session</div>
            <div style="font-size:15px; font-weight:700; color:#0F172A; margin-top:3px;">#{st.session_state.session_id} — {st.session_state.recipe_name}</div>
            <div style="font-size:12px; color:#64748B; margin-top:2px;">Step {st.session_state.current_step_number} of {st.session_state.total_steps} ({st.session_state.session_status})</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.sidebar.button("🔄 Choose Another Recipe", use_container_width=True, type="secondary"):
        st.session_state.session_id = None
        st.session_state.recipe_name = None
        st.session_state.chat_history = []
        st.session_state.current_step_number = 1
        st.session_state.total_steps = 1
        st.session_state.steps_list = []
        st.session_state.ingredients = []
        st.session_state.current_instruction = ""
        st.session_state.session_status = None
        st.session_state.est_duration = None
        if "session_id" in st.query_params:
            del st.query_params["session_id"]
        st.rerun()

    with st.sidebar.expander("Switch Recipe"):
        recipes = fetch_recipes()
        recipe_map = {f"{r['name']} ({r['cuisine']})": r for r in recipes}
        if recipe_map:
            switch_name = st.selectbox("Recipe", list(recipe_map.keys()), key="sidebar_switch_recipe")
            switch_recipe = recipe_map[switch_name]
            c_serv, c_time = st.columns(2)
            with c_serv:
                switch_servings = st.number_input("Servings", min_value=1, max_value=20, value=switch_recipe.get("default_servings", 4), key="sidebar_switch_servings")
            with c_time:
                tot_time = (switch_recipe.get("prep_time_minutes") or 0) + (switch_recipe.get("cook_time_minutes") or 0)
                st.metric("Total Time", f"{tot_time}m")
            if st.button("Start New Session", use_container_width=True, type="primary", key="btn_start_switch"):
                start_new_session(switch_recipe["id"], switch_servings)
                st.rerun()
else:
    st.sidebar.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("<h4 style='font-size:14px; text-transform:uppercase; letter-spacing:0.06em; color:#64748B;'>Select Recipe</h4>", unsafe_allow_html=True)

    recipes = fetch_recipes()
    recipe_map = {f"{r['name']} ({r['cuisine']})": r for r in recipes}

    if recipe_map:
        selected_name = st.sidebar.selectbox("Recipe", list(recipe_map.keys()), label_visibility="collapsed")
        selected_recipe = recipe_map[selected_name]

        c_serv, c_time = st.sidebar.columns(2)
        with c_serv:
            servings = st.sidebar.number_input("Servings", min_value=1, max_value=20, value=selected_recipe.get("default_servings", 4))
        with c_time:
            tot_time = (selected_recipe.get("prep_time_minutes") or 0) + (selected_recipe.get("cook_time_minutes") or 0)
            st.sidebar.metric("Total Time", f"{tot_time}m")

        if st.sidebar.button("Start Cooking Session", use_container_width=True, type="primary"):
            start_new_session(selected_recipe["id"], servings)
            st.rerun()
    else:
        st.sidebar.info("No recipes loaded. Verify database seed.")

st.sidebar.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
with st.sidebar.expander("💬 Natural Speech Examples"):
    st.markdown(
        """
        - *"Ab aage kya karna hai?"*
        - *"Step 1 mukammal ho gaya"*
        - *"Oil kitna garam hona chahiye?"*
        - *"Can I substitute with butter?"*
        - *"Is step mein kitne masalay daalne hain?"*
        """
    )

# -----------------------------------------------------------------------------
# MAIN INTERFACE
# -----------------------------------------------------------------------------
if st.session_state.session_id:
    # Top Session Header Bar
    head_col1, head_col2, head_col3 = st.columns([3, 1.2, 1.2])
    with head_col1:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
                <h1 class="editorial-serif" style="margin:0; font-size:32px; color:#0F172A;">{st.session_state.recipe_name}</h1>
                <span class="badge-pill badge-pakistani">🇵🇰 Pakistani</span>
                <span class="badge-pill badge-active">● {st.session_state.session_status}</span>
            </div>
            <div style="font-size:13px; color:#64748B;">Authoritative Step-by-Step Cooking Guide</div>
            """,
            unsafe_allow_html=True
        )
    with head_col2:
        st.metric("Current Progress", f"Step {st.session_state.current_step_number} of {st.session_state.total_steps}")
    with head_col3:
        mins = round(st.session_state.est_duration / 60) if st.session_state.est_duration else None
        st.metric("Estimated Time", f"~{mins} mins" if mins else "Self-Paced")

    # Step Progress Indicator
    progress_val = st.session_state.current_step_number / max(1, st.session_state.total_steps)
    st.progress(progress_val)
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # TWO-COLUMN WORKSPACE: Chat (Left) vs Mise en Place (Right)
    chat_col, right_col = st.columns([1.25, 0.85], gap="large")

    with chat_col:
        # Active Step Hero Card
        st.markdown(
            f"""
            <div class="step-hero-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <span class="badge-pill badge-step-num">Step {st.session_state.current_step_number}</span>
                    <span style="font-size:12px; color:#64748B; font-weight:600;">Active Instruction</span>
                </div>
                <div class="editorial-serif" style="font-size:1.25rem; font-weight:600; line-height:1.6; color:#0F172A;">
                    {st.session_state.current_instruction}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Step Cooking Timer Widget if step has estimated duration
        if st.session_state.est_duration and st.session_state.est_duration > 0:
            dur_sec = st.session_state.est_duration
            dur_mins = round(dur_sec / 60) if dur_sec >= 60 else None
            dur_label = f"{dur_mins} mins" if dur_mins else f"{dur_sec}s"

            timer_action = st.session_state.get("timer_action")
            timer_auto_start = st.session_state.get("timer_auto_start", False)
            timer_nonce = st.session_state.get("timer_nonce", 0)

            timer_component_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <style>
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                body {{
                    background: transparent;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    color: #0F172A;
                    padding: 2px 2px 8px 2px;
                }}
                .timer-card {{
                    background: #FFFFFF;
                    border: 1px solid #FED7AA;
                    border-left: 6px solid #EA580C;
                    border-radius: 16px;
                    padding: 14px 18px;
                    box-shadow: 0 4px 16px -2px rgba(234, 88, 12, 0.08);
                    transition: all 0.25s ease;
                }}
                .timer-top {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }}
                .timer-title {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: 700;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                    color: #C2410C;
                }}
                .badge {{
                    font-size: 11px;
                    font-weight: 700;
                    padding: 2px 9px;
                    border-radius: 12px;
                    background: #FFF7ED;
                    color: #C2410C;
                    border: 1px solid #FFEDD5;
                }}
                .btn-chime {{
                    background: #FAFAFA;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-size: 12px;
                    font-weight: 600;
                    color: #475569;
                    cursor: pointer;
                    transition: all 0.15s ease;
                }}
                .btn-chime:hover {{
                    background: #FFF7ED;
                    color: #EA580C;
                    border-color: #FDBA74;
                }}
                .clock-row {{
                    display: flex;
                    align-items: baseline;
                    justify-content: space-between;
                    margin-bottom: 8px;
                }}
                .clock-digits {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace;
                    font-size: 32px;
                    font-weight: 800;
                    color: #0F172A;
                    letter-spacing: -0.02em;
                    line-height: 1;
                }}
                .timer-hint {{
                    font-size: 12px;
                    color: #64748B;
                    font-weight: 500;
                }}
                .progress-track {{
                    width: 100%;
                    height: 6px;
                    background: #F1F5F9;
                    border-radius: 8px;
                    overflow: hidden;
                    margin-bottom: 12px;
                }}
                .progress-fill {{
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, #EA580C 0%, #F59E0B 100%);
                    border-radius: 8px;
                    transition: width 0.3s ease;
                }}
                .btn-group {{
                    display: flex;
                    gap: 8px;
                    align-items: center;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #EA580C 0%, #C2410C 100%);
                    color: #FFFFFF;
                    border: none;
                    border-radius: 10px;
                    padding: 7px 16px;
                    font-weight: 700;
                    font-size: 13px;
                    cursor: pointer;
                    box-shadow: 0 2px 8px rgba(234, 88, 12, 0.25);
                    transition: all 0.15s ease;
                }}
                .btn-primary:hover {{
                    background: linear-gradient(135deg, #C2410C 0%, #9A3412 100%);
                    transform: translateY(-1px);
                }}
                .btn-secondary {{
                    background: #FFFFFF;
                    border: 1px solid #CBD5E1;
                    color: #334155;
                    border-radius: 10px;
                    padding: 7px 13px;
                    font-weight: 600;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.15s ease;
                }}
                .btn-secondary:hover {{
                    background: #F8FAFC;
                    color: #0F172A;
                    border-color: #94A3B8;
                }}
            </style>
            </head>
            <body>
            <div id="timer-card" class="timer-card">
                <div class="timer-top">
                    <div class="timer-title">
                        <span>⏱️ Step {st.session_state.current_step_number} Timer</span>
                        <span id="timer-badge" class="badge">Ready</span>
                    </div>
                    <button id="btn-test-chime" class="btn-chime" title="Test fun bell alarm sound">🔔 Test Alarm Bell</button>
                </div>
                <div class="clock-row">
                    <div id="clock-display" class="clock-digits">00:00</div>
                    <div id="clock-hint" class="timer-hint">Recommended: {dur_label}</div>
                </div>
                <div class="progress-track">
                    <div id="progress-fill" class="progress-fill"></div>
                </div>
                <div class="btn-group">
                    <button id="btn-start" class="btn-primary">▶️ Start {dur_label} Timer</button>
                    <button id="btn-pause" class="btn-secondary" style="display: none;">⏸️ Pause</button>
                    <button id="btn-reset" class="btn-secondary">🔄 Reset</button>
                    <button id="btn-add-min" class="btn-secondary">+1 Min</button>
                </div>
            </div>

            <script>
            (function() {{
                const sessionId = "{st.session_state.session_id}";
                const stepNum = {st.session_state.current_step_number};
                const totalDuration = {dur_sec};
                const timerAction = "{timer_action or ''}";
                const autoStart = {"true" if (timer_auto_start or timer_action == 'start') else "false"};
                const timerNonce = {timer_nonce};
                const storageKey = "chef_timer_" + sessionId + "_" + stepNum;

                const clockEl = document.getElementById("clock-display");
                const hintEl = document.getElementById("clock-hint");
                const progressEl = document.getElementById("progress-fill");
                const badgeEl = document.getElementById("timer-badge");
                const cardEl = document.getElementById("timer-card");
                const btnStart = document.getElementById("btn-start");
                const btnPause = document.getElementById("btn-pause");
                const btnReset = document.getElementById("btn-reset");
                const btnAddMin = document.getElementById("btn-add-min");
                const btnTestChime = document.getElementById("btn-test-chime");

                // Fun Acoustic Bell Chime using Web Audio API (duration ~1.4 seconds)
                function playFunBell() {{
                    try {{
                        const AudioCtx = window.AudioContext || window.webkitAudioContext;
                        if (!AudioCtx) return;
                        const ctx = new AudioCtx();
                        if (ctx.state === "suspended") {{
                            ctx.resume();
                        }}
                        const now = ctx.currentTime;

                        // Tone 1 at t=0: Bright strike (880Hz + 1318.5Hz + 1760Hz)
                        [880, 1318.5, 1760].forEach((freq, idx) => {{
                            const osc = ctx.createOscillator();
                            const gain = ctx.createGain();
                            osc.type = idx === 0 ? "triangle" : "sine";
                            osc.frequency.setValueAtTime(freq, now);
                            gain.gain.setValueAtTime(idx === 0 ? 0.35 : 0.15, now);
                            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.6);
                            osc.connect(gain);
                            gain.connect(ctx.destination);
                            osc.start(now);
                            osc.stop(now + 0.65);
                        }});

                        // Tone 2 at t=0.18s: Cheerful resolve chime (1174.66Hz + 1760Hz + 2349.32Hz)
                        const t2 = now + 0.18;
                        [1174.66, 1760, 2349.32].forEach((freq, idx) => {{
                            const osc = ctx.createOscillator();
                            const gain = ctx.createGain();
                            osc.type = idx === 0 ? "triangle" : "sine";
                            osc.frequency.setValueAtTime(freq, t2);
                            gain.gain.setValueAtTime(idx === 0 ? 0.45 : 0.2, t2);
                            gain.gain.exponentialRampToValueAtTime(0.0001, t2 + 1.2);
                            osc.connect(gain);
                            gain.connect(ctx.destination);
                            osc.start(t2);
                            osc.stop(t2 + 1.25);
                        }});
                    }} catch(e) {{
                        console.error("Audio error:", e);
                    }}
                }}

                btnTestChime.addEventListener("click", playFunBell);

                let state = {{
                    totalDuration: totalDuration,
                    targetEndTime: null,
                    isRunning: false,
                    remainingSeconds: totalDuration,
                    hasChimed: false
                }};

                try {{
                    const raw = sessionStorage.getItem(storageKey);
                    if (raw) {{
                        const saved = JSON.parse(raw);
                        if (saved && typeof saved.remainingSeconds === "number") {{
                            state = saved;
                        }}
                    }}
                }} catch(e) {{}}

                function saveState() {{
                    try {{
                        sessionStorage.setItem(storageKey, JSON.stringify(state));
                    }} catch(e) {{}}
                }}

                function formatTime(secs) {{
                    secs = Math.max(0, Math.floor(secs));
                    const m = Math.floor(secs / 60);
                    const s = secs % 60;
                    return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
                }}

                let intervalId = null;

                function updateUI() {{
                    let remaining = state.remainingSeconds;
                    if (state.isRunning && state.targetEndTime) {{
                        const now = Date.now();
                        remaining = Math.max(0, Math.round((state.targetEndTime - now) / 1000));
                        state.remainingSeconds = remaining;
                    }}

                    clockEl.textContent = formatTime(remaining);
                    const pct = state.totalDuration > 0 ? (remaining / state.totalDuration) * 100 : 0;
                    progressEl.style.width = Math.max(0, Math.min(100, pct)) + "%";

                    if (state.isRunning) {{
                        btnStart.style.display = "none";
                        btnPause.style.display = "inline-block";
                        btnPause.textContent = "⏸️ Pause";
                        badgeEl.textContent = "🔥 Running";
                        badgeEl.style.background = "#FEF3C7";
                        badgeEl.style.color = "#D97706";
                        badgeEl.style.borderColor = "#FCD34D";
                        hintEl.textContent = "Cooking in progress...";
                        cardEl.style.borderLeftColor = "#EA580C";
                        cardEl.style.background = "#FFFFFF";
                    }} else if (remaining === 0) {{
                        btnStart.style.display = "inline-block";
                        btnStart.textContent = "🔄 Restart Timer";
                        btnPause.style.display = "none";
                        badgeEl.textContent = "🔔 Time's Up!";
                        badgeEl.style.background = "#ECFDF5";
                        badgeEl.style.color = "#047857";
                        badgeEl.style.borderColor = "#A7F3D0";
                        hintEl.textContent = "Time complete! Proceed when ready.";
                        cardEl.style.borderLeftColor = "#10B981";
                        cardEl.style.background = "#F0FDF4";
                    }} else if (remaining < state.totalDuration) {{
                        btnStart.style.display = "inline-block";
                        btnStart.textContent = "▶️ Resume";
                        btnPause.style.display = "none";
                        badgeEl.textContent = "⏸️ Paused";
                        badgeEl.style.background = "#F1F5F9";
                        badgeEl.style.color = "#475569";
                        badgeEl.style.borderColor = "#CBD5E1";
                        hintEl.textContent = "Timer paused";
                        cardEl.style.borderLeftColor = "#F59E0B";
                        cardEl.style.background = "#FFFFFF";
                    }} else {{
                        btnStart.style.display = "inline-block";
                        btnStart.textContent = "▶️ Start {dur_label} Timer";
                        btnPause.style.display = "none";
                        badgeEl.textContent = "Ready";
                        badgeEl.style.background = "#FFF7ED";
                        badgeEl.style.color = "#C2410C";
                        badgeEl.style.borderColor = "#FFEDD5";
                        hintEl.textContent = "Recommended: {dur_label}";
                        cardEl.style.borderLeftColor = "#EA580C";
                        cardEl.style.background = "#FFFFFF";
                    }}
                }}

                function tick() {{
                    if (!state.isRunning) return;
                    const now = Date.now();
                    const rem = Math.max(0, Math.round((state.targetEndTime - now) / 1000));
                    state.remainingSeconds = rem;

                    if (rem <= 0) {{
                        state.isRunning = false;
                        state.targetEndTime = null;
                        if (intervalId) clearInterval(intervalId);
                        intervalId = null;

                        if (!state.hasChimed) {{
                            state.hasChimed = true;
                            playFunBell();
                        }}
                    }}
                    saveState();
                    updateUI();
                }}

                function startTimer() {{
                    if (state.remainingSeconds <= 0) {{
                        state.remainingSeconds = state.totalDuration;
                    }}
                    state.isRunning = true;
                    state.hasChimed = false;
                    state.targetEndTime = Date.now() + (state.remainingSeconds * 1000);
                    saveState();
                    updateUI();
                    if (intervalId) clearInterval(intervalId);
                    intervalId = setInterval(tick, 1000);
                }}

                function pauseTimer() {{
                    if (!state.isRunning) return;
                    state.isRunning = false;
                    const now = Date.now();
                    state.remainingSeconds = Math.max(0, Math.round((state.targetEndTime - now) / 1000));
                    state.targetEndTime = null;
                    if (intervalId) clearInterval(intervalId);
                    intervalId = null;
                    saveState();
                    updateUI();
                }}

                function resetTimer() {{
                    state.isRunning = false;
                    state.targetEndTime = null;
                    state.remainingSeconds = state.totalDuration;
                    state.hasChimed = false;
                    if (intervalId) clearInterval(intervalId);
                    intervalId = null;
                    saveState();
                    updateUI();
                }}

                function addOneMin() {{
                    state.remainingSeconds += 60;
                    state.totalDuration += 60;
                    if (state.isRunning && state.targetEndTime) {{
                        state.targetEndTime += 60000;
                    }}
                    state.hasChimed = false;
                    saveState();
                    updateUI();
                }}

                btnStart.addEventListener("click", startTimer);
                btnPause.addEventListener("click", pauseTimer);
                btnReset.addEventListener("click", resetTimer);
                btnAddMin.addEventListener("click", addOneMin);

                if (timerAction === "start" || (autoStart && !state.isRunning && state.remainingSeconds > 0)) {{
                    if (!state.isRunning) {{
                        startTimer();
                    }}
                }} else if (timerAction === "pause") {{
                    pauseTimer();
                }} else if (timerAction === "reset") {{
                    resetTimer();
                }} else if (state.isRunning) {{
                    intervalId = setInterval(tick, 1000);
                }}

                updateUI();
            }})();
            </script>
            </body>
            </html>
            """
            components.html(timer_component_html, height=180, scrolling=False)
            st.session_state.timer_auto_start = False
            st.session_state.timer_action = None

        # Quick Action Shortcuts (Hands-Free simulation)
        st.caption("Quick actions:")
        btn_c1, btn_c2, btn_c3, btn_c4, btn_c5 = st.columns([1, 1, 1, 1, 1.1])
        if btn_c1.button("✅ Done", use_container_width=True, type="secondary"):
            st.session_state.pending_quick_message = f"Step {st.session_state.current_step_number} complete, aage kya karna hai?"
            st.rerun()
        if btn_c2.button("🧂 Items", use_container_width=True, type="secondary"):
            st.session_state.pending_quick_message = "Is step mein kaun se ingredients aur kitni quantity dalni hai?"
            st.rerun()
        if btn_c3.button("🔥 Heat", use_container_width=True, type="secondary"):
            st.session_state.pending_quick_message = "Aanch (heat flame) kitni honi chahiye?"
            st.rerun()
        if btn_c4.button("⏭️ Skip", use_container_width=True, type="secondary"):
            st.session_state.pending_quick_message = "Skip this step."
            st.rerun()
        if btn_c5.button("⏱️ Timer", use_container_width=True, type="secondary"):
            st.session_state.timer_auto_start = True
            st.session_state.timer_action = "start"
            st.session_state.timer_nonce = st.session_state.get("timer_nonce", 0) + 1
            st.session_state.pending_quick_message = "Start the timer for this step."
            st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Chat History Container
        chat_box = st.container()
        with chat_box:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"], avatar="👨‍🍳" if msg["role"] == "assistant" else "👤"):
                    st.markdown(msg["content"])
                    if "decision" in msg and msg["decision"]:
                        d = msg["decision"]
                        is_timer_reply = (
                            msg.get("role") == "assistant"
                            and any(phrase in msg.get("content", "").lower() for phrase in ["timer started", "⏱️ timer started", "timer shuru", "timer is running", "timer set for", "timer has started"])
                        )
                        if is_timer_reply:
                            tag_html = '<span class="decision-tag tag-execute">⏱️ Timer Started</span>'
                        else:
                            tag_html = {
                                "execute_action": '<span class="decision-tag tag-execute">🟢 Action Verified</span>',
                                "answer_question": '<span class="decision-tag tag-answer">🔵 Culinary Advice</span>',
                                "clarify": '<span class="decision-tag tag-clarify">🟠 Clarification Requested</span>',
                                "session_start": '<span class="decision-tag tag-execute">✨ Session Active</span>'
                            }.get(d, f'<span class="decision-tag tag-answer">{d}</span>')
                        st.markdown(tag_html, unsafe_allow_html=True)

        # Hands-Free Voice Input (Chef Voice AI)
        with st.expander("🎙️ Tap to Speak (Hands-Free Voice Mode)", expanded=False):
            st.caption("Record a voice update or question in English, Roman Urdu, or Urdu:")
            voice_recording = st.audio_input("Record audio", label_visibility="collapsed", key="voice_mic_input")
            if voice_recording is not None:
                audio_bytes = voice_recording.read()
                audio_hash = hash(audio_bytes)
                if st.session_state.get("last_processed_audio_hash") != audio_hash:
                    st.session_state["last_processed_audio_hash"] = audio_hash
                    transcription = None
                    with st.spinner("⚡ Processing voice command..."):
                        try:
                            files = {"file": ("recording.wav", audio_bytes, "audio/wav")}
                            res = requests.post(
                                f"{API_BASE_URL}/audio/transcribe",
                                files=files,
                                timeout=45,
                            )
                            if res.status_code == 200:
                                t_data = res.json()
                                transcription = t_data.get("transcription", "").strip()
                            elif res.status_code == 503:
                                st.error("⚠️ **Voice Service Unavailable:** Voice configuration is missing or inactive. Please type your message.")
                            else:
                                st.error(f"⚠️ Voice transcription notice ({res.status_code}): {res.text}")
                        except Exception as e:
                            st.error(f"Voice transmission error: {e}")

                    if transcription:
                        st.session_state.pending_quick_message = transcription
                        st.rerun()

        # Inbound Chat Input
        user_input = st.chat_input("Speak or type in English, Roman Urdu, or Urdu...")
        if st.session_state.pending_quick_message:
            user_input = st.session_state.pending_quick_message
            st.session_state.pending_quick_message = None

        if user_input:
            # Check if user affirms or requests timer control (start / pause / reset)
            last_assistant_msg = ""
            for m in reversed(st.session_state.chat_history):
                if m.get("role") == "assistant":
                    last_assistant_msg = m.get("content", "")
                    break

            if is_timer_start_request(user_input, last_assistant_msg):
                st.session_state.timer_auto_start = True
                st.session_state.timer_action = "start"
                st.session_state.timer_nonce = st.session_state.get("timer_nonce", 0) + 1
            elif is_timer_pause_request(user_input):
                st.session_state.timer_action = "pause"
                st.session_state.timer_nonce = st.session_state.get("timer_nonce", 0) + 1
            elif is_timer_reset_request(user_input):
                st.session_state.timer_action = "reset"
                st.session_state.timer_nonce = st.session_state.get("timer_nonce", 0) + 1

            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)

            with st.spinner("Chef AI is reviewing your recipe state..."):
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/sessions/{st.session_state.session_id}/message",
                        json={"message": user_input},
                        timeout=120
                    )
                    if res.status_code == 200:
                        data = res.json()
                        reply = data.get("reply", "")
                        decision = data.get("decision_type", "")
                        session_info = data.get("session", {})

                        # If AI reply confirms timer start, guarantee timer starts regardless of user phrasing
                        if any(phrase in reply.lower() for phrase in ["timer started", "⏱️ timer started", "timer shuru", "timer is running", "timer set for", "timer has started"]):
                            st.session_state.timer_auto_start = True
                            st.session_state.timer_action = "start"
                            st.session_state.timer_nonce = st.session_state.get("timer_nonce", 0) + 1

                        if session_info:
                            st.session_state.current_step_number = session_info.get("current_step_number", st.session_state.current_step_number)
                            st.session_state.session_status = session_info.get("status", st.session_state.session_status)
                            curr_step = session_info.get("current_step")
                            if curr_step and "instruction" in curr_step:
                                st.session_state.current_instruction = curr_step["instruction"]
                                st.session_state.est_duration = curr_step.get("estimated_duration_seconds")
                            elif session_info.get("status") == "COMPLETED":
                                st.session_state.current_instruction = "🎉 Recipe Completed! Nosh-e-Jaan / Enjoy your meal!"

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": reply,
                            "decision": decision
                        })
                        st.rerun()
                    else:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"⚠️ **Server Notice ({res.status_code}):** {res.text}\n\n*Please try sending your message again.*",
                            "decision": "clarify"
                        })
                        st.rerun()
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"⚠️ **Connection Notice:** Unable to reach backend ({e}). If the server was sleeping, it is waking up. Please retry in a few moments.",
                        "decision": "clarify"
                    })
                    st.rerun()

    with right_col:
        tab_ing, tab_map, tab_tips = st.tabs(["🧂 Ingredients", "📋 Roadmap", "💡 Tips"])

        with tab_ing:
            st.markdown("<h4 style='font-size:16px; margin-top:8px;'>Ingredients Needed</h4>", unsafe_allow_html=True)
            st.caption(f"Exact quantities scaled for **{st.session_state.get('servings', 4)} servings**:")
            if st.session_state.ingredients:
                for idx, ing in enumerate(st.session_state.ingredients):
                    qty = f"**{ing['quantity']} {ing['unit'] or ''}**".strip() if ing.get("quantity") else "*To taste*"
                    note = f" — *{ing['notes']}*" if ing.get("notes") else ""
                    st.checkbox(f"{ing['ingredient_name']}: {qty}{note}", key=f"ing_check_{idx}", value=False)
            else:
                st.info("Ingredients will load as you cook.")

        with tab_map:
            st.markdown("<h4 style='font-size:16px; margin-top:8px;'>Recipe Timeline</h4>", unsafe_allow_html=True)
            if st.session_state.steps_list:
                for s in st.session_state.steps_list:
                    s_num = s["step_number"]
                    is_active = (s_num == st.session_state.current_step_number)
                    is_past = (s_num < st.session_state.current_step_number) or (st.session_state.session_status == "COMPLETED")

                    icon = "✅" if is_past else ("🔥" if is_active else "⏳")
                    border_style = "border-left: 3px solid #D97706; padding-left: 10px; margin-bottom: 12px; background:#FFFBEB; padding:8px 10px; border-radius:4px;" if is_active else "margin-bottom: 12px; padding:4px 0;"
                    st.markdown(
                        f"""
                        <div style="{border_style}">
                            <div style="font-weight:700; font-size:0.86rem; color:#0F172A;">{icon} Step {s_num}</div>
                            <div style="font-size:0.83rem; color:#64748B; margin-top:2px;">{s['instruction']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.caption("Steps list not available.")

        with tab_tips:
            st.markdown("<h4 style='font-size:16px; margin-top:8px;'>Authentic Cooking Notes</h4>", unsafe_allow_html=True)
            st.markdown(
                """
                - **Bhunai Principle**: The secret to deep restaurant Karahi flavor is continuous bhunai on high heat until the oil separates completely from the tomato gravy.
                - **Garlic & Cumin Tempering**: When preparing tarka for daal, do not let sliced garlic burn dark. Pull off heat as soon as it turns light golden brown.
                - **Fresh Garnish**: Add fresh coriander and julienned ginger after extinguishing the flame to keep maximum fragrance.
                """
            )

else:
    # -----------------------------------------------------------------------------
    # WELCOME SPLASH SCREEN (CLEAN, WHITE, EDITORIAL)
    # -----------------------------------------------------------------------------
    st.markdown(
        """
        <div style="text-align:center; padding: 24px 20px 24px 20px;">
            <div style="display:inline-flex; width:60px; height:60px; border-radius:50%; background:#FFF7ED; align-items:center; justify-content:center; font-size:28px; margin-bottom:14px; border:1px solid #FFEDD5; box-shadow:0 4px 14px rgba(234, 88, 12, 0.08);">
                🍲
            </div>
            <h1 style="font-size:42px; color:#0F172A; margin:0 0 10px 0;">
                The Intelligent Cooking Companion
            </h1>
            <p style="font-size:17px; color:#64748B; max-width:620px; margin:0 auto; line-height:1.6;">
                Voice-first, step-by-step guidance for authentic Pakistani and South Asian cooking.
                Speak naturally in <b style="color:#0F172A;">English, Urdu, or Roman Urdu</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2, gap="large")

    with c1:
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:14px;">
                    <span class="badge-pill badge-pakistani">🇵🇰 Pakistani</span>
                    <span class="badge-pill badge-time">⏱️ 45 Mins</span>
                </div>
                <h3 style="font-size:24px; margin:0 0 10px 0; color:#0F172A;">Restaurant-Style Chicken Karahi</h3>
                <p style="color:#475569; font-size:0.92rem; line-height:1.6; margin-bottom:18px;">
                    Authentic Pakistani karahi cooked on high flame with fresh tomatoes, ginger-garlic, crushed black pepper, and fresh green chillies.
                </p>
                <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px;">
                    <span class="badge-pill badge-servings">👥 4 Servings</span>
                    <span class="badge-pill" style="background:#F8FAFC; color:#334155; border:1px solid #E2E8F0;">📋 7 Steps</span>
                    <span class="badge-pill" style="background:#FFF1F2; color:#E11D48; border:1px solid #FECDD3;">🌶️ Bhunai Style</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Cook Chicken Karahi ➔", key="start_karahi", use_container_width=True, type="primary"):
                start_new_session(1, 4)
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:14px;">
                    <span class="badge-pill badge-pakistani">🇵🇰 Pakistani</span>
                    <span class="badge-pill badge-time">⏱️ 40 Mins</span>
                </div>
                <h3 style="font-size:24px; margin:0 0 10px 0; color:#0F172A;">Comforting Tarka Daal</h3>
                <p style="color:#475569; font-size:0.92rem; line-height:1.6; margin-bottom:18px;">
                    Slow-cooked yellow lentils tempered with golden garlic, cumin seeds, and whole dried button chillies in ghee.
                </p>
                <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px;">
                    <span class="badge-pill badge-servings">👥 4 Servings</span>
                    <span class="badge-pill" style="background:#F8FAFC; color:#334155; border:1px solid #E2E8F0;">📋 7 Steps</span>
                    <span class="badge-pill" style="background:#FEF3C7; color:#B45309; border:1px solid #FDE68A;">🧈 Golden Ghee Tarka</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Cook Tarka Daal ➔", key="start_daal", use_container_width=True, type="primary"):
                start_new_session(2, 4)
                st.rerun()
