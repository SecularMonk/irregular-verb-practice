from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, Union

from pydantic import ValidationError

from app.schemas.contracts import AIEvaluationPayload, AIGeneratedExercisePayload

T = TypeVar("T")


class AIValidationError(Exception):
    pass


def _coerce_to_dict(raw: Union[dict[str, Any], str]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise AIValidationError("AI response must be a JSON object.")
    return parsed


def validate_generated_payload(
    raw: Union[dict[str, Any], str],
    *,
    requested_difficulty: int,
    requested_exercise_type: str,
) -> AIGeneratedExercisePayload:
    try:
        payload = AIGeneratedExercisePayload.model_validate(_coerce_to_dict(raw))
    except (ValidationError, json.JSONDecodeError) as exc:
        raise AIValidationError(f"Generated payload shape invalid: {exc}") from exc

    if payload.difficulty != requested_difficulty:
        raise AIValidationError("Generated difficulty does not match request.")
    if payload.exercise_type != requested_exercise_type:
        raise AIValidationError("Generated exercise type does not match request.")
    if "___" not in payload.prompt:
        raise AIValidationError("Generated prompt must contain ___ placeholder.")
    return payload


def validate_evaluation_payload(
    raw: Union[dict[str, Any], str],
    *,
    expected_answer: str,
) -> AIEvaluationPayload:
    try:
        payload = AIEvaluationPayload.model_validate(_coerce_to_dict(raw))
    except (ValidationError, json.JSONDecodeError) as exc:
        raise AIValidationError(f"Evaluation payload shape invalid: {exc}") from exc

    if payload.corrected_answer.strip().lower() != expected_answer.strip().lower():
        raise AIValidationError("Evaluation corrected answer does not match stored expected answer.")
    return payload


async def retry_with_validation(
    *,
    max_retries: int,
    operation: Callable[[], Awaitable[Union[dict[str, Any], str]]],
    validator: Callable[[Union[dict[str, Any], str]], T],
) -> T:
    errors: list[str] = []
    total_attempts = max_retries + 1

    for _ in range(total_attempts):
        raw_response = await operation()
        try:
            return validator(raw_response)
        except AIValidationError as exc:
            errors.append(str(exc))

    raise AIValidationError(f"AI response invalid after {total_attempts} attempts: {' | '.join(errors)}")
