from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app import models
from app.api.deps import get_db, get_current_user, require_roles

router = APIRouter()


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    _admin = Depends(require_roles("admin")),
) -> dict:
    from app.cache import get as cache_get, set as cache_set
    cache_key = "analytics:overview"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

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

    result = {
        "active_students": active_students,
        "total_questions": total_questions,
        "published_questions": published_questions,
        "draft_questions": draft_questions,
        "average_mastery_per_subject": {
            str(subj): round(avg, 1) for subj, avg in mastery_avg
        },
        "exam_attempts": exam_attempts,
    }
    cache_set(cache_key, result, ttl=60)
    return result


@router.get("/student/{student_id}/strengths")
def student_strengths(
    student_id: str,
    db: Session = Depends(get_db),
    _user = Depends(get_current_user),
) -> dict:
    rows = (
        db.query(models.SkillMastery)
        .filter(models.SkillMastery.student_id == student_id)
        .order_by(models.SkillMastery.subject, models.SkillMastery.mastery_score.desc())
        .all()
    )
    by_subject: dict[str, list] = {}
    for r in rows:
        by_subject.setdefault(r.subject.value, []).append({
            "skill_name": r.skill,
            "mastery_score": r.mastery_score,
            "last_practiced": r.last_practiced.isoformat() if r.last_practiced else None,
        })
    return by_subject


@router.get("/student/{student_id}/progress")
def student_progress(
    student_id: str,
    db: Session = Depends(get_db),
    _user = Depends(get_current_user),
) -> dict:
    since = datetime.utcnow() - timedelta(days=30)

    lp_rows = (
        db.query(
            func.date(models.LessonProgress.last_accessed).label("d"),
            models.LessonProgress.status,
            func.count().label("c"),
        )
        .filter(
            models.LessonProgress.student_id == student_id,
            models.LessonProgress.last_accessed >= since,
        )
        .group_by("d", models.LessonProgress.status)
        .all()
    )
    lp_map: dict[str, dict] = {}
    for d, status, c in lp_rows:
        key = str(status.value) if hasattr(status, "value") else str(status)
        lp_map.setdefault(str(d), {"date": str(d), "completed": 0, "in_progress": 0})[key] = c

    tr_rows = (
        db.query(
            func.date(models.TestResult.created_at).label("d"),
            models.TestResult.score,
            models.TestResult.exam_type,
        )
        .filter(
            models.TestResult.student_id == student_id,
            models.TestResult.created_at >= since,
        )
        .order_by(models.TestResult.created_at.asc())
        .all()
    )
    test_scores = [
        {
            "date": str(d),
            "score": score,
            "exam_type": str(et.value) if et and hasattr(et, "value") else (str(et) if et else None),
        }
        for d, score, et in tr_rows
    ]

    return {
        "lesson_progress": list(lp_map.values()),
        "test_scores": test_scores,
    }
