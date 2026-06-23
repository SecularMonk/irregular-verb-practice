from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import httpx
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.identity import resolve_or_create_user_id
from app.db.models import Attempt, Exercise
from app.db.session import get_db
from app.schemas.contracts import (
    AttemptRequest,
    AttemptResponse,
    ExerciseRequest,
    ExerciseResponse,
    ProgressResponse,
    SessionResponse,
)
from app.services.ai.factory import build_ai_provider
from app.services.ai.stub import StubAIProvider
from app.services.ai.validator import (
    AIValidationError,
    retry_with_validation,
    validate_evaluation_payload,
    validate_generated_payload,
)
from app.services.progress import get_progress_summary

router = APIRouter(prefix="/api", tags=["api"])
logger = logging.getLogger("uvicorn.error")


def _describe_ai_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        try:
            payload = exc.response.json().get("error", {})
            code = payload.get("code") or payload.get("type") or "unknown_error"
            message = payload.get("message") or "No provider message."
            return f"HTTP {status_code} ({code}): {message}"
        except Exception:
            return f"HTTP {status_code}: {exc}"
    return str(exc)


async def _generate_exercise_with_validation(
    *,
    provider,
    db: Session,
    user_id: str,
    difficulty: int,
    exercise_type: str,
    max_retries: int,
):
    return await retry_with_validation(
        max_retries=max_retries,
        operation=lambda: provider.generate_exercise(
            db=db,
            user_id=user_id,
            difficulty=difficulty,
            exercise_type=exercise_type,
        ),
        validator=lambda raw: validate_generated_payload(
            raw,
            requested_difficulty=difficulty,
            requested_exercise_type=exercise_type,
        ),
    )


@router.post("/session", response_model=SessionResponse)
def create_session(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> SessionResponse:
    user_id = resolve_or_create_user_id(request=request, response=response, settings=settings)
    return SessionResponse(user_id=user_id)


@router.post("/exercise", response_model=ExerciseResponse)
async def create_exercise(
    payload: ExerciseRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ExerciseResponse:
    user_id = resolve_or_create_user_id(request=request, response=response, settings=settings)
    provider = build_ai_provider(settings)

    try:
        generated = await _generate_exercise_with_validation(
            provider=provider,
            db=db,
            user_id=user_id,
            difficulty=payload.difficulty,
            exercise_type=payload.exercise_type,
            max_retries=settings.ai_max_retries,
        )
    except (AIValidationError, ValueError, httpx.HTTPError) as exc:
        # ponytail: generation must remain available when upstream LLM fails; fallback is deterministic seed bank.
        logger.warning("Real exercise generation failed; falling back to stub. Reason: %s", _describe_ai_error(exc))
        try:
            generated = await _generate_exercise_with_validation(
                provider=StubAIProvider(),
                db=db,
                user_id=user_id,
                difficulty=payload.difficulty,
                exercise_type=payload.exercise_type,
                max_retries=0,
            )
        except (AIValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to generate a valid exercise: {exc}",
            ) from exc

    exercise = Exercise(
        user_id=user_id,
        exercise_type=generated.exercise_type,
        difficulty=generated.difficulty,
        prompt=generated.prompt,
        correct_answer=generated.corrected_answer,
        reference_explanation=generated.explanation,
        question_bank_id=generated.question_bank_id,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    return ExerciseResponse(
        id=exercise.id,
        exercise_type=exercise.exercise_type,
        difficulty=exercise.difficulty,
        prompt=exercise.prompt,
    )


@router.post("/attempt", response_model=AttemptResponse)
async def submit_attempt(
    payload: AttemptRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AttemptResponse:
    user_id = resolve_or_create_user_id(request=request, response=response, settings=settings)
    exercise = db.execute(
        select(Exercise).where(Exercise.id == payload.exercise_id, Exercise.user_id == user_id)
    ).scalar_one_or_none()
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found for this user.")

    normalized_user_answer = payload.user_answer.strip().lower()
    normalized_expected = exercise.correct_answer.strip().lower()
    fallback_is_correct = normalized_user_answer == normalized_expected
    base_explanation = exercise.reference_explanation.strip()
    if fallback_is_correct:
        fallback_explanation = f"Correct. {base_explanation}"
    else:
        fallback_explanation = (
            f"Incorrect. The expected answer is '{exercise.correct_answer}'. {base_explanation}"
        )

    is_correct = fallback_is_correct
    corrected_answer = exercise.correct_answer
    explanation = fallback_explanation

    try:
        provider = build_ai_provider(settings)
        evaluated = await retry_with_validation(
            max_retries=settings.ai_max_retries,
            operation=lambda: provider.evaluate_attempt(
                exercise_type=exercise.exercise_type,
                difficulty=exercise.difficulty,
                prompt=exercise.prompt,
                expected_answer=exercise.correct_answer,
                reference_explanation=exercise.reference_explanation,
                user_answer=payload.user_answer,
            ),
            validator=lambda raw: validate_evaluation_payload(raw, expected_answer=exercise.correct_answer),
        )
        is_correct = evaluated.is_correct
        corrected_answer = evaluated.corrected_answer
        explanation = evaluated.explanation
    except (AIValidationError, ValueError, httpx.HTTPError) as exc:
        # ponytail: attempt evaluation must never fail user flow; fallback is strict exact match.
        logger.warning("Real attempt evaluation failed; using deterministic fallback. Reason: %s", _describe_ai_error(exc))
        pass

    attempt = Attempt(
        exercise_id=exercise.id,
        user_id=user_id,
        difficulty=exercise.difficulty,
        user_answer=payload.user_answer,
        is_correct=is_correct,
        corrected_answer=corrected_answer,
        explanation=explanation,
    )
    db.add(attempt)
    db.commit()

    return AttemptResponse(
        is_correct=is_correct,
        corrected_answer=corrected_answer,
        explanation=explanation,
    )


@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProgressResponse:
    user_id = resolve_or_create_user_id(request=request, response=response, settings=settings)
    return get_progress_summary(db, user_id)
