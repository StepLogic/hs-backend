from typing import Optional, Any

from sqlalchemy.orm import Session

from app import models, schemas


# ─── Questions ───

def get_question(db: Session, question_id: str) -> Optional[models.Question]:
    return db.query(models.Question).filter(models.Question.id == question_id).first()


def get_questions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    subject: Optional[str] = None,
    grade_level: Optional[int] = None,
) -> list[models.Question]:
    query = db.query(models.Question)
    if subject:
        query = query.filter(models.Question.subject == subject)
    if grade_level is not None:
        query = query.filter(models.Question.grade_level == grade_level)
    return query.offset(skip).limit(limit).all()


def create_question(db: Session, question: schemas.QuestionCreate) -> models.Question:
    db_question = models.Question(**question.model_dump())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def update_question(
    db: Session, question_id: str, question: schemas.QuestionUpdate
) -> Optional[models.Question]:
    db_question = get_question(db, question_id)
    if not db_question:
        return None
    update_data = question.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_question, key, value)
    db.commit()
    db.refresh(db_question)
    return db_question


def delete_question(db: Session, question_id: str) -> bool:
    db_question = get_question(db, question_id)
    if not db_question:
        return False
    db.delete(db_question)
    db.commit()
    return True


# ─── Courses ───

def get_course(db: Session, course_id: str) -> Optional[models.Course]:
    return db.query(models.Course).filter(models.Course.id == course_id).first()


def get_courses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    subject: Optional[str] = None,
) -> list[models.Course]:
    query = db.query(models.Course)
    if subject:
        query = query.filter(models.Course.subject == subject)
    return query.offset(skip).limit(limit).all()


def create_course(db: Session, course: schemas.CourseCreate) -> models.Course:
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def update_course(
    db: Session, course_id: str, course: schemas.CourseUpdate
) -> Optional[models.Course]:
    db_course = get_course(db, course_id)
    if not db_course:
        return None
    update_data = course.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_course, key, value)
    db.commit()
    db.refresh(db_course)
    return db_course


def delete_course(db: Session, course_id: str) -> bool:
    db_course = get_course(db, course_id)
    if not db_course:
        return False
    db.delete(db_course)
    db.commit()
    return True


# ─── Students ───

def get_student(db: Session, student_id: str) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_students(
    db: Session, skip: int = 0, limit: int = 100
) -> list[models.Student]:
    return db.query(models.Student).offset(skip).limit(limit).all()


def create_student(db: Session, student: schemas.StudentCreate) -> models.Student:
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def update_student(
    db: Session, student_id: str, student: schemas.StudentUpdate
) -> Optional[models.Student]:
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    update_data = student.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, student_id: str) -> bool:
    db_student = get_student(db, student_id)
    if not db_student:
        return False
    db.delete(db_student)
    db.commit()
    return True


# ─── Test Results ───

def get_test_result(db: Session, test_result_id: str) -> Optional[models.TestResult]:
    return db.query(models.TestResult).filter(models.TestResult.id == test_result_id).first()


def get_test_results(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[str] = None,
) -> list[models.TestResult]:
    query = db.query(models.TestResult)
    if student_id:
        query = query.filter(models.TestResult.student_id == student_id)
    return query.offset(skip).limit(limit).all()


def create_test_result(
    db: Session, test_result: schemas.TestResultCreate
) -> models.TestResult:
    db_test_result = models.TestResult(**test_result.model_dump())
    db.add(db_test_result)
    db.commit()
    db.refresh(db_test_result)
    return db_test_result


def update_test_result(
    db: Session, test_result_id: str, test_result: schemas.TestResultUpdate
) -> Optional[models.TestResult]:
    db_test_result = get_test_result(db, test_result_id)
    if not db_test_result:
        return None
    update_data = test_result.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_test_result, key, value)
    db.commit()
    db.refresh(db_test_result)
    return db_test_result


def delete_test_result(db: Session, test_result_id: str) -> bool:
    db_test_result = get_test_result(db, test_result_id)
    if not db_test_result:
        return False
    db.delete(db_test_result)
    db.commit()
    return True


# ─── User Answers ───

def get_user_answer(db: Session, user_answer_id: str) -> Optional[models.UserAnswer]:
    return db.query(models.UserAnswer).filter(models.UserAnswer.id == user_answer_id).first()


def get_user_answers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    test_result_id: Optional[str] = None,
) -> list[models.UserAnswer]:
    query = db.query(models.UserAnswer)
    if test_result_id:
        query = query.filter(models.UserAnswer.test_result_id == test_result_id)
    return query.offset(skip).limit(limit).all()


def create_user_answer(
    db: Session, user_answer: schemas.UserAnswerCreate
) -> models.UserAnswer:
    db_user_answer = models.UserAnswer(**user_answer.model_dump())
    db.add(db_user_answer)
    db.commit()
    db.refresh(db_user_answer)
    return db_user_answer


def update_user_answer(
    db: Session, user_answer_id: str, user_answer: schemas.UserAnswerUpdate
) -> Optional[models.UserAnswer]:
    db_user_answer = get_user_answer(db, user_answer_id)
    if not db_user_answer:
        return None
    update_data = user_answer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user_answer, key, value)
    db.commit()
    db.refresh(db_user_answer)
    return db_user_answer


def delete_user_answer(db: Session, user_answer_id: str) -> bool:
    db_user_answer = get_user_answer(db, user_answer_id)
    if not db_user_answer:
        return False
    db.delete(db_user_answer)
    db.commit()
    return True
