"""Comprehensive Milestones 1 to 6 End-to-End Test Suite with Edge Cases.

Runs directly against the FastAPI application stack and active database/LLM.
Tests both standard happy paths and critical edge cases.
"""

import sys
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def result_box(step_num: str, title: str, passed: bool, details: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"\n{status} {step_num}: {title}")
    if details:
        for line in details.strip().split("\n"):
            print(f"       {line}")

def test_milestone_1():
    banner("MILESTONE 1: API FOUNDATION & SYSTEM HEALTH")
    
    # Happy Path: Health Check
    resp = client.get("/api/v1/health")
    passed = resp.status_code == 200 and resp.json().get("status") in ("healthy", "ok")
    result_box("1.1", "Standard Health Check (GET /api/v1/health)", passed,
               f"Status: {resp.status_code} | Body: {resp.json()}")

    # Edge Case: Unknown API endpoint returns 404
    resp_edge = client.get("/api/v1/unknown_endpoint_xyz")
    passed_edge = resp_edge.status_code == 404
    result_box("1.2 [EDGE CASE]", "Non-existent Endpoint 404 Guard", passed_edge,
               f"Status: {resp_edge.status_code} | Detail: {resp_edge.json().get('detail')}")

def test_milestone_2_and_3():
    banner("MILESTONES 2 & 3: RECIPE CATALOG & SERVING CALCULATOR")
    
    # Happy Path: List recipes
    resp = client.get("/api/v1/recipes")
    data = resp.json()
    items = data.get("items", [])
    passed = resp.status_code == 200 and len(items) > 0
    names = [f"ID {r['id']}: {r['name']} ({r['cuisine']})" for r in items]
    result_box("2.1", "List Recipe Catalog (GET /api/v1/recipes)", passed,
               "Found recipes:\n" + "\n".join(names))

    # Happy Path: Recipe details with default servings
    resp_recipe = client.get("/api/v1/recipes/1")
    r1 = resp_recipe.json()
    passed_r1 = resp_recipe.status_code == 200 and r1["id"] == 1
    result_box("2.2", f"Get Recipe Details '{r1.get('name')}' (GET /api/v1/recipes/1)", passed_r1,
               f"Ingredients Count: {len(r1.get('ingredients', []))} | Steps Count: {len(r1.get('steps', []))}")

    # Happy Path: Recipe details by slug
    resp_slug = client.get("/api/v1/recipes/slug/chicken-karahi")
    passed_slug = resp_slug.status_code == 200 and resp_slug.json()["slug"] == "chicken-karahi"
    result_box("2.3", "Get Recipe by Unique Slug (GET /api/v1/recipes/slug/chicken-karahi)", passed_slug,
               f"Slug: {resp_slug.json()['slug']} | Servings: {resp_slug.json()['default_servings']}")

    # Edge Case: Filter recipes by cuisine
    resp_filter = client.get("/api/v1/recipes?cuisine=Pakistani")
    passed_filter = resp_filter.status_code == 200 and len(resp_filter.json()["items"]) >= 2
    result_box("2.4 [EDGE CASE]", "Filter Recipe Catalog by Cuisine (cuisine=Pakistani)", passed_filter,
               f"Matched {len(resp_filter.json()['items'])} recipes for Pakistani cuisine.")

    # Edge Case: Non-existent recipe ID
    resp_404 = client.get("/api/v1/recipes/99999")
    passed_404 = resp_404.status_code == 404
    result_box("2.5 [EDGE CASE]", "Query Non-existent Recipe ID (GET /api/v1/recipes/99999)", passed_404,
               f"Status: {resp_404.status_code} | Error: {resp_404.json().get('detail')}")

