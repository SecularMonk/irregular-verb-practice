from pathlib import Path

from sqlalchemy import select

from app.core.config import clear_settings_cache
from app.db.models import QuestionBank
from app.db.seed_data import SEED_QUESTIONS
from app.db.seed_questions import run_seed
from app.db.session import get_session_local, reset_engine


def test_seed_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "seed.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    clear_settings_cache()
    reset_engine()

    inserted_first = run_seed()
    inserted_second = run_seed()

    db = get_session_local()()
    try:
        records = db.execute(select(QuestionBank)).scalars().all()
    finally:
        db.close()

    assert inserted_first == len(SEED_QUESTIONS)
    assert inserted_second == 0
    assert len(records) == len(SEED_QUESTIONS)
    assert {record.id for record in records} == {item["id"] for item in SEED_QUESTIONS}

    clear_settings_cache()
    reset_engine()
