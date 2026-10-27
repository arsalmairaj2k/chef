import json
from fastapi.testclient import TestClient
from app.main import app

def run_option_b():
    client = TestClient(app)
    print("=" * 60)
    print("   AI COOKING COMPANION - OPTION B END-TO-END DEMO   ")
    print("=" * 60)

    # Step 1: Inspect Recipe Catalog (Milestone 3)
    print("\n--- STEP 1: Inspect Recipe Catalog (GET /api/v1/recipes) ---")
    resp1 = client.get("/api/v1/recipes")
    print(f"Status Code: {resp1.status_code}")
    recipes = resp1.json()
    for item in recipes.get("items", []):
        print(f"  [ID {item['id']}] {item['name']} ({item['cuisine']}) - {item['default_servings']} servings")

    # Step 2: Start Cooking Session for Chicken Karahi (Milestone 4)
    print("\n--- STEP 2: Start Cooking Session (POST /api/v1/sessions) ---")
    resp2 = client.post("/api/v1/sessions", json={"recipe_id": 1, "servings": 4})
    print(f"Status Code: {resp2.status_code}")
    session_data = resp2.json()
    session_id = session_data["id"]
    print(f"  Created Session ID: {session_id}")
    print(f"  Recipe: {session_data['recipe_name']}")
    print(f"  Session Status: {session_data['status']}")
    print(f"  Current Step Number: {session_data['current_step_number']}")
    print(f"  Active Step Instruction: {session_data['current_step']['instruction']}")

    # Step 3: Conversational Chat with LLM - Ask what to do first (Milestone 6)
    print("\n--- STEP 3: Chat with Gemini LLM - 'What should I do first?' ---")
    msg1 = {"message": "What should I do first?"}
    resp3 = client.post(f"/api/v1/sessions/{session_id}/message", json=msg1)
    print(f"Status Code: {resp3.status_code}")
    chat1 = resp3.json()
    print(f"  Decision Type: {chat1['decision_type']}")
    print(f"  AI Reply: {chat1['reply']}")
    print(f"  Current Step: {chat1['session']['current_step_number']}")

    # Step 4: Culinary Question without state change
    print("\n--- STEP 4: Culinary Question - 'How hot should the oil be?' ---")
    msg2 = {"message": "How hot should the oil be?"}
    resp4 = client.post(f"/api/v1/sessions/{session_id}/message", json=msg2)
    print(f"Status Code: {resp4.status_code}")
    chat2 = resp4.json()
    print(f"  Decision Type: {chat2['decision_type']}")
    print(f"  AI Reply: {chat2['reply']}")
    print(f"  Action Executed: {chat2.get('action')}")
    print(f"  Current Step Remains: {chat2['session']['current_step_number']}")

    # Step 5: Complete Step 1 using Roman Urdu / English
    print("\n--- STEP 5: Complete Step 1 - 'Step 1 ho gaya, oil is hot.' ---")
    msg3 = {"message": "Step 1 ho gaya, oil is hot."}
    resp5 = client.post(f"/api/v1/sessions/{session_id}/message", json=msg3)
    print(f"Status Code: {resp5.status_code}")
    chat3 = resp5.json()
    print(f"  Decision Type: {chat3['decision_type']}")
    print(f"  Action Summary: {json.dumps(chat3['action'], indent=4)}")
    print(f"  AI Reply: {chat3['reply']}")
    print(f"  Advanced to Step: {chat3['session']['current_step_number']}")

    # Step 6: Ambiguous Message triggers clarification
    print("\n--- STEP 6: Ambiguity Test - 'Chicken daal diya' ---")
    msg4 = {"message": "Chicken daal diya"}
    resp6 = client.post(f"/api/v1/sessions/{session_id}/message", json=msg4)
    print(f"Status Code: {resp6.status_code}")
    chat4 = resp6.json()
    print(f"  Decision Type: {chat4['decision_type']}")
    print(f"  AI Reply (Clarification): {chat4['reply']}")
    print(f"  Current Step Remains: {chat4['session']['current_step_number']}")
    print("\n" + "=" * 60)
    print("   ALL OPTION B MILESTONES EXECUTED SUCCESSFULLY!   ")
    print("=" * 60)

if __name__ == "__main__":
    run_option_b()
