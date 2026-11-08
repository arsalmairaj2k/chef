import io
import logging
from typing import Optional

try:
    from groq import Groq, APIError, RateLimitError, AuthenticationError
except ImportError:
    Groq = None  # type: ignore
    APIError = Exception  # type: ignore
    RateLimitError = Exception  # type: ignore
    AuthenticationError = Exception  # type: ignore

from app.core.config import get_settings
from app.ai.providers import get_llm_provider
from app.ai.providers.fake import FakeLLMProvider

logger = logging.getLogger(__name__)

CULINARY_WHISPER_PROMPT = (
    "Authentic Pakistani and South Asian cooking instructions, ingredients, Roman Urdu, "
    "Urdu, and English code-switching. Chicken karahi, bhunai, tarka, daal, pyaz, tamatar, "
    "namak, garam masala, adrak lehsun, dum, aanch, agla step, ho gaya, timer shuru."
)


class AudioTranscriptionError(Exception):
    """Base error for audio transcription failures."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GroqMissingKeyError(AudioTranscriptionError):
    """Raised when Groq API key is required but not configured."""
    def __init__(self, message: str = "Groq API key is not configured. Please set GROQ_API_KEY in your environment."):
        super().__init__(message, status_code=503)


class GroqRateLimitError(AudioTranscriptionError):
    """Raised when Groq Whisper rate limit is exceeded."""
    def __init__(self, message: str = "Groq Whisper transcription rate limit exceeded. Please wait a moment."):
        super().__init__(message, status_code=429)


class GroqAuthenticationError(AudioTranscriptionError):
    """Raised when Groq API key is invalid."""
    def __init__(self, message: str = "Invalid Groq API key provided."):
        super().__init__(message, status_code=502)


class AudioTranscriptionService:
    """Service for transcribing spoken cooking instructions using Groq Whisper."""

    @classmethod
    def transcribe(
        cls,
        file_bytes: bytes,
        filename: str = "audio.wav",
        api_key: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """
        Transcribes audio bytes to text using Groq's whisper-large-v3 model.
        Falls back to deterministic mock if in test environment with fake provider.
        """
        if not file_bytes or len(file_bytes) == 0:
            raise AudioTranscriptionError("Uploaded audio file is empty.", status_code=422)

        settings = get_settings()
        effective_key = api_key or settings.groq_api_key
        current_provider = get_llm_provider()

        # Offline/Testing Mock Mode: Deterministic mock for unit/integration tests with FakeLLMProvider
        if isinstance(current_provider, FakeLLMProvider) or settings.app_env == "test":
            logger.info("Using mock audio transcription for test environment.")
            return "Maine chicken fry kar liya hai, agla step kya hai?"

        if not effective_key:
            raise GroqMissingKeyError(
                "Groq API key not configured. Get a free key at https://console.groq.com and set GROQ_API_KEY in .env"
            )

        if Groq is None:
            raise AudioTranscriptionError(
                "The 'groq' package is not installed on the server. Please add 'groq>=0.9.0' to requirements.txt.",
                status_code=503,
            )

        try:
            client = Groq(api_key=effective_key)
            model_name = settings.groq_whisper_model or "whisper-large-v3"

            # Prepare file tuple for Groq SDK: (filename, file_content, mime_type)
            file_payload = (filename, io.BytesIO(file_bytes), "application/octet-stream")

            kwargs = {
                "file": file_payload,
                "model": model_name,
                "prompt": CULINARY_WHISPER_PROMPT,
                "response_format": "json",
                "temperature": 0.0,
            }
            if language:
                kwargs["language"] = language

            transcription = client.audio.transcriptions.create(**kwargs)
            transcribed_text = transcription.text.strip() if hasattr(transcription, "text") else str(transcription).strip()

            if not transcribed_text:
                raise AudioTranscriptionError("Speech could not be recognized. Please speak clearly into the microphone.", status_code=422)

            logger.info("Groq Whisper transcribed audio (%d bytes) -> '%s'", len(file_bytes), transcribed_text)
            return transcribed_text

        except RateLimitError as e:
            logger.warning("Groq Whisper rate limit exceeded: %s", e)
            raise GroqRateLimitError(str(e)) from e
        except AuthenticationError as e:
            logger.error("Groq Whisper authentication error: %s", e)
            raise GroqAuthenticationError(str(e)) from e
        except APIError as e:
            logger.error("Groq Whisper API error (%s): %s", getattr(e, "status_code", 500), e)
            raise AudioTranscriptionError(f"Groq transcription API error: {e}", status_code=getattr(e, "status_code", 500)) from e
        except AudioTranscriptionError:
            raise
        except Exception as e:
            logger.error("Unexpected error during audio transcription: %s", e)
            raise AudioTranscriptionError(f"Unexpected error during transcription: {e}", status_code=500) from e
