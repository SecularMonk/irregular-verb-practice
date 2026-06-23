from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Attempt, Exercise
from app.schemas.contracts import DifficultyProgress, ProgressResponse, RecentAttempt


@dataclass
class AttemptSnapshot:
    difficulty: int
    is_correct: bool


def _rate(correct: int, attempts: int) -> float:
    if attempts == 0:
        return 0.0
    return round((correct / attempts) * 100, 2)


def calculate_progress(rows: list[AttemptSnapshot]) -> tuple[int, int, float, dict[int, DifficultyProgress]]:
    total_attempts = len(rows)
    total_correct = sum(1 for row in rows if row.is_correct)
    by_difficulty = {
        1: {"attempts": 0, "correct_answers": 0},
        2: {"attempts": 0, "correct_answers": 0},
        3: {"attempts": 0, "correct_answers": 0},
    }

    for row in rows:
        bucket = by_difficulty.setdefault(row.difficulty, {"attempts": 0, "correct_answers": 0})
        bucket["attempts"] += 1
        if row.is_correct:
            bucket["correct_answers"] += 1

    difficulty_stats = {
        key: DifficultyProgress(
            attempts=value["attempts"],
            correct_answers=value["correct_answers"],
            success_rate=_rate(value["correct_answers"], value["attempts"]),
        )
        for key, value in by_difficulty.items()
    }
    return total_attempts, total_correct, _rate(total_correct, total_attempts), difficulty_stats


def get_progress_summary(db: Session, user_id: str, recent_limit: int = 10) -> ProgressResponse:
    attempt_rows = list(
        db.execute(
            select(Attempt.difficulty, Attempt.is_correct).where(Attempt.user_id == user_id)
        ).all()
    )
    snapshots = [AttemptSnapshot(difficulty=row.difficulty, is_correct=row.is_correct) for row in attempt_rows]
    total_attempts, total_correct, success_rate, by_difficulty = calculate_progress(snapshots)

    recent_rows = list(
        db.execute(
            select(Attempt, Exercise.prompt)
            .join(Exercise, Exercise.id == Attempt.exercise_id)
            .where(Attempt.user_id == user_id)
            .order_by(Attempt.created_at.desc())
            .limit(recent_limit)
        ).all()
    )
    recent_attempts = [
        RecentAttempt(
            attempt_id=attempt.id,
            exercise_id=attempt.exercise_id,
            prompt=prompt,
            difficulty=attempt.difficulty,
            user_answer=attempt.user_answer,
            is_correct=attempt.is_correct,
            corrected_answer=attempt.corrected_answer,
            explanation=attempt.explanation,
            timestamp=attempt.created_at,
        )
        for attempt, prompt in recent_rows
    ]

    return ProgressResponse(
        overall_attempts=total_attempts,
        correct_answers=total_correct,
        success_rate=success_rate,
        by_difficulty=by_difficulty,
        recent_attempts=recent_attempts,
    )
