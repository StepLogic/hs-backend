"""Full mocks: restoring module order, and serving a mock module by module."""
from types import SimpleNamespace

from scripts.backfill_mock_modules import plan


def _row(i, prompt, context=None, answer="A"):
    return SimpleNamespace(id=f"q{i}", prompt=prompt, context=context, correct_answer=answer)


def test_plan_maps_each_question_to_its_module_and_position():
    sections = [
        [{"question": "rw one", "passage": "P1", "correct_answer": "A"},
         {"question": "rw two", "passage": "P2", "correct_answer": "B"}],
        [], [{"question": "m one", "correct_answer": "C", "is_math": True}], [], [], [],
    ]
    rows = [_row(1, "m one", None, "C"), _row(2, "rw two", "P2", "B"), _row(3, "rw one", "P1", "A")]
    assert plan(rows, sections) == {"q1": ("math1", 0), "q2": ("rw1", 1), "q3": ("rw1", 0)}


def test_plan_fills_identical_questions_into_separate_slots():
    same = {"question": "dup", "correct_answer": "A"}
    sections = [[], [dict(same)], [], [], [dict(same)], []]
    got = plan([_row(1, "dup"), _row(2, "dup")], sections)
    assert sorted(got.values()) == [("rw2_easy", 0), ("rw2_hard", 0)]


def test_questions_by_source_test_come_back_in_module_order(client, admin_token):
    from app import models
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    for module, pos in [("math2_easy", 0), ("math1", 1), ("math1", 0), ("rw1", 0)]:
        db.add(models.Question(
            subject="math", grade_level=11, question_type="multiple-choice",
            prompt=f"{module}-{pos}", options=["A. 1", "B. 2"], correct_answer="A",
            skill="s", explanation="e", source_test_id="fullmock-9",
            mock_module=module, mock_position=pos,
        ))
    db.add(models.Question(
        subject="math", grade_level=11, question_type="multiple-choice", prompt="other mock",
        options=["A. 1"], correct_answer="A", skill="s", explanation="e", source_test_id="fullmock-8",
    ))
    db.commit(); db.close()

    r = client.get("/api/v1/questions/", params={"source_test_id": "fullmock-9", "limit": 200})
    assert r.status_code == 200
    assert [q["prompt"] for q in r.json()] == ["math1-0", "math1-1", "math2_easy-0", "rw1-0"]
    assert r.json()[0]["mock_module"] == "math1"


def test_combined_file_is_regrouped_per_mock_and_section():
    from scripts.backfill_mock_modules import sections_by_mock
    flat = [
        {"_source_test_id": "fullmock-1", "_section_idx": 2, "question": "a"},
        {"_source_test_id": "fullmock-1", "_section_idx": 0, "question": "b"},
        {"_source_test_id": "fullmock-1", "_section_idx": 2, "question": "c"},
        {"_source_test_id": "ps-words-1", "_section_idx": 0, "question": "not a mock"},
    ]
    got = sections_by_mock(flat)
    assert list(got) == ["fullmock-1"]
    assert [q["question"] for q in got["fullmock-1"][2]] == ["a", "c"]
    assert [q["question"] for q in got["fullmock-1"][0]] == ["b"]
