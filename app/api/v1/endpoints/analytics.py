from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app.api.deps import get_db, require_roles

router = APIRouter()


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    _admin = require_roles("admin"),
) -> dict:
    active_students = db.query(models.Student).count()
    total_questions = db.query(models.Question).count()
    published_questions = (
        db.query(models.Question)
        .filter(models.Question.review_status == models.ReviewStatus.PUBLISHED)
        .count()
    )
    draft_questions = (
        db.query(models.Question)
        .filter(models.Question.review_status == models.ReviewStatus.DRAFT)
        .count()
    )

    # Average mastery per subject
    mastery_avg = (
        db.query(
            models.SkillMastery.subject,
            func.avg(models.SkillMastery.mastery_score).label("avg_score"),
        )
        .group_by(models.SkillMastery.subject)
        .all()
    )

    exam_attempts = db.query(models.TestResult).filter(
        models.TestResult.exam_type.isnot(None)
    ).count()

    return {
        "active_students": active_students,
        "total_questions": total_questions,
        "published_questions": published_questions,
        "draft_questions": draft_questions,
        "average_mastery_per_subject": {
            str(subj): round(avg, 1) for subj, avg in mastery_avg
        },
        "exam_attempts": exam_attempts,
    }
