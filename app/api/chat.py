from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.chat_service import ChatService
from app.services.session_service import SessionNotFoundError
from app.ai.providers.base import (
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMInvalidOutputError,
    LLMProviderUnavailableError,
)


router = APIRouter(prefix="/sessions", tags=["chat"])


@router.post(
    "/{session_id}/message",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a conversational cooking message to guide recipe progress",
)
def send_session_message(
    session_id: int = Path(..., gt=0, description="Active cooking session ID"),
    payload: ChatMessageRequest = ...,
    db: Session = Depends(get_db),
) -> ChatMessageResponse:
    """Interprets user cooking statement, selects allowlisted backend actions, and returns a grounded reply."""
    try:
        return ChatService.process_message(
            db=db,
            session_id=session_id,
            message=payload.message,
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except LLMTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"LLM request timed out: {e.message}",
        )
    except LLMRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"LLM rate limit reached: {e.message}",
        )
    except LLMAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM provider authentication error: {e.message}",
        )
    except (LLMInvalidOutputError, LLMProviderUnavailableError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM provider error: {e.message}",
        )
    except LLMError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal LLM processing error: {e.message}",
        )
