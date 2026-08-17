from app.mastery.service import get_mastery, recalculate_mastery, status_for


def test_status_thresholds():
    assert status_for(85) == "mastered"
    assert status_for(80) == "mastered"
    assert status_for(79) == "in_progress"
    assert status_for(50) == "in_progress"
    assert status_for(49) == "needs_reteach"
    assert status_for(0) == "needs_reteach"


def test_recalculate_mastery_upserts(mock_db):
    record = recalculate_mastery(mock_db, "user1", "topic1", 62)
    assert record["mastery"] == 0.62
    assert record["status"] == "in_progress"

    stored = get_mastery(mock_db, "user1", "topic1")
    assert stored["mastery"] == 0.62

    # a later attempt overwrites, rather than averaging with, the earlier one
    recalculate_mastery(mock_db, "user1", "topic1", 90)
    stored = get_mastery(mock_db, "user1", "topic1")
    assert stored["mastery"] == 0.9
    assert stored["status"] == "mastered"


def test_recalculate_mastery_clamps_out_of_range_scores(mock_db):
    record = recalculate_mastery(mock_db, "user1", "topic1", 150)
    assert record["mastery"] == 1.0

    record = recalculate_mastery(mock_db, "user1", "topic2", -20)
    assert record["mastery"] == 0.0


def test_get_mastery_defaults_when_no_attempt_yet(mock_db):
    record = get_mastery(mock_db, "user1", "topic-never-attempted")
    assert record["status"] == "not_started"
    assert record["mastery"] == 0.0
