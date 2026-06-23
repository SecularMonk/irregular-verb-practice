from app.services.progress import AttemptSnapshot, calculate_progress


def test_calculate_progress_overall_and_by_difficulty() -> None:
    rows = [
        AttemptSnapshot(difficulty=1, is_correct=True),
        AttemptSnapshot(difficulty=1, is_correct=False),
        AttemptSnapshot(difficulty=2, is_correct=True),
        AttemptSnapshot(difficulty=3, is_correct=False),
        AttemptSnapshot(difficulty=3, is_correct=True),
    ]

    total_attempts, total_correct, success_rate, by_difficulty = calculate_progress(rows)

    assert total_attempts == 5
    assert total_correct == 3
    assert success_rate == 60.0

    assert by_difficulty[1].attempts == 2
    assert by_difficulty[1].correct_answers == 1
    assert by_difficulty[1].success_rate == 50.0

    assert by_difficulty[2].attempts == 1
    assert by_difficulty[2].correct_answers == 1
    assert by_difficulty[2].success_rate == 100.0

    assert by_difficulty[3].attempts == 2
    assert by_difficulty[3].correct_answers == 1
    assert by_difficulty[3].success_rate == 50.0
