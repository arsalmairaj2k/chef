import streamlit as st
import requests

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Chef AI — Smart Cooking Companion",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System (Warm Desi Culinary & Modern Glassmorphism Theme)
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

h1, h2, h3, h4, .brand-font {
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: -0.02em;
}

/* App Background subtle radial glow */
.stApp {
    background-color: #0d0f15;
    background-image: radial-gradient(circle at 15% 10%, rgba(245, 158, 11, 0.07) 0%, transparent 40%),
                      radial-gradient(circle at 85% 85%, rgba(239, 68, 68, 0.05) 0%, transparent 45%);
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #12151e !important;
    border-right: 1px solid rgba(255, 255, 255, 0.07);
}

/* Card Containers */
.chef-card {
    background: #171b26;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
}

.step-hero-card {
    background: linear-gradient(135deg, rgba(30, 36, 52, 0.95) 0%, rgba(20, 24, 36, 0.95) 100%);
    border: 1px solid rgba(245, 158, 11, 0.25);
    border-radius: 16px;
    padding: 22px 26px;
    margin-bottom: 18px;
    box-shadow: 0 8px 30px rgba(245, 158, 11, 0.06);
}

/* Badges & Tags */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-active {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-pakistani {
    background: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.25);
}

.badge-step {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

/* Quick Action Buttons */
.quick-prompt-btn {
    display: inline-block;
    padding: 6px 14px;
    margin: 4px 4px 6px 0;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    color: #e2e8f0;
    font-size: 0.84rem;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

/* Custom progress bar */
.stProgress > div > div > div > div {
    background-color: #f59e0b !important;
}

/* Metric styling */
[data-testid="stMetricValue"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.8rem !important;
    color: #f59e0b !important;
}

/* Chat bubble styling */
.chat-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    margin-top: 6px;
}
.badge-executed { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-answered { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
.badge-clarify  { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# STATE INITIALIZATION
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
# API HELPERS
# -----------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <span style="font-size:32px;">👨‍🍳</span>
        <div>
            <h2 class="brand-font" style="margin:0; font-size:22px; color:#f59e0b;">Chef AI</h2>
            <span style="font-size:12px; color:#94a3b8; letter-spacing:0.04em;">Desi Cooking Companion 🇵🇰</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

API_BASE_URL = st.sidebar.text_input(
    "API Endpoint",
    value="http://127.0.0.1:8000/api/v1",
    help="FastAPI backend base URL"
)

def check_backend_health():
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if r.status_code == 200:
            return True, r.json().get("version", "0.1.0")
    except Exception:
        pass
    return False, None

is_healthy, app_version = check_backend_health()
if is_healthy:
    st.sidebar.markdown(f'<div class="badge-pill badge-active">● Connected v{app_version}</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="badge-pill" style="background:rgba(239,68,68,0.15); color:#f87171;">● Backend Offline</div>', unsafe_allow_html=True)
    st.sidebar.caption("Run: `.venv\\Scripts\\python -m uvicorn app.main:app --reload`")

def fetch_recipes():
    try:
        res = requests.get(f"{API_BASE_URL}/recipes", timeout=5)
        if res.status_code == 200:
            return res.json().get("items", [])
    except Exception:
        pass
    return []

def start_new_session(recipe_id: int, servings: int):
    try:
        res = requests.post(
            f"{API_BASE_URL}/sessions",
            json={"recipe_id": recipe_id, "servings": servings},
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
                    "content": f"**Assalam-o-Alaikum!** Ready to cook authentic **{data['recipe_name']}** ({servings} servings)?\n\nI will guide you step by step with exact ingredient quantities. Feel free to talk to me naturally in **English, Urdu, or Roman Urdu**!",
                    "decision": "session_start"
                }
            ]
            st.toast(f"Session #{data['id']} started for {data['recipe_name']}!", icon="🔥")
        else:
            st.sidebar.error(f"Failed to start session: {res.text}")
    except Exception as e:
        st.sidebar.error(f"Request failed: {e}")

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📖 Recipe Selection")

recipes = fetch_recipes()
recipe_map = {f"{r['name']} ({r['cuisine']})": r for r in recipes}

if recipe_map:
    selected_name = st.sidebar.selectbox("Choose a Recipe", list(recipe_map.keys()))
    selected_recipe = recipe_map[selected_name]

    col_serv, col_time = st.sidebar.columns(2)
    with col_serv:
        servings = st.number_input("Servings", min_value=1, max_value=20, value=selected_recipe.get("default_servings", 4))
    with col_time:
        total_time = (selected_recipe.get("prep_time_minutes") or 0) + (selected_recipe.get("cook_time_minutes") or 0)
        st.metric("Total Time", f"~{total_time}m")

    if st.sidebar.button("🍳 Start / Reset Session", use_container_width=True, type="primary"):
        start_new_session(selected_recipe["id"], servings)
else:
    st.sidebar.info("No recipes found in catalog. Ensure database is seeded.")

st.sidebar.markdown("---")
with st.sidebar.expander("🗣️ Conversational Tips"):
    st.markdown(
        """
        You can talk to the Chef completely naturally:
        - **Guidance**: *"Ab kya karna hai?"*
        - **Declaration**: *"Step 1 mukammal ho gaya"*
        - **Culinary Advice**: *"Oil kitna garam hona chahiye?"*
        - **Substitutions**: *"Can I use ghee instead?"*
        - **Ingredients**: *"Is step mein kitni mirch daalni hai?"*
        """
    )

# -----------------------------------------------------------------------------
# MAIN DASHBOARD LAYOUT
# -----------------------------------------------------------------------------
if st.session_state.session_id:
    # Top Bar: Session Info & Metrics
    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
    with header_col1:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                <h1 style="margin:0; font-size:32px;">{st.session_state.recipe_name}</h1>
                <span class="badge-pill badge-pakistani">🇵🇰 Pakistani</span>
                <span class="badge-pill badge-active">● {st.session_state.session_status}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with header_col2:
        st.metric("Active Step", f"Step {st.session_state.current_step_number} of {st.session_state.total_steps}")
    with header_col3:
        progress_val = min(1.0, max(0.0, st.session_state.current_step_number / max(1, st.session_state.total_steps)))
        dur_mins = round(st.session_state.est_duration / 60) if st.session_state.est_duration else None
        st.metric("Step Duration", f"~{dur_mins} mins" if dur_mins else "Flexible")

    # Step Progress Bar
    progress_ratio = st.session_state.current_step_number / max(1, st.session_state.total_steps)
    st.progress(progress_ratio)

    # TWO-COLUMN WORKSPACE: Chat Assistant (60%) vs Mise en Place / Timeline (40%)
    col_chat, col_info = st.columns([1.2, 0.8], gap="large")

    with col_chat:
        # Active Step Hero Banner
        st.markdown(
            f"""
            <div class="step-hero-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <span class="badge-pill badge-step">Current Step #{st.session_state.current_step_number}</span>
                    <span style="font-size:12px; color:#94a3b8;">Authoritative State Verified ✔</span>
                </div>
                <div style="font-size:1.15rem; font-weight:600; line-height:1.6; color:#f8fafc;">
                    {st.session_state.current_instruction}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Quick Suggestion Chips (Kitchen-friendly hands-free simulation)
        st.caption("⚡ Quick Actions:")
        chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
        if chip_col1.button("✅ Step Done", use_container_width=True):
            st.session_state.pending_quick_message = f"Step {st.session_state.current_step_number} done, next step kya hai?"
            st.rerun()
        if chip_col2.button("🧂 Ingredients", use_container_width=True):
            st.session_state.pending_quick_message = "Is step mein kitne ingredients daalne hain?"
            st.rerun()
        if chip_col3.button("🔥 Heat / Temp", use_container_width=True):
            st.session_state.pending_quick_message = "Aanch (flame) kitni honi chahiye?"
            st.rerun()
        if chip_col4.button("⏭️ Skip Step", use_container_width=True):
            st.session_state.pending_quick_message = "Skip this step."
            st.rerun()

        # Chat Stream
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"], avatar="👨‍🍳" if msg["role"] == "assistant" else "👤"):
                    st.markdown(msg["content"])
                    if "decision" in msg and msg["decision"]:
                        dec = msg["decision"]
                        badge_html = {
                            "execute_action": '<span class="chat-badge badge-executed">🟢 Action Executed</span>',
                            "answer_question": '<span class="chat-badge badge-answered">🔵 Question Answered</span>',
                            "clarify": '<span class="chat-badge badge-clarify">🟠 Clarification Needed</span>',
                            "session_start": '<span class="chat-badge badge-executed">✨ Session Initialized</span>'
                        }.get(dec, f'<span class="chat-badge badge-answered">{dec}</span>')
                        st.markdown(badge_html, unsafe_allow_html=True)

        # Handle either chat input or quick prompt button
        user_prompt = st.chat_input("Speak or type in English, Roman Urdu, or Urdu...")
        if st.session_state.pending_quick_message:
            user_prompt = st.session_state.pending_quick_message
            st.session_state.pending_quick_message = None

        if user_prompt:
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_prompt)

            with st.spinner("Chef AI is thinking..."):
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/sessions/{st.session_state.session_id}/message",
                        json={"message": user_prompt},
                        timeout=30
                    )
                    if res.status_code == 200:
                        data = res.json()
                        reply = data.get("reply", "")
                        decision = data.get("decision_type", "")
                        session_info = data.get("session", {})

                        # Refresh session state
                        if session_info:
                            st.session_state.current_step_number = session_info.get("current_step_number", st.session_state.current_step_number)
                            st.session_state.session_status = session_info.get("status", st.session_state.session_status)
                            curr_step = session_info.get("current_step")
                            if curr_step and "instruction" in curr_step:
                                st.session_state.current_instruction = curr_step["instruction"]
                                st.session_state.est_duration = curr_step.get("estimated_duration_seconds")
                            elif session_info.get("status") == "COMPLETED":
                                st.session_state.current_instruction = "🎉 Recipe successfully completed! Bon Appétit / Nosh-e-Jaan!"

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": reply,
                            "decision": decision
                        })
                        st.rerun()
                    else:
                        st.error(f"Backend returned error ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    with col_info:
        tab_ingredients, tab_steps, tab_notes = st.tabs(["🧂 Mise en Place", "📋 Step Roadmap", "💡 Chef Notes"])

        with tab_ingredients:
            st.markdown("#### Scaled Ingredients")
            st.caption(f"Quantities automatically calculated for **{servings} servings**:")
            if st.session_state.ingredients:
                for idx, ing in enumerate(st.session_state.ingredients):
                    qty_str = f"{ing['quantity']} {ing['unit'] or ''}".strip() if ing.get("quantity") else "To taste"
                    notes_str = f" *({ing['notes']})*" if ing.get("notes") else ""
                    st.checkbox(f"**{ing['ingredient_name']}** — {qty_str}{notes_str}", key=f"ing_{idx}", value=False)
            else:
                st.info("Ingredients will load as you cook.")

        with tab_steps:
            st.markdown("#### Recipe Roadmap")
            if st.session_state.steps_list:
                for s in st.session_state.steps_list:
                    step_num = s["step_number"]
                    is_current = (step_num == st.session_state.current_step_number)
                    is_done = (step_num < st.session_state.current_step_number) or (st.session_state.session_status == "COMPLETED")

                    icon = "✅" if is_done else ("🔥" if is_current else "⏳")
                    style_border = "border-left: 3px solid #f59e0b; padding-left: 8px; margin-bottom: 8px;" if is_current else "margin-bottom: 8px;"
                    st.markdown(
                        f"""
                        <div style="{style_border}">
                            <b>{icon} Step {step_num}</b><br>
                            <span style="font-size:0.85rem; color:#94a3b8;">{s['instruction']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.caption("Steps list not available.")

        with tab_notes:
            st.markdown("#### South Asian Cooking Tips")
            st.info(
                """
                - **Bhunai Technique**: When bhunaoing meat or masala, wait until oil visibly separates (*tail alag ho jaye*). That is the authentic marker of depth of flavor.
                - **Tempering (Tarka)**: Always pour hot tarka quickly into the lentils and instantly seal with lid for 1 minute to trap aromatic volatilized oils.
                - **Fresh Ginger**: Always add julienned ginger right at the end to keep the bite and aromatics crisp.
                """
            )

else:
    # Welcome Splash Screen (No Active Session)
    st.markdown(
        """
        <div style="text-align:center; padding: 40px 20px 20px 20px;">
            <span style="font-size:64px;">🥘</span>
            <h1 class="brand-font" style="font-size:42px; color:#f59e0b; margin-top:10px;">
                Pakistan's First AI Cooking Companion
            </h1>
            <p style="font-size:18px; color:#cbd5e1; max-width:650px; margin:0 auto 30px auto; line-height:1.6;">
                Hands-free, step-by-step guidance through authentic South Asian recipes. 
                Speaks your kitchen's language — <b>English, Urdu, and Roman Urdu</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown(
            """
            <div class="chef-card">
                <h3>🍗 Restaurant-Style Chicken Karahi</h3>
                <p style="color:#94a3b8; font-size:0.9rem;">
                    Rich, fiery karahi cooked on high flame with fresh tomatoes, green chillies, crushed black pepper, and julienned ginger.
                </p>
                <div style="display:flex; gap:10px; margin-top:10px;">
                    <span class="badge-pill badge-pakistani">🇵🇰 Pakistani</span>
                    <span class="badge-pill badge-step">⏱️ 45 Mins</span>
                    <span class="badge-pill badge-active">4 Servings</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Cook Chicken Karahi Now ➔", use_container_width=True, type="primary"):
            start_new_session(1, 4)
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="chef-card">
                <h3>🍲 Classic Tarka Daal</h3>
                <p style="color:#94a3b8; font-size:0.9rem;">
                    Hearty yellow moong and masoor lentils tempered with aromatic golden garlic, cumin seeds, and whole button red chillies in ghee.
                </p>
                <div style="display:flex; gap:10px; margin-top:10px;">
                    <span class="badge-pill badge-pakistani">🇵🇰 Pakistani</span>
                    <span class="badge-pill badge-step">⏱️ 40 Mins</span>
                    <span class="badge-pill badge-active">4 Servings</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Cook Tarka Daal Now ➔", use_container_width=True, type="primary"):
            start_new_session(2, 4)
            st.rerun()
