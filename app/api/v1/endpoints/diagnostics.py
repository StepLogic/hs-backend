import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.post("/start", response_model=dict)
def start_diagnostic(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    student_id: str,
    subject: str,
    grade_level: int = 6,
) -> dict:
    # Fetch questions for the subject, starting at the given grade level
    questions = (
        db.query(models.Question)
        .filter(
            models.Question.subject == subject,
            models.Question.grade_level == grade_level,
            models.Question.review_status == models.ReviewStatus.PUBLISHED,
        )
        .order_by(models.Question.difficulty)
        .limit(20)
        .all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No questions available for this subject/grade")

    question_data = []
    for q in questions:
        question_data.append({
            "id": q.id,
            "prompt": q.prompt,
            "type": q.question_type.value if q.question_type else "multiple-choice",
            "options": q.options,
            "skill": q.skill,
            "difficulty": q.difficulty.value if q.difficulty else "medium",
            "correct_answer": q.correct_answer,
        })

    return {
        "student_id": student_id,
        "subject": subject,
        "questions": question_data,
    }


@router.post("/submit", response_model=schemas.DiagnosticResultResponse)
def submit_diagnostic(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    student_id: str,
    subject: str,
    answers: list[dict],
) -> models.DiagnosticResult:
    correct = sum(1 for a in answers if a.get("is_correct"))
    total = len(answers)
    percent = correct / total if total else 0

    # Map percent to grade-level equivalent (rough heuristic)
    grade_level_equivalent = min(12, max(1, int(percent * 12)))

    # Compute skill gaps
    skill_counts: dict[str, dict] = {}
    for a in answers:
        skill = a.get("skill", "unknown")
        if skill not in skill_counts:
            skill_counts[skill] = {"correct": 0, "total": 0}
        skill_counts[skill]["total"] += 1
        if a.get("is_correct"):
            skill_counts[skill]["correct"] += 1

    skill_gaps = [
        {"skill": skill, "correct": data["correct"], "total": data["total"], "level": "weak" if data["correct"] / data["total"] < 0.6 else "ok"}
        for skill, data in skill_counts.items()
        if data["total"] > 0
    ]

    # Recommend courses based on weak skills
    courses = db.query(models.Course).filter(models.Course.subject == subject).all()
    recommended = []
    weak_skills = {sg["skill"] for sg in skill_gaps if sg["level"] == "weak"}
    for course in courses:
        course_skills = set(course.skills or [])
        if course_skills & weak_skills:
            recommended.append(course.id)

    result = crud.create_diagnostic_result(
        db,
        schemas.DiagnosticResultCreate(
            student_id=student_id,
            subject=models.Subject(subject) if subject in [s.value for s in models.Subject] else models.Subject.MATH,
            grade_level_equivalent=grade_level_equivalent,
            skill_gaps=skill_gaps,
            recommended_courses=recommended,
        ),
    )
    return result
