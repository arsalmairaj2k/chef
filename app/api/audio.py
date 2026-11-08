import logging
from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.config import get_settings
from app.schemas.audio import AudioTranscriptionResponse, VoiceMessageResponse
from app.services.audio_service import (
    AudioTranscriptionService,
    AudioTranscriptionError,
    GroqMissingKeyError,
    GroqRateLimitError,
    GroqAuthenticationError,
)
from app.services.chat_service import ChatService
from app.services.session_service import SessionService, SessionNotFoundError
from app.ai.providers.base import LLMError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audio"])


@router.post(
    "/audio/transcribe",
    response_model=AudioTranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe spoken cooking audio via Groq Whisper",
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (WAV, MP3, WEBM, M4A)"),
) -> AudioTranscriptionResponse:
    """Accepts an audio file and returns high-accuracy speech transcription using Groq's whisper-large-v3."""
    try:
        content = await file.read()
        transcription = AudioTranscriptionService.transcribe(
            file_bytes=content,
            filename=file.filename or "audio.wav",
        )
        settings = get_settings()
        return AudioTranscriptionResponse(
            transcription=transcription,
            filename=file.filename or "audio.wav",
            model=settings.groq_whisper_model or "whisper-large-v3",
        )
    except AudioTranscriptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("Failed to transcribe audio upload: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/sessions/{session_id}/voice",
    response_model=VoiceMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a voice note directly in a cooking session",
)
async def process_session_voice(
    session_id: int = Path(..., gt=0, description="Active cooking session ID"),
    file: UploadFile = File(..., description="Recorded voice audio file"),
    db: Session = Depends(get_db),
) -> VoiceMessageResponse:
    """
    1. Validates that the session exists.
    2. Transcribes spoken audio via Groq Whisper.
    3. Passes transcribed text to Chef AI intent interpreter and state machine.
    4. Returns both the recognized text and grounded response in one roundtrip.
    """
    try:
        # Verify session existence
        SessionService.get_session(db, session_id)

        content = await file.read()
        transcription = AudioTranscriptionService.transcribe(
            file_bytes=content,
            filename=file.filename or "voice_input.wav",
        )

        chat_response = ChatService.process_message(
            db=db,
            session_id=session_id,
            message=transcription,
        )

        return VoiceMessageResponse(
            transcription=transcription,
            reply=chat_response.reply,
            session=chat_response.session,
            decision_type=chat_response.decision_type,
            action=chat_response.action,
        )

    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AudioTranscriptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except LLMError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"LLM Error: {e.message}")
    except Exception as e:
        logger.error("Voice processing error on session %s: %s", session_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
