from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Union

from sqlalchemy.orm import Session


class AIProvider(ABC):
    @abstractmethod
    async def generate_exercise(
        self,
        *,
        db: Session,
        user_id: str,
        difficulty: int,
        exercise_type: str,
    ) -> Union[dict[str, Any], str]:
        raise NotImplementedError

    @abstractmethod
    async def evaluate_attempt(
        self,
        *,
        exercise_type: str,
        difficulty: int,
        prompt: str,
        expected_answer: str,
        reference_explanation: str,
        user_answer: str,
    ) -> Union[dict[str, Any], str]:
        raise NotImplementedError