def test_milestone_4():
    banner("MILESTONE 4: COOKING SESSION ENGINE & STATE MACHINE")

    # Happy Path: Create active session
    resp = client.post("/api/v1/sessions", json={"recipe_id": 1, "servings": 4})
    passed = resp.status_code == 201
    s_data = resp.json()
    session_id = s_data["id"]
    result_box("4.1", f"Start Session for Recipe ID 1 (POST /api/v1/sessions)", passed,
               f"Created Session ID: {session_id} | Status: {s_data['status']} | Step: {s_data['current_step_number']}")

    # Happy Path: Read session state
    resp_get = client.get(f"/api/v1/sessions/{session_id}")
    passed_get = resp_get.status_code == 200 and resp_get.json()["id"] == session_id
    result_box("4.2", f"Retrieve Session State (GET /api/v1/sessions/{session_id})", passed_get,
               f"Active Step #{resp_get.json()['current_step_number']}: {resp_get.json()['current_step']['instruction'][:60]}...")

    # Edge Case: Start session with non-existent recipe ID
    resp_bad_recipe = client.post("/api/v1/sessions", json={"recipe_id": 99999, "servings": 4})
    passed_bad = resp_bad_recipe.status_code == 404
    result_box("4.3 [EDGE CASE]", "Create Session with Invalid Recipe ID 99999", passed_bad,
               f"Status: {resp_bad_recipe.status_code} | Detail: {resp_bad_recipe.json().get('detail')}")

    # Edge Case: Start session with invalid servings (<=0)
    resp_invalid_serv = client.post("/api/v1/sessions", json={"recipe_id": 1, "servings": 0})
    passed_serv = resp_invalid_serv.status_code == 422
    result_box("4.4 [EDGE CASE]", "Input Validation: Reject Non-Positive Servings (servings=0)", passed_serv,
               f"Status: {resp_invalid_serv.status_code} | Rejection validated by Pydantic.")

    return session_id

def test_milestone_5(session_id: int):
    banner("MILESTONE 5: STRICTLY TYPED TOOL REGISTRY & ACTION ENGINE")

    # Happy Path: Complete active step 1 via direct session endpoint
    resp_comp = client.post(f"/api/v1/sessions/{session_id}/complete-step", json={"step_number": 1})
    passed_comp = resp_comp.status_code == 200 and resp_comp.json()["current_step_number"] == 2
    result_box("5.1", f"Complete Step 1 (POST /api/v1/sessions/{session_id}/complete-step)", passed_comp,
               f"Successfully advanced from Step 1 -> Step {resp_comp.json()['current_step_number']}")

    # Happy Path: Skip step 2 via direct session endpoint
    resp_skip = client.post(f"/api/v1/sessions/{session_id}/skip-step", json={"step_number": 2})
    passed_skip = resp_skip.status_code == 200 and resp_skip.json()["current_step_number"] == 3
    result_box("5.2", f"Skip Step 2 (POST /api/v1/sessions/{session_id}/skip-step)", passed_skip,
               f"Successfully advanced from Step 2 -> Step {resp_skip.json()['current_step_number']}")

    # Happy Path: Execute tool via Action Registry endpoint (Milestone 5 dynamic tool dispatcher)
    action_payload = {
        "action": "complete_step",
        "arguments": {"step_number": 3}
    }
    resp_tool = client.post(f"/api/v1/sessions/{session_id}/actions", json=action_payload)
    tool_data = resp_tool.json()
    passed_tool = resp_tool.status_code == 200 and tool_data.get("success") is True
    result_box("5.3", f"Action Registry Dispatch (POST /api/v1/sessions/{session_id}/actions)", passed_tool,
               f"Action: {tool_data.get('action')} | Success: {tool_data.get('success')}")

    # Edge Case: Attempt out-of-order step execution (try to complete Step 1 again while on Step 4)
    resp_bad_order = client.post(f"/api/v1/sessions/{session_id}/complete-step", json={"step_number": 1})
    passed_bad_order = resp_bad_order.status_code in (400, 409, 422)
    result_box("5.4 [EDGE CASE]", "Out-of-Order Guard: Attempt Completing Already Finished Step 1", passed_bad_order,
               f"Status: {resp_bad_order.status_code} | Safely blocked: {resp_bad_order.json().get('detail')}")

    # Edge Case: Attempt out-of-order future step (try to complete Step 7 while on Step 4)
    resp_future = client.post(f"/api/v1/sessions/{session_id}/complete-step", json={"step_number": 7})
    passed_future = resp_future.status_code in (400, 409, 422)
    result_box("5.5 [EDGE CASE]", "Out-of-Order Guard: Attempt Skipping Ahead to Step 7 Directly", passed_future,
               f"Status: {resp_future.status_code} | Safely blocked: {resp_future.json().get('detail')}")

