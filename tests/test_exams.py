import pytest


def test_exam_start_submit(client, admin_token):
    # Create blueprint
    r = client.post("/api/v1/exams/blueprints", json={
        "exam_type": "sat",
        "subject": "math",
        "section": "math",
        "question_count": 2,
        "time_limit_sec": 1800,
        "grade_level": 8,
        "skill_weights": {"algebra": 1, "geometry": 1},
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    blueprint_id = r.json()["id"]

    # Create questions for the exam
    for skill in ["algebra", "geometry"]:
        client.post("/api/v1/questions/", json={
            "subject": "math",
            "grade_level": 8,
            "question_type": "multiple-choice",
            "prompt": f"What is {skill}?",
            "correct_answer": "A",
            "skill": skill,
            "explanation": "Explanation",
            "difficulty": "easy",
            "options": ["A", "B", "C", "D"],
        }, headers={"Authorization": f"Bearer {admin_token}"})

    # Create student
    rs = client.post("/api/v1/students/", json={"name": "Test", "grade_level": 8}, headers={"Authorization": f"Bearer {admin_token}"})
    student_id = rs.json()["id"]

    # Start exam
    r = client.post("/api/v1/exams/start", params={"student_id": student_id, "blueprint_id": blueprint_id})
    if r.status_code != 200:
        print("Start exam response:", r.status_code, r.json())
    assert r.status_code == 200
    result = r.json()
    assert "result_id" in result
    assert len(result["questions"]) > 0
    result_id = result["result_id"]

    # Submit exam
    questions = result["questions"]
    answers = [{"question_id": q["id"], "answer": "A", "is_correct": True, "time_spent": 20} for q in questions]
    r = client.post(f"/api/v1/exams/{result_id}/submit", json={"answers": answers, "elapsed_sec": 120})
    assert r.status_code == 200
    assert "section_score" in r.json()
    score = r.json()["section_score"]
    # SAT scaled score should be in 200-800 range
    assert 200 <= score <= 800
