from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ExerciseType = Literal["fill_blank"]


class SessionResponse(BaseModel):
    user_id: str


class ExerciseRequest(BaseModel):
    difficulty: int = Field(ge=1, le=3)
    exercise_type: ExerciseType = "fill_blank"


class ExerciseResponse(BaseModel):
    id: str
    exercise_type: ExerciseType
    difficulty: int
    prompt: str


class AttemptRequest(BaseModel):
    exercise_id: str
    user_answer: str = Field(min_length=1, max_length=100)

    @field_validator("user_answer")
    @classmethod
    def normalize_answer(cls, value: str) -> str:
        return value.strip()


class AttemptResponse(BaseModel):
    is_correct: bool
    corrected_answer: str
    explanation: str


class DifficultyProgress(BaseModel):
    attempts: int
    correct_answers: int
    success_rate: float


class RecentAttempt(BaseModel):
    attempt_id: str
    exercise_id: str
    prompt: str
    difficulty: int
    user_answer: str
    is_correct: bool
    corrected_answer: str
    explanation: str
    timestamp: datetime


class ProgressResponse(BaseModel):
    overall_attempts: int
    correct_answers: int
    success_rate: float
    by_difficulty: dict[int, DifficultyProgress]
    recent_attempts: list[RecentAttempt]


class AIGeneratedExercisePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise_type: ExerciseType
    difficulty: int = Field(ge=1, le=3)
    prompt: str = Field(min_length=8, max_length=500)
    corrected_answer: str = Field(min_length=1, max_length=120)
    explanation: str = Field(min_length=5, max_length=300)
    question_bank_id: Optional[str] = None


class AIEvaluationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_correct: bool
    corrected_answer: str = Field(min_length=1, max_length=120)
    explanation: str = Field(min_length=5, max_length=300)
