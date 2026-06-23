from __future__ import annotations

import logging
import ssl
from typing import Any

import certifi
import httpx
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.ai.base import AIProvider


class OpenAIMessage(BaseModel):
    content: str


class OpenAIChoice(BaseModel):
    message: OpenAIMessage


class OpenAIChatCompletionResponse(BaseModel):
    choices: list[OpenAIChoice] = Field(min_length=1)


class RealAIProvider(AIProvider):
    def __init__(self, settings: Settings):
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY is required for real AI mode.")
        self.settings = settings
        self.logger = logging.getLogger("app.ai.real")

    async def generate_exercise(
        self,
        *,
        db: Session,
        user_id: str,
        difficulty: int,
        exercise_type: str,
    ) -> str:
        del db
        del user_id
        self.logger.info("Generating exercise with real AI provider.")
        system_prompt = (
            "You generate English irregular verb exercises. "
            "Return only JSON with keys: exercise_type, difficulty, prompt, corrected_answer, explanation."
        )
        user_prompt = (
            f"Create one {exercise_type} exercise with difficulty {difficulty}. "
            "Prompt must include exactly one blank represented by ___ and include the base verb in parentheses."
        )
        return await self._chat_json(system_prompt=system_prompt, user_prompt=user_prompt)

    async def evaluate_attempt(
        self,
        *,
        exercise_type: str,
        difficulty: int,
        prompt: str,
        expected_answer: str,
        reference_explanation: str,
        user_answer: str,
    ) -> str:
        system_prompt = (
            "You evaluate English irregular verb answers. "
            "Return only JSON with keys: is_correct, corrected_answer, explanation."
        )
        user_prompt = (
            "Evaluate this user answer.\n"
            f"Exercise type: {exercise_type}\n"
            f"Difficulty: {difficulty}\n"
            f"Prompt: {prompt}\n"
            f"Expected answer: {expected_answer}\n"
            f"Reference explanation: {reference_explanation}\n"
            f"User answer: {user_answer}\n"
            "Mark is_correct true only if the user answer exactly fits the blank for this exercise. "
            "Always return corrected_answer as the best correct form for the blank."
        )
        return await self._chat_json(system_prompt=system_prompt, user_prompt=user_prompt)

    async def _chat_json(self, *, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(cafile=certifi.where())

        async with httpx.AsyncClient(timeout=30.0, verify=ssl_context) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            raw_data = response.json()

        try:
            parsed = OpenAIChatCompletionResponse.model_validate(raw_data)
        except ValidationError as exc:
            raise ValueError(f"LLM envelope validation failed: {exc}") from exc

        return parsed.choices[0].message.content
