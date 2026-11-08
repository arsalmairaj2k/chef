import io
import pytest
from fastapi.testclient import TestClient

from app.ai.providers import set_llm_provider
from app.ai.providers.fake import FakeLLMProvider


@pytest.fixture(autouse=True)
def ensure_fake_provider():
    set_llm_provider(FakeLLMProvider())
    yield
    set_llm_provider(None)


@pytest.fixture
def test_session_id(client: TestClient) -> int:
    recipe_payload = {
        "name": "Chicken Karahi STT Test",
        "slug": "chicken-karahi-stt-test",
        "description": "Quick karahi recipe for audio testing.",
        "cuisine": "Pakistani",
        "default_servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 25,
        "ingredients": [
            {"name": "Chicken", "quantity": 1000, "unit": "g"},
            {"name": "Tomatoes", "quantity": 500, "unit": "g"},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Fry chicken in oil until light golden.", "estimated_duration_seconds": 360},
            {"step_number": 2, "instruction": "Add ginger garlic paste and saute.", "estimated_duration_seconds": 120},
        ],
    }
    r = client.post("/api/v1/recipes", json=recipe_payload)
    assert r.status_code == 201
    recipe_id = r.json()["id"]

    s = client.post("/api/v1/sessions", json={"recipe_id": recipe_id, "servings": 4})
    assert s.status_code == 201
    return s.json()["id"]


def test_api_transcribe_audio_empty_file(client: TestClient):
    files = {"file": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    response = client.post("/api/v1/audio/transcribe", files=files)
    assert response.status_code == 422


def test_api_transcribe_audio_valid(client: TestClient):
    dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
    files = {"file": ("test.wav", io.BytesIO(dummy_wav), "audio/wav")}
    response = client.post("/api/v1/audio/transcribe", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data
    assert data["filename"] == "test.wav"
    assert data["model"] == "whisper-large-v3"


def test_api_session_voice_nonexistent_session(client: TestClient):
    dummy_wav = b"RIFF....WAVE"
    files = {"file": ("test.wav", io.BytesIO(dummy_wav), "audio/wav")}
    response = client.post("/api/v1/sessions/99999/voice", files=files)
    assert response.status_code == 404


def test_api_session_voice_full_loop(client: TestClient, test_session_id: int):
    # Upload voice note in active session
    dummy_wav = b"RIFF....WAVE"
    files = {"file": ("voice_cmd.wav", io.BytesIO(dummy_wav), "audio/wav")}
    response = client.post(f"/api/v1/sessions/{test_session_id}/voice", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data
    assert "reply" in data
    assert "session" in data
    assert "decision_type" in data
    assert data["session"]["id"] == test_session_id
