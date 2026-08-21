from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


def _owned_student(db: Session, student_id: str, current_user: models.User) -> models.Student:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role in (models.Role.STUDENT, models.Role.PARENT):
        if str(student.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to access this student")
    return student


def _with_progress(db: Session, goal: models.CourseGoal) -> schemas.CourseGoalResponse:
    """Two independent lines: per-skill mastery, and the final exam.

    They are reported separately on purpose. A student can fix every weak skill and
    still not have sat the final, or pass the final while a skill is untouched —
    collapsing that into one verdict hides the thing worth acting on.
    """
    out = schemas.CourseGoalResponse.model_validate(goal)

    masteries = {
        m.skill: m.mastery_score
        for m in db.query(models.SkillMastery)
        .filter(models.SkillMastery.student_id == goal.student_id)
        .all()
    }

    skills = []
    for skill in goal.target_skills or []:
        score = masteries.get(skill)
        if score is None:
            status = "not_practiced"
            score = 0
        elif score >= goal.target_mastery:
            status = "met"
        else:
            status = "in_progress"
        skills.append(
            schemas.GoalSkillProgress(
                skill=skill,
                baseline_percent=(goal.baseline or {}).get(skill),
                mastery_score=score,
                target=goal.target_mastery,
                status=status,
            )
        )

    best = (
        db.query(models.FinalExamAttempt)
        .filter(
            models.FinalExamAttempt.student_id == goal.student_id,
            models.FinalExamAttempt.course_id == goal.course_id,
        )
        .order_by(models.FinalExamAttempt.score.desc())
        .first()
    )

    out.skills = skills
    out.skills_total = len(skills)
    out.skills_met = sum(1 for s in skills if s.status == "met")
    out.exam = schemas.GoalExamProgress(
        attempted=best is not None,
        best_score=float(best.score) if best else None,
        target=goal.target_exam_score,
        passed=bool(best and best.score >= goal.target_exam_score),
    )

    # Achieved means both lines are satisfied. Stamped once, then left alone.
    if out.skills_total and out.skills_met == out.skills_total and out.exam.passed:
        if goal.achieved_at is None:
            goal.achieved_at = datetime.utcnow()
            db.commit()
            db.refresh(goal)
        out.achieved_at = goal.achieved_at

    return out


@router.post(
    "/courses/{course_id}/goals",
    response_model=schemas.CourseGoalResponse,
    status_code=201,
)
def set_course_goal(
    course_id: str,
    body: schemas.CourseGoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.CourseGoalResponse:
    """Record what the student committed to after their diagnostic.

    Re-running the diagnostic replaces the goal rather than stacking a second one,
    so the baseline always reflects the most recent honest measurement.
    """
    _owned_student(db, body.student_id, current_user)
    if not db.query(models.Course).filter(models.Course.id == course_id).first():
        raise HTTPException(status_code=404, detail="Course not found")

    goal = (
        db.query(models.CourseGoal)
        .filter(
            models.CourseGoal.student_id == body.student_id,
            models.CourseGoal.course_id == course_id,
        )
        .first()
    )
    if goal is None:
        goal = models.CourseGoal(student_id=body.student_id, course_id=course_id)
        db.add(goal)

    goal.scope = body.scope
    goal.target_skills = body.target_skills
    goal.baseline = body.baseline
    goal.target_mastery = body.target_mastery
    goal.target_exam_score = body.target_exam_score
    goal.achieved_at = None
    db.commit()
    db.refresh(goal)
    return _with_progress(db, goal)


@router.get("/courses/{course_id}/goals", response_model=schemas.CourseGoalResponse)
def get_course_goal(
    course_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.CourseGoalResponse:
    _owned_student(db, student_id, current_user)
    goal = (
        db.query(models.CourseGoal)
        .filter(
            models.CourseGoal.student_id == student_id,
            models.CourseGoal.course_id == course_id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="No goal set for this course")
    return _with_progress(db, goal)
