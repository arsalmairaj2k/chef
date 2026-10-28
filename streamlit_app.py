import streamlit as st
import requests

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

API_BASE_URL = st.sidebar.text_input(
    "API Host",
    value="http://127.0.0.1:8000/api/v1",
    help="FastAPI backend endpoint"
)

def check_health():
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if r.status_code == 200:
            return True, r.json().get("version", "0.1.0")
    except Exception:
        pass
    return False, None

is_healthy, app_ver = check_health()
if is_healthy:
    st.sidebar.markdown(f'<span class="badge-pill" style="background:#F0FDF4; color:#15803D; border:1px solid #BBF7D0;">● System Online v{app_ver}</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<span class="badge-pill" style="background:#FEF2F2; color:#B91C1C; border:1px solid #FECACA;">● Backend Disconnected</span>', unsafe_allow_html=True)
    st.sidebar.caption("Run: `.venv\\Scripts\\python -m uvicorn app.main:app --reload`")

def fetch_recipes():
    try:
        res = requests.get(f"{API_BASE_URL}/recipes", timeout=5)
        if res.status_code == 200:
            return res.json().get("items", [])
    except Exception:
        pass
    return []

def start_new_session(recipe_id: int, servings_count: int):
    try:
        res = requests.post(
            f"{API_BASE_URL}/sessions",
            json={"recipe_id": recipe_id, "servings": servings_count},
            timeout=8
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

            curr = data.get("current_step")
            if curr:
                st.session_state.current_instruction = curr.get("instruction", "")
                st.session_state.est_duration = curr.get("estimated_duration_seconds")
            else:
                st.session_state.current_instruction = ""
                st.session_state.est_duration = None

            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": f"**Assalam-o-Alaikum!** I'm your dedicated Chef companion for **{data['recipe_name']}** ({servings_count} servings).\n\nWhenever you're ready, let's begin with **Step 1**. Feel free to talk to me naturally in **English, Urdu, or Roman Urdu**!",
                    "decision": "session_start"
                }
            ]
            st.toast(f"Cooking Session #{data['id']} Ready!", icon="✨")
        else:
            st.sidebar.error(f"Failed to start session: {res.text}")
    except Exception as e:
        st.sidebar.error(f"Request failed: {e}")

st.sidebar.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
st.sidebar.markdown("<h4 style='font-size:14px; text-transform:uppercase; letter-spacing:0.06em; color:#64748B;'>Select Recipe</h4>", unsafe_allow_html=True)

recipes = fetch_recipes()
recipe_map = {f"{r['name']} ({r['cuisine']})": r for r in recipes}

if recipe_map:
    selected_name = st.sidebar.selectbox("Recipe", list(recipe_map.keys()), label_visibility="collapsed")
    selected_recipe = recipe_map[selected_name]

    c_serv, c_time = st.sidebar.columns(2)
    with c_serv:
        servings = st.number_input("Servings", min_value=1, max_value=20, value=selected_recipe.get("default_servings", 4))
    with c_time:
        tot_time = (selected_recipe.get("prep_time_minutes") or 0) + (selected_recipe.get("cook_time_minutes") or 0)
        st.metric("Total Time", f"{tot_time}m")

    if st.sidebar.button("Start Cooking Session", use_container_width=True, type="primary"):
        start_new_session(selected_recipe["id"], servings)
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

        # Quick Action Shortcuts (Hands-Free simulation)
        st.caption("Quick actions:")
        btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
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

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Chat History Container
        chat_box = st.container()
        with chat_box:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"], avatar="👨‍🍳" if msg["role"] == "assistant" else "👤"):
                    st.markdown(msg["content"])
                    if "decision" in msg and msg["decision"]:
                        d = msg["decision"]
                        tag_html = {
                            "execute_action": '<span class="decision-tag tag-execute">🟢 Action Verified</span>',
                            "answer_question": '<span class="decision-tag tag-answer">🔵 Culinary Advice</span>',
                            "clarify": '<span class="decision-tag tag-clarify">🟠 Clarification Requested</span>',
                            "session_start": '<span class="decision-tag tag-execute">✨ Session Active</span>'
                        }.get(d, f'<span class="decision-tag tag-answer">{d}</span>')
                        st.markdown(tag_html, unsafe_allow_html=True)

        # Inbound Chat Input
        user_input = st.chat_input("Speak or type in English, Roman Urdu, or Urdu...")
        if st.session_state.pending_quick_message:
            user_input = st.session_state.pending_quick_message
            st.session_state.pending_quick_message = None

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)

            with st.spinner("Chef AI is reviewing your recipe state..."):
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/sessions/{st.session_state.session_id}/message",
                        json={"message": user_input},
                        timeout=30
                    )
                    if res.status_code == 200:
                        data = res.json()
                        reply = data.get("reply", "")
                        decision = data.get("decision_type", "")
                        session_info = data.get("session", {})

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
                        st.error(f"Backend Error ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    with right_col:
        tab_ing, tab_map, tab_tips = st.tabs(["🧂 Ingredients", "📋 Roadmap", "💡 Tips"])

        with tab_ing:
            st.markdown("<h4 style='font-size:16px; margin-top:8px;'>Ingredients Needed</h4>", unsafe_allow_html=True)
            st.caption(f"Exact quantities scaled for **{servings} servings**:")
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
