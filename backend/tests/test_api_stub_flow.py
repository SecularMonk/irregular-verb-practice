from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import clear_settings_cache
from app.db.models import Exercise
from app.db.seed_questions import run_seed
from app.db.session import get_session_local, reset_engine
from app.services.ai.stub import StubAIProvider


def _make_client(tmp_path: Path, monkeypatch, *, db_name: str, with_api_key: bool) -> TestClient:
    db_path = tmp_path / db_name
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    if with_api_key:
        monkeypatch.setenv("LLM_API_KEY", "test-key")
    else:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
    clear_settings_cache()
    reset_engine()
    run_seed()

    from app.main import app

    return TestClient(app)


def test_stub_mode_api_flow(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch, db_name="stub_flow.db", with_api_key=False)

    assert client.post("/api/session").status_code == 200

    exercise_resp = client.post("/api/exercise", json={"difficulty": 1, "exercise_type": "fill_blank"})
    assert exercise_resp.status_code == 200
    exercise = exercise_resp.json()
    assert "___" in exercise["prompt"]
    assert "expected_answer" not in exercise
    assert "corrected_answer" not in exercise

    db = get_session_local()()
    try:
        expected_answer = db.execute(
            select(Exercise.correct_answer).where(Exercise.id == exercise["id"])
        ).scalar_one()
    finally:
        db.close()

    attempt_resp = client.post(
        "/api/attempt",
        json={"exercise_id": exercise["id"], "user_answer": expected_answer},
    )
    assert attempt_resp.status_code == 200
    assert attempt_resp.json()["is_correct"] is True

    progress = client.get("/api/progress").json()
    assert progress["overall_attempts"] == 1
    assert progress["correct_answers"] == 1
    assert len(progress["recent_attempts"]) == 1

    clear_settings_cache()
    reset_engine()


def test_exercise_generation_falls_back_on_real_provider_http_error(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch, db_name="fallback_flow.db", with_api_key=False)

    class BrokenGenerateProvider:
        async def generate_exercise(self, **kwargs):
            raise httpx.ConnectError("simulated upstream failure")

        async def evaluate_attempt(self, **kwargs):
            raise ValueError("unused in this test")

    monkeypatch.setattr("app.api.routes.build_ai_provider", lambda settings: BrokenGenerateProvider())

    assert client.post("/api/session").status_code == 200

    exercise_resp = client.post("/api/exercise", json={"difficulty": 2, "exercise_type": "fill_blank"})
    assert exercise_resp.status_code == 200
    payload = exercise_resp.json()
    assert payload["exercise_type"] == "fill_blank"
    assert payload["difficulty"] == 2
    assert "___" in payload["prompt"]

    clear_settings_cache()
    reset_engine()


def test_attempt_evaluation_falls_back_when_provider_fails(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch, db_name="eval_fallback.db", with_api_key=False)

    class StubGenerateBrokenEvaluate(StubAIProvider):
        async def evaluate_attempt(self, **kwargs):
            raise ValueError("simulated evaluation failure")

    monkeypatch.setattr("app.api.routes.build_ai_provider", lambda settings: StubGenerateBrokenEvaluate())

    assert client.post("/api/session").status_code == 200

    exercise = client.post("/api/exercise", json={"difficulty": 1, "exercise_type": "fill_blank"}).json()
    assert "___" in exercise["prompt"]

    attempt_payload = client.post(
        "/api/attempt",
        json={"exercise_id": exercise["id"], "user_answer": "definitely-wrong"},
    ).json()
    assert attempt_payload["is_correct"] is False
    assert attempt_payload["corrected_answer"]
    assert attempt_payload["explanation"]

    progress = client.get("/api/progress").json()
    assert progress["overall_attempts"] == 1
    assert progress["correct_answers"] == 0
    assert "1" in progress["by_difficulty"]
    assert len(progress["recent_attempts"]) == 1

    clear_settings_cache()
    reset_engine()