def test_milestone_6():
    banner("MILESTONE 6: LIVE CONVERSATIONAL ORCHESTRATION & LLM INTENT")

    # Create fresh session for Chicken Karahi (4 steps)
    s_resp = client.post("/api/v1/sessions", json={"recipe_id": 1, "servings": 4})
    session_id = s_resp.json()["id"]
    print(f"Started fresh session #{session_id} for live conversational tests.\n")

    # Happy Path 1: Ask guidance (Intent: get_current_step or guidance)
    msg1 = {"message": "What should I do first?"}
    r1 = client.post(f"/api/v1/sessions/{session_id}/message", json=msg1)
    d1 = r1.json()
    passed1 = r1.status_code == 200 and "reply" in d1
    result_box("6.1", "Intent 1: Direct Guidance ('What should I do first?')", passed1,
               f"Decision: {d1.get('decision_type')} | Step: {d1['session']['current_step_number']}\n"
               f"Chef Reply: {d1.get('reply')[:120]}...")

    # Happy Path 2: Culinary Question (Intent: answer_question, ZERO state mutation)
    msg2 = {"message": "How hot should the oil be?"}
    r2 = client.post(f"/api/v1/sessions/{session_id}/message", json=msg2)
    d2 = r2.json()
    passed2 = (
        r2.status_code == 200 
        and d2.get("decision_type") == "answer_question"
        and d2["session"]["current_step_number"] == 1
    )
    result_box("6.2", "Intent 2: Culinary Q&A with Zero State Change ('How hot should the oil be?')", passed2,
               f"Decision: {d2.get('decision_type')} | Action: {d2.get('action')}\n"
               f"Step Unchanged: Step {d2['session']['current_step_number']}\n"
               f"Chef Answer: {d2.get('reply')[:120]}...")

    # Edge Case 1: Ambiguous Partial Statement (Intent: clarify)
    msg3 = {"message": "Chicken daal diya karahi mein."}
    r3 = client.post(f"/api/v1/sessions/{session_id}/message", json=msg3)
    d3 = r3.json()
    passed3 = (
        r3.status_code == 200 
        and d3.get("decision_type") == "clarify"
        and d3["session"]["current_step_number"] == 1
    )
    result_box("6.3 [EDGE CASE]", "Intent 3: Ambiguity Safety Guard ('Chicken daal diya karahi mein.')", passed3,
               f"Decision: {d3.get('decision_type')} (Did not prematurely advance step!)\n"
               f"Clarification Asked: {d3.get('reply')}")

    # Happy Path 3: Step Completion in Roman Urdu (Intent: execute_action complete_step)
    msg4 = {"message": "Step 1 mukammal ho gaya hai, chicken golden fry ho gaya hai."}
    r4 = client.post(f"/api/v1/sessions/{session_id}/message", json=msg4)
    d4 = r4.json()
    passed4 = (
        r4.status_code == 200 
        and d4["session"]["current_step_number"] == 2
    )
    result_box("6.4", "Intent 4: Roman Urdu Step Completion Advancing State", passed4,
               f"Decision: {d4.get('decision_type')} | Advanced to Step: {d4['session']['current_step_number']}\n"
               f"Chef Reply: {d4.get('reply')[:120]}...")

    # Edge Case 2: Empty or Whitespace-only Message (Rejected at API layer without wasting LLM quota)
    r_empty = client.post(f"/api/v1/sessions/{session_id}/message", json={"message": "   "})
    passed_empty = r_empty.status_code == 422
    result_box("6.5 [EDGE CASE]", "Input Guard: Reject Whitespace Message at Gateway (No LLM Quota Used)", passed_empty,
               f"Status: {r_empty.status_code} | Blocked before LLM invocation.")

    # Edge Case 3: Overly Long Message (>1000 characters)
    long_msg = "A" * 1050
    r_long = client.post(f"/api/v1/sessions/{session_id}/message", json={"message": long_msg})
    passed_long = r_long.status_code == 422
    result_box("6.6 [EDGE CASE]", "Input Guard: Reject Payload Exceeding 1000 Characters", passed_long,
               f"Status: {r_long.status_code} | Payload rejected safely.")

    # Edge Case 4: Off-topic / Unrelated question
    msg_offtopic = {"message": "Who won the cricket world cup in 1992?"}
    r_off = client.post(f"/api/v1/sessions/{session_id}/message", json=msg_offtopic)
    d_off = r_off.json()
    passed_off = (
        r_off.status_code == 200 
        and d_off["session"]["current_step_number"] == 2  # State strictly guarded
    )
    result_box("6.7 [EDGE CASE]", "Off-Topic Query Guard ('Who won the cricket world cup in 1992?')", passed_off,
               f"Decision: {d_off.get('decision_type')} | Step Unchanged: Step {d_off['session']['current_step_number']}\n"
               f"Chef Reply: {d_off.get('reply')[:120]}...")

if __name__ == "__main__":
    banner("AI COOKING COMPANION - MILESTONES 1-6 COMPREHENSIVE TEST SUITE")
    test_milestone_1()
    test_milestone_2_and_3()
    s_id = test_milestone_4()
    test_milestone_5(s_id)
    test_milestone_6()
    banner("ALL 6 MILESTONES & EDGE CASES COMPLETED!")
