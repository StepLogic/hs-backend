from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/{student_id}")
def get_transcript(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Access control: owner, parent of owner, teacher, admin
    if current_user.role == models.Role.STUDENT and str(student.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Enrollments with completion %
    enrollments = crud.get_enrollments_by_student(db, student_id)
    enrollment_data = []
    for enr in enrollments:
        course = crud.get_course(db, enr.course_id)
        if not course:
            continue
        units = crud.get_units_by_course(db, enr.course_id)
        total_lessons = 0
        completed_lessons = 0
        for unit in units:
            lessons = crud.get_lessons_by_unit(db, unit.id)
            for lesson in lessons:
                total_lessons += 1
                prog = crud.get_lesson_progress_by_student_lesson(db, student_id, lesson.id)
                if prog and prog.status == models.LessonProgressStatus.COMPLETED:
                    completed_lessons += 1
        completion_pct = int((completed_lessons / total_lessons) * 100) if total_lessons else 0

        # GPA estimate
        letter = "F"
        if completion_pct >= 90:
            letter = "A"
        elif completion_pct >= 80:
            letter = "B"
        elif completion_pct >= 70:
            letter = "C"
        elif completion_pct >= 60:
            letter = "D"

        enrollment_data.append({
            "course_title": course.title,
            "completion_pct": completion_pct,
            "grade": letter,
            "status": enr.status.value,
        })

    # Skill mastery summary per subject
    mastery_rows = crud.get_skill_masteries_by_student(db, student_id)
    subject_summary = {}
    for sm in mastery_rows:
        subj = sm.subject.value
        if subj not in subject_summary:
            subject_summary[subj] = {"skills": 0, "avg_score": 0, "levels": []}
        subject_summary[subj]["skills"] += 1
        subject_summary[subj]["avg_score"] += sm.mastery_score
        subject_summary[subj]["levels"].append(sm.mastery_level.value)

    for subj in subject_summary:
        count = subject_summary[subj]["skills"]
        subject_summary[subj]["avg_score"] = int(subject_summary[subj]["avg_score"] / count) if count else 0

    # Exam results
    test_results = db.query(models.TestResult).filter(
        models.TestResult.student_id == student_id,
        models.TestResult.exam_type.isnot(None),
    ).all()
    exams = []
    for tr in test_results:
        exams.append({
            "exam_type": tr.exam_type.value if tr.exam_type else None,
            "section": tr.section,
            "score": tr.score,
            "total_questions": tr.total_questions,
            "correct_count": tr.correct_count,
            "date": tr.created_at.isoformat() if tr.created_at else None,
        })

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "grade_level": student.grade_level,
        },
        "enrollments": enrollment_data,
        "subject_mastery": subject_summary,
        "exams": exams,
    }
