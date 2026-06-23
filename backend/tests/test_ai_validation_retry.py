import pytest

from app.services.ai.validator import (
    AIValidationError,
    retry_with_validation,
    validate_evaluation_payload,
    validate_generated_payload,
)


@pytest.mark.asyncio
async def test_retry_with_validation_succeeds_after_invalid_json() -> None:
    responses = iter(
        [
            "not-json",
            '{"exercise_type":"fill_blank","difficulty":2,"prompt":"Yesterday I ___ (go) home.","corrected_answer":"went","explanation":"Use went for past simple."}',
        ]
    )

    async def operation():
        return next(responses)

    payload = await retry_with_validation(
        max_retries=2,
        operation=operation,
        validator=lambda raw: validate_generated_payload(
            raw, requested_difficulty=2, requested_exercise_type="fill_blank"
        ),
    )

    assert payload.corrected_answer == "went"


@pytest.mark.asyncio
async def test_retry_with_validation_raises_after_exhaustion() -> None:
    async def operation():
        return "nope"

    with pytest.raises(AIValidationError):
        await retry_with_validation(
            max_retries=1,
            operation=operation,
            validator=lambda raw: validate_generated_payload(
                raw, requested_difficulty=1, requested_exercise_type="fill_blank"
            ),
        )


def test_validate_evaluation_payload_rejects_wrong_corrected_answer() -> None:
    raw = '{"is_correct": false, "corrected_answer": "go", "explanation": "Use past simple."}'

    with pytest.raises(AIValidationError):
        validate_evaluation_payload(raw, expected_answer="went")
