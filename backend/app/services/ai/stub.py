from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Exercise, QuestionBank
from app.services.ai.base import AIProvider


class StubAIProvider(AIProvider):
    async def generate_exercise(
        self,
        *,
        db: Session,
        user_id: str,
        difficulty: int,
        exercise_type: str,
    ) -> dict:
        statement = select(QuestionBank).where(
            QuestionBank.exercise_type == exercise_type,
            QuestionBank.difficulty == difficulty,
        ).order_by(QuestionBank.prompt.asc())
        questions = list(db.execute(statement).scalars().all())
        if not questions:
            raise ValueError("No seeded questions found for the selected difficulty.")

        count_stmt = select(func.count(Exercise.id)).where(
            Exercise.user_id == user_id,
            Exercise.difficulty == difficulty,
            Exercise.exercise_type == exercise_type,
        )
        existing_count = db.execute(count_stmt).scalar_one()
        selected = questions[existing_count % len(questions)]

        return {
            "exercise_type": exercise_type,
            "difficulty": difficulty,
            "prompt": selected.prompt,
            "corrected_answer": selected.corrected_answer,
            "explanation": selected.explanation,
            "question_bank_id": selected.id,
        }

    async def evaluate_attempt(
        self,
        *,
        exercise_type: str,
        difficulty: int,
        prompt: str,
        expected_answer: str,
        reference_explanation: str,
        user_answer: str,
    ) -> dict:
        del exercise_type
        del difficulty
        del prompt
        normalized_user_answer = user_answer.strip().lower()
        normalized_expected = expected_answer.strip().lower()
        is_correct = normalized_user_answer == normalized_expected
        if is_correct:
            explanation = f"Correct. {reference_explanation.strip()}"
        else:
            explanation = (
                f"Incorrect. The expected answer is '{expected_answer}'. "
                f"{reference_explanation.strip()}"
            )
        return {
            "is_correct": is_correct,
            "corrected_answer": expected_answer,
            "explanation": explanation,
        }
