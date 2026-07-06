import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.post("/courses/{course_id}/assessment/start", response_model=dict)
def start_assessment(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    """Start an adaptive diagnostic for a course. Returns questions sampled per unit tag."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    units = db.query(models.Unit).filter(models.Unit.course_id == course_id).all()
    if not units:
        raise HTTPException(status_code=404, detail="Course has no units")

    # Collect unique tags from unit descriptions (free-form per course)
    unit_tags = list({u.description for u in units if u.description})

    # Sample 2-3 questions per tag
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
                questions.append({
                    "id": q.id,
                    "prompt": q.prompt,
                    "question_type": q.question_type.value if q.question_type else "multiple-choice",
                    "options": q.options,
                    "skill": q.skill,
                    "difficulty": q.difficulty.value if q.difficulty else "medium",
                    "unit_tag": tag,
                })

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for course units")

    return {
        "assessment_id": f"asmt-{course_id}",
        "course_id": course_id,
        "questions": questions,
    }
