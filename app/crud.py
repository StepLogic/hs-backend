from typing import Optional, Any
from datetime import date

from sqlalchemy.orm import Session

from app import models, schemas


# ─── Users ───

def get_user(db: Session, user_id: str) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate, password_hash: str) -> models.User:
    db_user = models.User(email=user.email, password_hash=password_hash, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user



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


# ─── SkillTaxonomy ───

def get_skill_taxonomy(db: Session, skill_id: str) -> models.SkillTaxonomy | None:
    return db.query(models.SkillTaxonomy).filter(models.SkillTaxonomy.id == skill_id).first()


def get_skill_taxonomies(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    subject: str | None = None,
) -> list[models.SkillTaxonomy]:
    query = db.query(models.SkillTaxonomy)
    if subject is not None:
        query = query.filter(models.SkillTaxonomy.subject == subject)
    return query.offset(skip).limit(limit).all()


def create_skill_taxonomy(
    db: Session, skill: schemas.SkillTaxonomyCreate
) -> models.SkillTaxonomy:
    db_skill = models.SkillTaxonomy(**skill.model_dump())
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill


def delete_skill_taxonomy(db: Session, skill_id: str) -> bool:
    db_skill = get_skill_taxonomy(db, skill_id)
    if not db_skill:
        return False
    db.delete(db_skill)
    db.commit()
    return True


# ─── Units ───

def get_unit(db: Session, unit_id: str) -> models.Unit | None:
    return db.query(models.Unit).filter(models.Unit.id == unit_id).first()


def get_units_by_course(db: Session, course_id: str) -> list[models.Unit]:
    return (
        db.query(models.Unit)
        .filter(models.Unit.course_id == course_id)
        .order_by(models.Unit.order_index)
        .all()
    )


def create_unit(db: Session, unit: schemas.UnitCreate) -> models.Unit:
    db_unit = models.Unit(**unit.model_dump())
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit


def update_unit(db: Session, unit_id: str, unit: schemas.UnitUpdate) -> models.Unit | None:
    db_unit = get_unit(db, unit_id)
    if not db_unit:
        return None
    for key, value in unit.model_dump(exclude_unset=True).items():
        setattr(db_unit, key, value)
    db.commit()
    db.refresh(db_unit)
    return db_unit


def delete_unit(db: Session, unit_id: str) -> bool:
    db_unit = get_unit(db, unit_id)
    if not db_unit:
        return False
    db.delete(db_unit)
    db.commit()
    return True


# ─── Lessons ───

def get_lesson(db: Session, lesson_id: str) -> models.Lesson | None:
    return db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()


def get_lessons_by_unit(db: Session, unit_id: str) -> list[models.Lesson]:
    return (
        db.query(models.Lesson)
        .filter(models.Lesson.unit_id == unit_id)
        .order_by(models.Lesson.order_index)
        .all()
    )


def create_lesson(db: Session, lesson: schemas.LessonCreate) -> models.Lesson:
    db_lesson = models.Lesson(**lesson.model_dump())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def update_lesson(db: Session, lesson_id: str, lesson: schemas.LessonUpdate) -> models.Lesson | None:
    db_lesson = get_lesson(db, lesson_id)
    if not db_lesson:
        return None
    for key, value in lesson.model_dump(exclude_unset=True).items():
        setattr(db_lesson, key, value)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def delete_lesson(db: Session, lesson_id: str) -> bool:
    db_lesson = get_lesson(db, lesson_id)
    if not db_lesson:
        return False
    db.delete(db_lesson)
    db.commit()
    return True


# ─── Enrollments ───

def get_enrollment(db: Session, enrollment_id: str) -> models.Enrollment | None:
    return db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()


def get_enrollments_by_student(db: Session, student_id: str) -> list[models.Enrollment]:
    return db.query(models.Enrollment).filter(models.Enrollment.student_id == student_id).all()


def create_enrollment(db: Session, enrollment: schemas.EnrollmentCreate) -> models.Enrollment:
    db_enrollment = models.Enrollment(**enrollment.model_dump())
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment


def update_enrollment(
    db: Session, enrollment_id: str, enrollment: schemas.EnrollmentUpdate
) -> models.Enrollment | None:
    db_enrollment = get_enrollment(db, enrollment_id)
    if not db_enrollment:
        return None
    for key, value in enrollment.model_dump(exclude_unset=True).items():
        setattr(db_enrollment, key, value)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment


# ─── LessonProgress ───

def get_lesson_progress(db: Session, progress_id: str) -> models.LessonProgress | None:
    return db.query(models.LessonProgress).filter(models.LessonProgress.id == progress_id).first()


def get_lesson_progress_by_student_lesson(
    db: Session, student_id: str, lesson_id: str
) -> models.LessonProgress | None:
    return (
        db.query(models.LessonProgress)
        .filter(
            models.LessonProgress.student_id == student_id,
            models.LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )


def create_or_update_lesson_progress(
    db: Session, progress: schemas.LessonProgressCreate
) -> models.LessonProgress:
    existing = get_lesson_progress_by_student_lesson(db, progress.student_id, progress.lesson_id)
    if existing:
        for key, value in progress.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    db_progress = models.LessonProgress(**progress.model_dump())
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress


# ─── SkillMastery ───

def get_skill_mastery(db: Session, mastery_id: str) -> models.SkillMastery | None:
    return db.query(models.SkillMastery).filter(models.SkillMastery.id == mastery_id).first()


def get_skill_mastery_by_student_skill(
    db: Session, student_id: str, subject: str, skill: str
) -> models.SkillMastery | None:
    return (
        db.query(models.SkillMastery)
        .filter(
            models.SkillMastery.student_id == student_id,
            models.SkillMastery.subject == subject,
            models.SkillMastery.skill == skill,
        )
        .first()
    )


def get_skill_masteries_by_student(
    db: Session, student_id: str, subject: str | None = None
) -> list[models.SkillMastery]:
    query = db.query(models.SkillMastery).filter(models.SkillMastery.student_id == student_id)
    if subject is not None:
        query = query.filter(models.SkillMastery.subject == subject)
    return query.all()


def create_or_update_skill_mastery(
    db: Session, mastery: schemas.SkillMasteryCreate
) -> models.SkillMastery:
    existing = get_skill_mastery_by_student_skill(db, mastery.student_id, mastery.subject.value if hasattr(mastery.subject, "value") else mastery.subject, mastery.skill)
    if existing:
        for key, value in mastery.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    db_mastery = models.SkillMastery(**mastery.model_dump())
    db.add(db_mastery)
    db.commit()
    db.refresh(db_mastery)
    return db_mastery


# ─── UserProfile ───

def get_user_profile(db: Session, user_id: str) -> models.UserProfile | None:
    return db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()


def create_user_profile(db: Session, profile: schemas.UserProfileCreate) -> models.UserProfile:
    db_profile = models.UserProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_user_profile(
    db: Session, user_id: str, profile: schemas.UserProfileUpdate
) -> models.UserProfile | None:
    db_profile = get_user_profile(db, user_id)
    if not db_profile:
        return None
    for key, value in profile.model_dump(exclude_unset=True).items():
        setattr(db_profile, key, value)
    db.commit()
    db.refresh(db_profile)
    return db_profile


# ─── ExamBlueprint ───

def get_exam_blueprint(db: Session, blueprint_id: str) -> models.ExamBlueprint | None:
    return db.query(models.ExamBlueprint).filter(models.ExamBlueprint.id == blueprint_id).first()


def get_exam_blueprints(db: Session, skip: int = 0, limit: int = 100) -> list[models.ExamBlueprint]:
    return db.query(models.ExamBlueprint).offset(skip).limit(limit).all()


def create_exam_blueprint(db: Session, blueprint: schemas.ExamBlueprintCreate) -> models.ExamBlueprint:
    db_bp = models.ExamBlueprint(**blueprint.model_dump())
    db.add(db_bp)
    db.commit()
    db.refresh(db_bp)
    return db_bp


def update_exam_blueprint(
    db: Session, blueprint_id: str, blueprint: schemas.ExamBlueprintUpdate
) -> models.ExamBlueprint | None:
    db_bp = get_exam_blueprint(db, blueprint_id)
    if not db_bp:
        return None
    for key, value in blueprint.model_dump(exclude_unset=True).items():
        setattr(db_bp, key, value)
    db.commit()
    db.refresh(db_bp)
    return db_bp


def delete_exam_blueprint(db: Session, blueprint_id: str) -> bool:
    db_bp = get_exam_blueprint(db, blueprint_id)
    if not db_bp:
        return False
    db.delete(db_bp)
    db.commit()
    return True


# ─── LiveSession ───

def get_live_session(db: Session, session_id: str) -> models.LiveSession | None:
    return db.query(models.LiveSession).filter(models.LiveSession.id == session_id).first()


def get_live_sessions(
    db: Session, skip: int = 0, limit: int = 100, course_id: str | None = None, status: str | None = None
) -> list[models.LiveSession]:
    query = db.query(models.LiveSession)
    if course_id:
        query = query.filter(models.LiveSession.course_id == course_id)
    if status:
        query = query.filter(models.LiveSession.status == status)
    return query.offset(skip).limit(limit).all()


def create_live_session(db: Session, session: schemas.LiveSessionCreate) -> models.LiveSession:
    db_session = models.LiveSession(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_live_session(
    db: Session, session_id: str, session: schemas.LiveSessionUpdate
) -> models.LiveSession | None:
    db_session = get_live_session(db, session_id)
    if not db_session:
        return None
    for key, value in session.model_dump(exclude_unset=True).items():
        setattr(db_session, key, value)
    db.commit()
    db.refresh(db_session)
    return db_session


def delete_live_session(db: Session, session_id: str) -> bool:
    db_session = get_live_session(db, session_id)
    if not db_session:
        return False
    db.delete(db_session)
    db.commit()
    return True


# ─── ChatSession ───

def get_chat_session(db: Session, session_id: str) -> models.ChatSession | None:
    return db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()


def get_chat_sessions_by_student(db: Session, student_id: str) -> list[models.ChatSession]:
    return db.query(models.ChatSession).filter(models.ChatSession.student_id == student_id).all()


def create_chat_session(db: Session, session: schemas.ChatSessionCreate) -> models.ChatSession:
    db_session = models.ChatSession(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


# ─── ChatMessage ───

def create_chat_message(db: Session, session_id: str, role: str, content: str) -> models.ChatMessage:
    db_msg = models.ChatMessage(session_id=session_id, role=role, content=content)
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg


def get_chat_messages(db: Session, session_id: str) -> list[models.ChatMessage]:
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at)
        .all()
    )


# ─── WritingSubmission ───

def get_writing_submission(db: Session, submission_id: str) -> models.WritingSubmission | None:
    return db.query(models.WritingSubmission).filter(models.WritingSubmission.id == submission_id).first()


def get_writing_submissions_by_student(db: Session, student_id: str) -> list[models.WritingSubmission]:
    return db.query(models.WritingSubmission).filter(models.WritingSubmission.student_id == student_id).all()


def create_writing_submission(db: Session, submission: schemas.WritingSubmissionCreate) -> models.WritingSubmission:
    db_sub = models.WritingSubmission(**submission.model_dump())
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub


def update_writing_submission(
    db: Session, submission_id: str, submission: schemas.WritingSubmissionUpdate
) -> models.WritingSubmission | None:
    db_sub = get_writing_submission(db, submission_id)
    if not db_sub:
        return None
    for key, value in submission.model_dump(exclude_unset=True).items():
        setattr(db_sub, key, value)
    db.commit()
    db.refresh(db_sub)
    return db_sub


# ─── DiagnosticResult ───

def get_diagnostic_result(db: Session, result_id: str) -> models.DiagnosticResult | None:
    return db.query(models.DiagnosticResult).filter(models.DiagnosticResult.id == result_id).first()


def get_diagnostic_results_by_student(db: Session, student_id: str) -> list[models.DiagnosticResult]:
    return db.query(models.DiagnosticResult).filter(models.DiagnosticResult.student_id == student_id).all()


def create_diagnostic_result(db: Session, result: schemas.DiagnosticResultCreate) -> models.DiagnosticResult:
    db_result = models.DiagnosticResult(**result.model_dump())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


# ─── College ───

def get_college(db: Session, college_id: str) -> models.College | None:
    return db.query(models.College).filter(models.College.id == college_id).first()


def search_colleges(
    db: Session,
    q: Optional[str] = None,
    sat_min: Optional[int] = None,
    sat_max: Optional[int] = None,
    major: Optional[str] = None,
    tags: Optional[list[str]] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[models.College]:
    query = db.query(models.College)
    if q:
        query = query.filter(
            (models.College.name.ilike(f"%{q}%")) | (models.College.location.ilike(f"%{q}%"))
        )
    if sat_min is not None:
        query = query.filter(models.College.avg_sat >= sat_min)
    if sat_max is not None:
        query = query.filter(models.College.avg_sat <= sat_max)
    if major:
        query = query.filter(models.College.majors.like(f'%"{major}"%'))
    if tags:
        for tag in tags:
            query = query.filter(models.College.tags.like(f'%"{tag}"%'))
    return query.offset(skip).limit(limit).all()


def create_college(db: Session, college: schemas.CollegeCreate) -> models.College:
    db_college = models.College(**college.model_dump())
    db.add(db_college)
    db.commit()
    db.refresh(db_college)
    return db_college


def update_college(
    db: Session, college_id: str, college: schemas.CollegeUpdate
) -> models.College | None:
    db_college = get_college(db, college_id)
    if not db_college:
        return None
    update_data = college.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_college, key, value)
    db.add(db_college)
    db.commit()
    db.refresh(db_college)
    return db_college


def delete_college(db: Session, college_id: str) -> bool:
    db_college = get_college(db, college_id)
    if not db_college:
        return False
    db.delete(db_college)
    db.commit()
    return True

# ─── CollegeApplication ───

def get_application(db: Session, application_id: str) -> models.CollegeApplication | None:
    return db.query(models.CollegeApplication).filter(models.CollegeApplication.id == application_id).first()


def get_applications_by_student(db: Session, student_id: str) -> list[models.CollegeApplication]:
    return db.query(models.CollegeApplication).filter(models.CollegeApplication.student_id == student_id).all()


def create_application(db: Session, application: schemas.CollegeApplicationCreate) -> models.CollegeApplication:
    db_app = models.CollegeApplication(**application.model_dump())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


def update_application(
    db: Session, application_id: str, application: schemas.CollegeApplicationUpdate
) -> models.CollegeApplication | None:
    db_app = get_application(db, application_id)
    if not db_app:
        return None
    update_data = application.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_app, key, value)
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


def update_application_status(
    db: Session, application_id: str, status: str
) -> models.CollegeApplication | None:
    db_app = get_application(db, application_id)
    if not db_app:
        return None
    db_app.status = status
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


def delete_application(db: Session, application_id: str) -> bool:
    db_app = get_application(db, application_id)
    if not db_app:
        return False
    db.delete(db_app)
    db.commit()
    return True

# ─── StudyPlan ───

def get_study_plan(db: Session, plan_id: str) -> models.StudyPlan | None:
    return db.query(models.StudyPlan).filter(models.StudyPlan.id == plan_id).first()


def get_study_plans_by_student(db: Session, student_id: str) -> list[models.StudyPlan]:
    return db.query(models.StudyPlan).filter(models.StudyPlan.student_id == student_id).all()


def create_study_plan(db: Session, plan: schemas.StudyPlanCreate) -> models.StudyPlan:
    items_data = plan.items if plan.items else []
    db_plan = models.StudyPlan(
        student_id=plan.student_id,
        title=plan.title,
        start_date=plan.start_date,
        end_date=plan.end_date,
        target_exam=plan.target_exam,
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    for item in items_data:
        db_item = models.StudyPlanItem(
            study_plan_id=db_plan.id,
            title=item.title,
            description=item.description,
            due_date=item.due_date,
            status=item.status,
        )
        db.add(db_item)
    db.commit()
    db.refresh(db_plan)
    return db_plan


def update_study_plan_item(
    db: Session, plan_id: str, item_id: str, item_update: schemas.StudyPlanItemUpdate
) -> models.StudyPlanItem | None:
    db_item = (
        db.query(models.StudyPlanItem)
        .filter(models.StudyPlanItem.id == item_id, models.StudyPlanItem.study_plan_id == plan_id)
        .first()
    )
    if not db_item:
        return None
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_study_plan(db: Session, plan_id: str) -> bool:
    db_plan = get_study_plan(db, plan_id)
    if not db_plan:
        return False
    db.delete(db_plan)
    db.commit()
    return True


def generate_study_plan(
    db: Session,
    student_id: str,
    target_exam: str,
    target_exam_date: date,
) -> models.StudyPlan | None:
    from datetime import date as dt_date, timedelta
    # Get latest diagnostic result for the student
    diagnostics = (
        db.query(models.DiagnosticResult)
        .filter(models.DiagnosticResult.student_id == student_id)
        .order_by(models.DiagnosticResult.created_at.desc())
        .all()
    )
    skill_gaps: list[str] = []
    if diagnostics:
        latest = diagnostics[0]
        for gap in latest.skill_gaps or []:
            if isinstance(gap, dict):
                skill_name = gap.get("skill") or gap.get("name")
                if skill_name:
                    skill_gaps.append(str(skill_name))
            elif isinstance(gap, str):
                skill_gaps.append(gap)
    if not skill_gaps:
        skill_gaps = ["general review"]

    start_date = dt_date.today()
    if target_exam_date < start_date:
        target_exam_date = start_date + timedelta(days=7)

    total_days = max(1, (target_exam_date - start_date).days)
    plan_title = f"{target_exam.upper()} Study Plan"
    db_plan = models.StudyPlan(
        student_id=student_id,
        title=plan_title,
        start_date=start_date,
        end_date=target_exam_date,
        target_exam=target_exam,
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    # Distribute items evenly across days
    for i, skill in enumerate(skill_gaps):
        item_date = start_date + timedelta(days=(i * total_days // max(1, len(skill_gaps))))
        db_item = models.StudyPlanItem(
            study_plan_id=db_plan.id,
            title=f"Review: {skill}",
            description=f"Focus on {skill} based on diagnostic results.",
            due_date=item_date,
            status="scheduled",
        )
        db.add(db_item)
    db.commit()
    db.refresh(db_plan)
    return db_plan

# ─── ForumPost ───

def get_forum_post(db: Session, post_id: str) -> models.ForumPost | None:
    return db.query(models.ForumPost).filter(models.ForumPost.id == post_id).first()


def get_forum_posts(
    db: Session, course_id: str | None = None, skip: int = 0, limit: int = 100
) -> list[models.ForumPost]:
    query = db.query(models.ForumPost)
    if course_id:
        query = query.filter(models.ForumPost.course_id == course_id)
    return query.order_by(models.ForumPost.created_at.desc()).offset(skip).limit(limit).all()


def create_forum_post(db: Session, post: schemas.ForumPostCreate) -> models.ForumPost:
    db_post = models.ForumPost(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_forum_post(
    db: Session, post_id: str, post: schemas.ForumPostUpdate
) -> models.ForumPost | None:
    db_post = get_forum_post(db, post_id)
    if not db_post:
        return None
    for field, value in post.model_dump(exclude_unset=True).items():
        setattr(db_post, field, value)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_forum_post(db: Session, post_id: str) -> bool:
    db_post = get_forum_post(db, post_id)
    if not db_post:
        return False
    db.delete(db_post)
    db.commit()
    return True


# ─── Leaderboard ───
from datetime import datetime, timedelta
from sqlalchemy import func

def get_leaderboard(
    db: Session, subject: str | None = None, limit: int = 10
) -> list[dict]:
    since = datetime.utcnow() - timedelta(days=7)
    query = (
        db.query(
            models.Student.id.label("student_id"),
            models.Student.name,
            func.sum(models.TestResult.correct_count).label("xp_gained"),
        )
        .join(models.TestResult, models.Student.id == models.TestResult.student_id)
        .filter(models.TestResult.created_at >= since)
    )
    if subject:
        query = query.filter(models.TestResult.subject == subject)
    rows = (
        query.group_by(models.Student.id, models.Student.name)
        .order_by(func.sum(models.TestResult.correct_count).desc())
        .limit(limit)
        .all()
    )
    result = []
    for rank, row in enumerate(rows, start=1):
        result.append({
            "student_id": row.student_id,
            "name": row.name,
            "xp_gained": row.xp_gained or 0,
            "rank": rank,
        })
    return result


# ─── Subscription ───

def get_subscription(db: Session, subscription_id: str) -> models.Subscription | None:
    return db.query(models.Subscription).filter(models.Subscription.id == subscription_id).first()


def get_subscription_by_user(db: Session, user_id: str) -> models.Subscription | None:
    return db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()


def create_subscription(db: Session, subscription: schemas.SubscriptionCreate) -> models.Subscription:
    db_sub = models.Subscription(**subscription.model_dump())
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub


def update_subscription(
    db: Session, subscription_id: str, subscription: schemas.SubscriptionUpdate
) -> models.Subscription | None:
    db_sub = get_subscription(db, subscription_id)
    if not db_sub:
        return None
    for key, value in subscription.model_dump(exclude_unset=True).items():
        setattr(db_sub, key, value)
    db.commit()
    db.refresh(db_sub)
    return db_sub
