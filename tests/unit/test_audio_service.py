import pytest
from unittest.mock import MagicMock, patch
from groq import RateLimitError, AuthenticationError, APIError
import httpx

from app.services.audio_service import (
    AudioTranscriptionService,
    AudioTranscriptionError,
    GroqMissingKeyError,
    GroqRateLimitError,
    GroqAuthenticationError,
)
from app.core.config import Settings


def test_transcribe_rejects_empty_bytes():
    with pytest.raises(AudioTranscriptionError) as exc_info:
        AudioTranscriptionService.transcribe(b"")
    assert exc_info.value.status_code == 422
    assert "empty" in exc_info.value.message.lower()


def test_transcribe_offline_test_fallback():
    # In test environment, missing key returns deterministic test string
    dummy_wav = b"RIFF....WAVEfmt ...."
    result = AudioTranscriptionService.transcribe(dummy_wav, api_key=None)
    assert isinstance(result, str)
    assert len(result) > 0


def test_transcribe_raises_missing_key_in_production():
    dummy_wav = b"RIFF....WAVEfmt ...."
    # Override provider and settings to simulate production environment without key
    with patch("app.services.audio_service.get_llm_provider", return_value=None):
        with patch("app.services.audio_service.get_settings") as mock_settings:
            mock_settings.return_value = Settings(app_env="production", llm_provider="gemini", groq_api_key=None)
            with pytest.raises(GroqMissingKeyError) as exc_info:
                AudioTranscriptionService.transcribe(dummy_wav, api_key=None)
            assert exc_info.value.status_code == 503


@patch("app.services.audio_service.Groq")
def test_transcribe_successful_groq_call(mock_groq_class):
    mock_client = MagicMock()
    mock_transcription = MagicMock()
    mock_transcription.text = "Chicken fry ho gaya hai agla step"
    mock_client.audio.transcriptions.create.return_value = mock_transcription
    mock_groq_class.return_value = mock_client

    audio_bytes = b"fake-audio-bytes"
    result = AudioTranscriptionService.transcribe(audio_bytes, api_key="gsk_test123")

    assert result == "Chicken fry ho gaya hai agla step"
    mock_client.audio.transcriptions.create.assert_called_once()


@patch("app.services.audio_service.Groq")
def test_transcribe_handles_rate_limit(mock_groq_class):
    mock_client = MagicMock()
    request = httpx.Request("POST", "https://api.groq.com")
    response = httpx.Response(429, request=request)
    mock_client.audio.transcriptions.create.side_effect = RateLimitError(
        message="Rate limit exceeded", response=response, body=None
    )
    mock_groq_class.return_value = mock_client

    with pytest.raises(GroqRateLimitError) as exc_info:
        AudioTranscriptionService.transcribe(b"audio-bytes", api_key="gsk_test")
    assert exc_info.value.status_code == 429


@patch("app.services.audio_service.Groq")
def test_transcribe_handles_auth_error(mock_groq_class):
    mock_client = MagicMock()
    request = httpx.Request("POST", "https://api.groq.com")
    response = httpx.Response(401, request=request)
    mock_client.audio.transcriptions.create.side_effect = AuthenticationError(
        message="Invalid key", response=response, body=None
    )
    mock_groq_class.return_value = mock_client

    with pytest.raises(GroqAuthenticationError) as exc_info:
        AudioTranscriptionService.transcribe(b"audio-bytes", api_key="gsk_invalid")
    assert exc_info.value.status_code == 502
