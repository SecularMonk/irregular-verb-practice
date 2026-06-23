from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import QuestionBank
from app.db.seed_data import SEED_QUESTIONS
from app.db.session import get_session_local, init_db


def seed_question_bank(db: Session) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    skipped = 0

    for item in SEED_QUESTIONS:
        existing = db.execute(
            select(QuestionBank).where(
                or_(QuestionBank.id == item["id"], QuestionBank.prompt == item["prompt"])
            )
        ).scalar_one_or_none()
        if existing is not None:
            changed = (
                existing.exercise_type != item["exercise_type"]
                or existing.difficulty != item["difficulty"]
                or existing.prompt != item["prompt"]
                or existing.corrected_answer != item["corrected_answer"]
                or existing.explanation != item["explanation"]
            )
            if changed:
                # ponytail: keep existing primary key on legacy rows, but sync all content from deterministic seed.
                existing.exercise_type = item["exercise_type"]
                existing.difficulty = item["difficulty"]
                existing.prompt = item["prompt"]
                existing.corrected_answer = item["corrected_answer"]
                existing.explanation = item["explanation"]
                updated += 1
            else:
                skipped += 1
            continue

        question = QuestionBank(
            id=item["id"],
            exercise_type=item["exercise_type"],
            difficulty=item["difficulty"],
            prompt=item["prompt"],
            corrected_answer=item["corrected_answer"],
            explanation=item["explanation"],
        )
        db.add(question)
        inserted += 1

    db.commit()
    return inserted, updated, skipped


def run_seed() -> int:
    init_db()
    db = get_session_local()()
    try:
        inserted, _, _ = seed_question_bank(db)
        return inserted
    finally:
        db.close()


def run_seed_with_stats() -> tuple[int, int, int]:
    init_db()
    db = get_session_local()()
    try:
        return seed_question_bank(db)
    finally:
        db.close()


def main() -> None:
    inserted, updated, skipped = run_seed_with_stats()
    print(
        "Seed complete. "
        f"Inserted {inserted} questions, updated {updated} questions, skipped {skipped} questions."
    )


if __name__ == "__main__":
    main()
