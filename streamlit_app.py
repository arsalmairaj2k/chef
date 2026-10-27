import streamlit as st
import requests

st.set_page_config(
    page_title="AI Cooking Companion",
    page_icon="🍳",
    layout="wide"
)

# Configuration
API_BASE_URL = st.sidebar.text_input("Backend API Base URL", value="http://127.0.0.1:8000/api/v1")

# Initialize session state variables
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

def fetch_recipes():
    try:
        res = requests.get(f"{API_BASE_URL}/recipes", timeout=5)
        if res.status_code == 200:
            return res.json().get("items", [])
    except Exception as e:
        st.sidebar.error(f"Failed to connect to backend: {e}")
    return []

def start_new_session(recipe_id: int, servings: int):
    try:
        res = requests.post(
            f"{API_BASE_URL}/sessions",
            json={"recipe_id": recipe_id, "servings": servings},
            timeout=5
        )
        if res.status_code == 201:
            data = res.json()
            steps = data.get("steps", [])
            st.session_state.session_id = data["id"]
            st.session_state.recipe_name = data["recipe_name"]
            st.session_state.session_status = data["status"]
            st.session_state.current_step_number = data.get("current_step_number", 1)
            st.session_state.total_steps = len(steps) if steps else 1
            st.session_state.current_instruction = data["current_step"]["instruction"] if data.get("current_step") else ""
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": f"Salam! Let's cook **{data['recipe_name']}** together. I'm ready for Step 1 whenever you are!",
                    "decision": "session_start"
                }
            ]
            st.success(f"Started session #{data['id']} for {data['recipe_name']}")
        else:
            st.error(f"Error starting session: {res.text}")
    except Exception as e:
        st.error(f"Request failed: {e}")

# Sidebar: Session Controls
st.sidebar.title("🍳 Cooking Session")

# Check Health
try:
    h = requests.get(f"{API_BASE_URL}/health", timeout=3)
    if h.status_code == 200:
        st.sidebar.success("Backend: Connected (Healthy)")
    else:
        st.sidebar.warning(f"Backend returned: {h.status_code}")
except Exception:
    st.sidebar.error("Backend: Not running (Start uvicorn first)")

recipes = fetch_recipes()
recipe_options = {f"{r['name']} ({r['cuisine']})": r["id"] for r in recipes}

if recipe_options:
    selected_label = st.sidebar.selectbox("Select Recipe", list(recipe_options.keys()))
    servings = st.sidebar.number_input("Servings", min_value=1, max_value=20, value=4)
    if st.sidebar.button("Start / Restart Cooking Session", use_container_width=True):
        start_new_session(recipe_options[selected_label], servings)
else:
    st.sidebar.info("No recipes found. Ensure backend is running and seeded.")

# Main Layout
st.title("👨‍🍳 AI Cooking Companion")

if st.session_state.session_id:
    # Header card showing active progress
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        col1.subheader(f"📖 {st.session_state.recipe_name}")
        col2.metric("Step", f"{st.session_state.current_step_number} / {st.session_state.total_steps}")
        col3.metric("Status", st.session_state.session_status)

        st.info(f"**Current Instruction:**\n\n{st.session_state.current_instruction}")

    st.divider()

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "decision" in msg and msg["decision"]:
                badge_color = {
                    "execute_action": "🟢 Action Executed",
                    "answer_question": "🔵 Question Answered",
                    "clarify": "🟠 Clarification Needed",
                    "session_start": "✨ Welcome"
                }.get(msg["decision"], f"ℹ️ {msg['decision']}")
                st.caption(f"*Decision: {badge_color}*")

    # Chat input
    if prompt := st.chat_input("Ask a question, say step is done, or report progress..."):
        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Call Backend API
        with st.spinner("Chef AI is thinking..."):
            try:
                res = requests.post(
                    f"{API_BASE_URL}/sessions/{st.session_state.session_id}/message",
                    json={"message": prompt},
                    timeout=30
                )
                if res.status_code == 200:
                    data = res.json()
                    reply = data.get("reply", "")
                    decision = data.get("decision_type", "")
                    session_info = data.get("session", {})

                    # Update step status if changed
                    if session_info:
                        st.session_state.current_step_number = session_info.get("current_step_number", st.session_state.current_step_number)
                        st.session_state.session_status = session_info.get("status", st.session_state.session_status)
                        curr_step = session_info.get("current_step")
                        if curr_step and "instruction" in curr_step:
                            st.session_state.current_instruction = curr_step["instruction"]
                        elif session_info.get("status") == "COMPLETED":
                            st.session_state.current_instruction = "🎉 Recipe completed! Enjoy your meal!"

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": reply,
                        "decision": decision
                    })
                    st.rerun()
                else:
                    st.error(f"Backend error ({res.status_code}): {res.text}")
            except Exception as e:
                st.error(f"Failed to communicate with cooking engine: {e}")
else:
    st.info("👈 Select a recipe and click **'Start / Restart Cooking Session'** in the sidebar to begin!")
