from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.cooking_session import CookingSessionRead
from app.schemas.chat import ActionExecutionSummary


class AudioTranscriptionResponse(BaseModel):
    """Result of an audio transcription request."""
    transcription: str = Field(..., description="Transcribed text from speech")
    filename: str = Field(..., description="Original audio filename processed")
    model: str = Field(..., description="Whisper model used for transcription")

    model_config = ConfigDict(from_attributes=True)


class VoiceMessageResponse(BaseModel):
    """Response returned when an audio voice snippet is processed in a cooking session."""
    transcription: str = Field(..., description="Transcribed user speech")
    reply: str = Field(..., description="Grounded natural language response from Chef AI")
    session: CookingSessionRead = Field(..., description="Authoritative cooking session state after processing")
    decision_type: str = Field(..., description="Decision type: 'execute_action', 'answer_question', 'clarify'")
    action: Optional[ActionExecutionSummary] = Field(None, description="Details of executed action if applicable")

    model_config = ConfigDict(from_attributes=True)
