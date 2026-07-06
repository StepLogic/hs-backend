import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.post(
    "/courses/{course_id}/assessment/start",
    response_model=schemas.AssessmentStartResponse,
)
def start_assessment(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.AssessmentStartResponse:
    """Start an adaptive diagnostic for a course. Returns questions sampled per unit tag."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    units = db.query(models.Unit).filter(models.Unit.course_id == course_id).all()
    if not units:
        raise HTTPException(status_code=404, detail="Course has no units")

    # Collect unique tags from unit descriptions (free-form per course)
    unit_tags = list({u.description for u in units if u.description})

    # Sample up to 3 questions per tag
    questions = []
    for tag in unit_tags:
        tag_questions = (
            db.query(models.Question)
            .filter(
                models.Question.skill == tag,
                models.Question.review_status == models.ReviewStatus.PUBLISHED,
            )
            .limit(10)
            .all()
        )
        sample_size = min(3, len(tag_questions))
        if sample_size > 0:
            sampled = random.sample(tag_questions, sample_size)
            for q in sampled:
                questions.append(
                    schemas.AssessmentQuestion(
                        id=q.id,
                        prompt=q.prompt,
                        question_type=q.question_type.value if q.question_type else "multiple-choice",
                        options=q.options,
                        skill=q.skill,
                        difficulty=q.difficulty.value if q.difficulty else "medium",
                        unit_tag=tag,
                    )
                )

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for course units")

    return schemas.AssessmentStartResponse(
        assessment_id=f"asmt-{course_id}",
        course_id=course_id,
        questions=questions,
    )


@router.post("/courses/{course_id}/assessment/submit", response_model=schemas.AssessmentSubmitResponse)
def submit_assessment(
    course_id: str,
    payload: schemas.AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.AssessmentSubmitResponse:
    """Score assessment answers by tag. Tags with <60% accuracy are weak."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Score each answer against the correct answer in the database
    tag_counts: dict[str, dict] = {}
    for answer in payload.answers:
        tag = answer.unit_tag
        if tag not in tag_counts:
            tag_counts[tag] = {"correct": 0, "total": 0}

        question = db.query(models.Question).filter(models.Question.id == answer.question_id).first()
        is_correct = question and question.correct_answer == answer.answer
        if is_correct:
            tag_counts[tag]["correct"] += 1
        tag_counts[tag]["total"] += 1

    weak_tags = []
    strong_tags = []
    tag_results = []
    total_correct = 0
    total_questions = 0

    for tag, counts in tag_counts.items():
        percent = (counts["correct"] / counts["total"]) * 100 if counts["total"] > 0 else 0
        level = "weak" if percent < 60 else "strong"
        if level == "weak":
            weak_tags.append(tag)
        else:
            strong_tags.append(tag)
        tag_results.append(schemas.TagResult(
            tag=tag,
            correct=counts["correct"],
            total=counts["total"],
            percent=round(percent, 1),
            level=level,
        ))
        total_correct += counts["correct"]
        total_questions += counts["total"]

    return schemas.AssessmentSubmitResponse(
        assessment_id=f"asmt-{course_id}",
        student_id=payload.student_id,
        course_id=course_id,
        weak_tags=weak_tags,
        strong_tags=strong_tags,
        tag_results=tag_results,
        total_correct=total_correct,
        total_questions=total_questions,
    )
