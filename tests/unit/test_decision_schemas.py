import pytest
from pydantic import ValidationError, TypeAdapter

from app.ai.decision_schemas import (
    ExecuteActionDecision,
    AnswerQuestionDecision,
    ClarifyDecision,
    LLMDecision,
)


decision_adapter = TypeAdapter(LLMDecision)


def test_valid_execute_action_decision():
    """Verify valid action decision creates successfully."""
    dec = ExecuteActionDecision(
        action="complete_step",
        arguments={"step_number": 1},
    )
    assert dec.type == "execute_action"
    assert dec.action == "complete_step"
    assert dec.arguments == {"step_number": 1}


def test_execute_action_rejects_unknown_action():
    """Verify unapproved action names fail validation."""
    with pytest.raises(ValidationError, match="not allowlisted"):
        ExecuteActionDecision(
            action="drop_table",
            arguments={},
        )


def test_execute_action_rejects_extra_fields():
    """Verify unexpected extra fields are forbidden."""
    with pytest.raises(ValidationError):
        ExecuteActionDecision.model_validate({
            "type": "execute_action",
            "action": "complete_step",
            "arguments": {"step_number": 1},
            "unauthorized_field": "injected",
        })


def test_valid_answer_question_decision():
    """Verify answer question decision parses properly."""
    dec = AnswerQuestionDecision(
        question="Why brown the meat first?",
        answer="Browning creates flavorful crust via the Maillard reaction.",
    )
    assert dec.type == "answer_question"
    assert "Maillard" in dec.answer


def test_answer_question_rejects_extra_fields():
    with pytest.raises(ValidationError):
        AnswerQuestionDecision.model_validate({
            "type": "answer_question",
            "question": "Q?",
            "answer": "A.",
            "extra": 123,
        })


def test_valid_clarify_decision():
    """Verify clarify decision parses properly."""
    dec = ClarifyDecision(
        question="Did you finish frying or just add the garlic?",
    )
    assert dec.type == "clarify"
    assert "frying" in dec.question


def test_discriminated_union_parsing():
    """Verify polymorphic discriminated union parses valid decision types."""
    dec1 = decision_adapter.validate_python({
        "type": "execute_action",
        "action": "get_current_step",
        "arguments": {},
    })
    assert isinstance(dec1, ExecuteActionDecision)

    dec2 = decision_adapter.validate_python({
        "type": "answer_question",
        "question": "How hot should the oil be?",
        "answer": "Medium-high heat, around 180C.",
    })
    assert isinstance(dec2, AnswerQuestionDecision)

    dec3 = decision_adapter.validate_python({
        "type": "clarify",
        "question": "Which spice did you mean?",
    })
    assert isinstance(dec3, ClarifyDecision)


def test_discriminated_union_rejects_unknown_type():
    """Verify discriminated union rejects unknown decision types."""
    with pytest.raises(ValidationError):
        decision_adapter.validate_python({
            "type": "delete_all",
            "target": "everything",
        })
