from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


def _get_all_final_exam_questions(db: Session, course_id: str):
    """Return FinalExam rows plus Question rows scoped to this course as full-test questions."""
    final_exam_rows = crud.get_final_exam_questions(db, course_id)
    question_rows = (
        db.query(models.Question)
        .filter(models.Question.course_id == course_id, models.Question.is_full_test == True)
        .all()
    )
    return final_exam_rows + question_rows


@router.post("/{course_id}/final/start", response_model=schemas.FinalExamStartResponse)
def start_final_exam(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.FinalExamStartResponse:
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.certificate_enabled:
        raise HTTPException(status_code=403, detail="This course does not offer certificates")

    questions = _get_all_final_exam_questions(db, course_id)
    if not questions:
        raise HTTPException(status_code=404, detail="No final exam questions found for this course")

    return schemas.FinalExamStartResponse(
        exam_id=f"final-{course_id}",
        course_id=course_id,
        questions=[
            schemas.FinalExamQuestion(
                id=q.id,
                prompt=q.prompt,
                question_type=q.question_type.value if q.question_type else "multiple-choice",
                options=q.options,
                skill=q.skill,
                difficulty=q.difficulty.value if q.difficulty else "medium",
            )
            for q in questions
        ],
    )


@router.post("/{course_id}/final/submit", response_model=schemas.FinalExamSubmitResponse)
def submit_final_exam(
    course_id: str,
    payload: schemas.FinalExamSubmitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.FinalExamSubmitResponse:
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if str(student.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this student")

    questions = _get_all_final_exam_questions(db, course_id)
    question_map = {q.id: q for q in questions}

    total_correct = 0
    for answer in payload.answers:
        q = question_map.get(answer.question_id)
        if q and q.correct_answer == answer.answer:
            total_correct += 1

    total_questions = len(questions)
    score = round((total_correct / total_questions) * 100) if total_questions > 0 else 0
    passed = score >= course.certificate_passing_score

    crud.create_final_exam_attempt(db, payload.student_id, course_id, score, passed)

    return schemas.FinalExamSubmitResponse(
        exam_id=f"final-{course_id}",
        student_id=payload.student_id,
        course_id=course_id,
        total_correct=total_correct,
        total_questions=total_questions,
        score=score,
        passed=passed,
        passing_score=course.certificate_passing_score,
    )
