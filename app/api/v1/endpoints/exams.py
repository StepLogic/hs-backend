import random
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


def _scaled_score(percent_correct: float, exam_type: str) -> int:
    """Approximate linear scaled score. ponytail: real scaling varies by test form."""
    if exam_type == "sat":
        # SAT 200-800 per section, approx 200 + percent * 6
        return min(800, max(200, int(200 + percent_correct * 6)))
    if exam_type == "act":
        # ACT 1-36, approx 1 + percent * 0.35
        return min(36, max(1, int(1 + percent_correct * 0.35)))
    if exam_type == "ap":
        # AP 1-5, approx 1 + percent * 0.04
        return min(5, max(1, int(1 + percent_correct * 0.04)))
    return int(percent_correct)


@router.get("/blueprints", response_model=list[schemas.ExamBlueprintResponse])
def read_blueprints(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[models.ExamBlueprint]:
    return crud.get_exam_blueprints(db, skip=skip, limit=limit)


@router.post("/blueprints", response_model=schemas.ExamBlueprintResponse, status_code=201)
def create_blueprint(
    *, db: Session = Depends(get_db), blueprint_in: schemas.ExamBlueprintCreate
) -> models.ExamBlueprint:
    return crud.create_exam_blueprint(db, blueprint_in)


@router.post("/start", response_model=dict)
def start_exam(
    *,
    db: Session = Depends(get_db),
    student_id: str = Query(...),
    blueprint_id: str = Query(...),
) -> dict:
    blueprint = crud.get_exam_blueprint(db, blueprint_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    # Assemble questions based on blueprint weights
    skills = list(blueprint.skill_weights.keys()) if blueprint.skill_weights else []
    if not skills:
        # Fallback: pick any skills from taxonomy for the subject
        taxonomy = crud.get_skill_taxonomies(db, subject=blueprint.subject.value if blueprint.subject else None)
        skills = [t.skill for t in taxonomy[:5]]

    questions = []
    for skill in skills:
        weight = blueprint.skill_weights.get(skill, 1) if blueprint.skill_weights else 1
        q_list = (
            db.query(models.Question)
            .filter(
                models.Question.subject == (blueprint.subject.value if blueprint.subject else None),
                models.Question.skill == skill,
                models.Question.review_status == models.ReviewStatus.PUBLISHED,
            )
            .limit(weight)
            .all()
        )
        questions.extend(q_list)

    # Trim to blueprint count
    if len(questions) > blueprint.question_count:
        questions = random.sample(questions, blueprint.question_count)

    # Create TestResult
    test_result_in = schemas.TestResultCreate(
        student_id=student_id,
        subject=blueprint.subject or models.Subject.MATH,
        score=0,
        grade_equivalent=0,
        percentile=0,
        correct_count=0,
        total_questions=len(questions),
        skill_breakdown={},
        mastery_level=models.MasteryLevel.BEGINNER,
        exam_type=blueprint.exam_type,
        timed=True,
        time_limit_sec=blueprint.time_limit_sec,
        section=blueprint.section,
    )
    test_result = crud.create_test_result(db, test_result_in)

    deadline = datetime.now(timezone.utc).timestamp() + blueprint.time_limit_sec
    return {
        "result_id": test_result.id,
        "questions": [schemas.QuestionResponse.model_validate(q) for q in questions],
        "deadline_utc": deadline,
        "time_limit_sec": blueprint.time_limit_sec,
    }


@router.post("/{result_id}/submit", response_model=dict)
def submit_exam(
    *,
    db: Session = Depends(get_db),
    result_id: str,
    answers: list[schemas.PracticeAnswer],
    elapsed_sec: int = Body(...),
) -> dict:
    test_result = crud.get_test_result(db, result_id)
    if not test_result:
        raise HTTPException(status_code=404, detail="Test result not found")

    correct_count = sum(1 for a in answers if a.is_correct)
    total = len(answers)
    percent = (correct_count / total) * 100 if total else 0
    score = _scaled_score(percent, test_result.exam_type.value if test_result.exam_type else "")

    # Update test result
    test_result.score = score
    test_result.correct_count = correct_count
    test_result.total_questions = total
    db.commit()

    # Write user answers and update skill mastery
    skill_masteries = []
    for ans in answers:
        ua = schemas.UserAnswerCreate(
            test_result_id=test_result.id,
            question_id=ans.question_id,
            answer=ans.answer,
            is_correct=ans.is_correct,
            time_spent=ans.time_spent,
        )
        crud.create_user_answer(db, ua)

        q = crud.get_question(db, ans.question_id)
        if q:
            from app.srs import score_to_quality, update_mastery
            sm = crud.get_skill_mastery_by_student_skill(
                db, test_result.student_id,
                test_result.subject.value if test_result.subject else "math",
                q.skill,
            )
            if not sm:
                sm = crud.create_or_update_skill_mastery(
                    db,
                    schemas.SkillMasteryCreate(
                        student_id=test_result.student_id,
                        subject=test_result.subject or models.Subject.MATH,
                        skill=q.skill,
                        due_date=datetime.now(timezone.utc).date(),
                    ),
                )
            quality = score_to_quality(ans.is_correct, ans.time_spent, q.difficulty.value if hasattr(q.difficulty, "value") else q.difficulty)
            update_mastery(sm, quality)
            db.commit()
            db.refresh(sm)
            skill_masteries.append(sm)

    return {
        "test_result": schemas.TestResultResponse.model_validate(test_result),
        "section_score": score,
        "scaled_estimate": score,
        "skill_mastery": [schemas.SkillMasteryResponse.model_validate(sm) for sm in skill_masteries],
    }
