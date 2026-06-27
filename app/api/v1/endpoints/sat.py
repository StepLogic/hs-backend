"""SAT Math Prep course endpoints: assessment + adaptive lesson curation."""
import random
from collections import defaultdict
from datetime import date, datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user
from app.srs import score_to_quality, update_mastery

router = APIRouter()

# SAT math skills in priority order
SAT_SKILLS = [
    "linear-equations", "systems-of-equations", "inequalities", "linear-functions",
    "ratios-rates", "percentages", "proportions", "data-interpretation",
    "quadratics", "polynomials", "exponentials", "nonlinear-functions",
    "area-volume", "angles-lines-triangles", "right-triangles", "trigonometry",
    "expression-manipulation", "complex-numbers", "structure", "isolating-quantities",
]

SAT_AREAS = {
    "algebra": ["linear-equations", "systems-of-equations", "inequalities", "linear-functions"],
    "problem-solving-data-analysis": ["ratios-rates", "percentages", "proportions", "data-interpretation"],
    "advanced-math": ["quadratics", "polynomials", "exponentials", "nonlinear-functions"],
    "geometry-trigonometry": ["area-volume", "angles-lines-triangles", "right-triangles", "trigonometry"],
    "passport-advanced-math": ["expression-manipulation", "complex-numbers", "structure", "isolating-quantities"],
}

# Reverse mapping: skill → area
SKILL_TO_AREA = {}
for area, skills in SAT_AREAS.items():
    for sk in skills:
        SKILL_TO_AREA[sk] = area


def _get_sat_course(db: Session) -> models.Course:
    course = db.query(models.Course).filter(models.Course.title == "SAT Math Prep").first()
    if not course:
        raise HTTPException(status_code=404, detail="SAT Math Prep course not found. Run seed_sat_course.py first.")
    return course


@router.get("/assessment", response_model=dict)
def get_assessment(
    db: Session = Depends(get_db),
) -> dict:
    """Return 20 assessment questions spanning all SAT math areas.

    Selects 4 published questions per skill area (one per sub-skill),
    shuffled for variety.
    """
    course = _get_sat_course(db)

    questions = []
    for area, skills in SAT_AREAS.items():
        for skill in skills:
            q = (
                db.query(models.Question)
                .filter(
                    models.Question.subject == models.Subject.MATH,
                    models.Question.skill == skill,
                    models.Question.review_status == models.ReviewStatus.PUBLISHED,
                    models.Question.grade_level == 12,
                )
                .first()
            )
            if q:
                questions.append(q)

    # Shuffle question order (not skill coverage)
    random.shuffle(questions)

    return {
        "course_id": course.id,
        "question_count": len(questions),
        "questions": [schemas.QuestionResponse.model_validate(q) for q in questions],
    }


