from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class QuestionBank(Base):
    __tablename__ = "question_bank"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    exercise_type: Mapped[str] = mapped_column(String(32), nullable=False, default="fill_blank")
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    corrected_answer: Mapped[str] = mapped_column(String(128), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    exercise_type: Mapped[str] = mapped_column(String(32), nullable=False, default="fill_blank")
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(128), nullable=False)
    reference_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    question_bank_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("question_bank.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    attempts: Mapped[list["Attempt"]] = relationship(back_populates="exercise")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    exercise_id: Mapped[str] = mapped_column(String(36), ForeignKey("exercises.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    corrected_answer: Mapped[str] = mapped_column(String(128), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    exercise: Mapped[Exercise] = relationship(back_populates="attempts")