@router.post("/assessment/submit", response_model=dict)
def submit_assessment(
    *,
    db: Session = Depends(get_db),
    student_id: str = Query(...),
    answers: list[schemas.PracticeAnswer] = Body(...),
) -> dict:
    """Submit assessment answers, compute per-skill scores, and return curated lesson path.

    1. Records each answer + updates SkillMastery via SRS
    2. Computes per-area and per-skill accuracy
    3. Creates enrollment in SAT Math Prep course
    4. Returns curated lesson order: weakest skills first
    """
    course = _get_sat_course(db)

    if not answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    # Create a TestResult to link answers to (UserAnswer requires test_result_id)
    test_result = crud.create_test_result(db, schemas.TestResultCreate(
        student_id=student_id,
        subject=models.Subject.MATH,
        score=0,
        grade_equivalent=0,
        percentile=0,
        correct_count=0,
        total_questions=len(answers),
        skill_breakdown={},
        mastery_level=models.MasteryLevel.BEGINNER,
        exam_type=models.ExamType.SAT,
        timed=False,
    ))

    # Process answers
    correct_count = 0
    skill_scores: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})

    for ans in answers:
        q = crud.get_question(db, ans.question_id)
        if not q:
            continue

        # Record answer
        ua = schemas.UserAnswerCreate(
            test_result_id=test_result.id,
            question_id=ans.question_id,
            answer=ans.answer,
            is_correct=ans.is_correct,
            time_spent=ans.time_spent,
        )
        crud.create_user_answer(db, ua)

        if ans.is_correct:
            correct_count += 1
            skill_scores[q.skill]["correct"] += 1
        skill_scores[q.skill]["total"] += 1

        # Update SkillMastery via SRS
        sm = crud.get_skill_mastery_by_student_skill(db, student_id, "math", q.skill)
        if not sm:
            sm = crud.create_or_update_skill_mastery(
                db,
                schemas.SkillMasteryCreate(
                    student_id=student_id,
                    subject=models.Subject.MATH,
                    skill=q.skill,
                    due_date=date.today(),
                ),
            )
        quality = score_to_quality(
            ans.is_correct,
            ans.time_spent,
            q.difficulty.value if hasattr(q.difficulty, "value") else q.difficulty,
        )
        update_mastery(sm, quality)
        db.commit()
        db.refresh(sm)

    # Update test result with final score
    test_result.score = correct_count
    test_result.correct_count = correct_count
    db.commit()

    # Compute per-area scores
    area_scores: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
    for skill, scores in skill_scores.items():
        area = SKILL_TO_AREA.get(skill, "unknown")
        area_scores[area]["correct"] += scores["correct"]
        area_scores[area]["total"] += scores["total"]

    # Determine weakest skills (sorted by accuracy ascending)
    skill_results = []
    for skill, scores in skill_scores.items():
        pct = (scores["correct"] / scores["total"] * 100) if scores["total"] else 0
        skill_results.append({
            "skill": skill,
            "area": SKILL_TO_AREA.get(skill, "unknown"),
            "correct": scores["correct"],
            "total": scores["total"],
            "percent": round(pct, 1),
        })
    skill_results.sort(key=lambda x: x["percent"])

    # Build curated lesson path: weakest skills first
    all_lessons = (
        db.query(models.Lesson)
        .join(models.Unit)
        .filter(models.Unit.course_id == course.id)
        .order_by(models.Lesson.order_index)
        .all()
    )

    # Sort lessons by the mastery score of their primary skill (weakest first)
    lesson_mastery = {}
    for lesson in all_lessons:
        primary_skill = lesson.skills[0] if lesson.skills else None
        if primary_skill:
            sm = crud.get_skill_mastery_by_student_skill(db, student_id, "math", primary_skill)
            lesson_mastery[lesson.id] = sm.mastery_score if sm else 0
        else:
            lesson_mastery[lesson.id] = 50

    # Sort: weakest mastery first, then by original order for ties
    curated_lessons = sorted(all_lessons, key=lambda l: (lesson_mastery[l.id], l.order_index))

    curated = []
    for lesson in curated_lessons:
        unit = lesson.unit
        curated.append({
            "lesson_id": lesson.id,
            "title": lesson.title,
            "slug": lesson.slug,
            "unit_title": unit.title,
            "skills": lesson.skills,
            "mastery_score": lesson_mastery[lesson.id],
            "difficulty": lesson.difficulty.value if hasattr(lesson.difficulty, "value") else lesson.difficulty,
        })

    # Create enrollment if not exists
    existing_enrollment = (
        db.query(models.Enrollment)
        .filter(
            models.Enrollment.student_id == student_id,
            models.Enrollment.course_id == course.id,
        )
        .first()
    )
    if not existing_enrollment:
        db.add(models.Enrollment(
            student_id=student_id,
            course_id=course.id,
            status=models.EnrollmentStatus.ACTIVE,
        ))
        db.commit()

    total = len(answers)
    overall_percent = round(correct_count / total * 100, 1) if total else 0

    return {
        "course_id": course.id,
        "total_questions": total,
        "correct_count": correct_count,
        "overall_percent": overall_percent,
        "area_scores": {
            area: {
                "correct": s["correct"],
                "total": s["total"],
                "percent": round(s["correct"] / s["total"] * 100, 1) if s["total"] else 0,
            }
            for area, s in sorted(area_scores.items(), key=lambda x: x[1]["correct"] / x[1]["total"] if x[1]["total"] else 0)
        },
        "skill_results": skill_results,
        "curated_lessons": curated,
    }


@router.get("/{course_id}/curated/{student_id}", response_model=dict)
def get_curated_path(
    course_id: str,
    student_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Return curated learning path for a student, sorted by weakest skills first.

    Uses current SkillMastery scores to order lessons. Lessons with lower mastery
    appear first. Does not respect prerequisites — this is the adaptive order.
    """
    all_lessons = (
        db.query(models.Lesson)
        .join(models.Unit)
        .filter(models.Unit.course_id == course_id)
        .order_by(models.Lesson.order_index)
        .all()
    )

    if not all_lessons:
        raise HTTPException(status_code=404, detail="No lessons found for this course")

    # Get mastery scores
    curated = []
    for lesson in all_lessons:
        primary_skill = lesson.skills[0] if lesson.skills else None
        mastery = 0
        if primary_skill:
            sm = crud.get_skill_mastery_by_student_skill(db, student_id, "math", primary_skill)
            mastery = sm.mastery_score if sm else 0

        progress = crud.get_lesson_progress_by_student_lesson(db, student_id, lesson.id)
        curated.append({
            "lesson_id": lesson.id,
            "title": lesson.title,
            "slug": lesson.slug,
            "unit_title": lesson.unit.title,
            "skills": lesson.skills,
            "mastery_score": mastery,
            "difficulty": lesson.difficulty.value if hasattr(lesson.difficulty, "value") else lesson.difficulty,
            "status": progress.status.value if progress else "not_started",
        })

    # Sort: weakest mastery first, then not-started before in-progress, then by order
    curated.sort(key=lambda x: (x["mastery_score"], 0 if x["status"] == "not_started" else 1))

    return {
        "course_id": course_id,
        "student_id": student_id,
        "curated_lessons": curated,
    }