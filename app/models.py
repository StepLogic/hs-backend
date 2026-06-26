import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, Float, Boolean, Date, DateTime, ForeignKey, Enum, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Subject(str, PyEnum):
    MATH = "math"
    ENGLISH_LANGUAGE_ARTS = "english_language_arts"
    SCIENCE = "science"
    SOCIAL_STUDIES = "social_studies"
    WORLD_LANGUAGES = "world_languages"
    TEST_PREP = "test_prep"
    COLLEGE_READINESS = "college_readiness"


class Role(str, PyEnum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"


class QuestionType(str, PyEnum):
    MULTIPLE_CHOICE = "multiple-choice"
    FILL_IN = "fill-in"
    ORDERING = "ordering"
    MATCHING = "matching"


class MasteryLevel(str, PyEnum):
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"


class CourseType(str, PyEnum):
    CORE = "core"
    TEST_PREP = "test_prep"
    COLLEGE_READINESS = "college_readiness"


class ReviewStatus(str, PyEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    REJECTED = "rejected"


class EnrollmentStatus(str, PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"


class LessonProgressStatus(str, PyEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Difficulty(str, PyEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = Column(Enum(Subject), nullable=False)
    grade_level = Column(Integer, nullable=False)
    question_type = Column("type", Enum(QuestionType), nullable=False)
    prompt = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    options = Column(JSON, nullable=True)
    pairs = Column(JSON, nullable=True)
    items = Column(JSON, nullable=True)
    correct_answer = Column("correct_answer", JSON, nullable=False)
    skill = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    hint = Column(Text, nullable=True)
    review_status = Column(Enum(ReviewStatus), nullable=False, default=ReviewStatus.PUBLISHED)
    difficulty = Column(Enum(Difficulty), nullable=False, default=Difficulty.MEDIUM)

class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = Column(Enum(Subject), nullable=False)
    course_type = Column(Enum(CourseType), nullable=False, default=CourseType.CORE)
    title = Column(String, nullable=False)
    short_title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=False)
    color = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    skills = Column(JSON, nullable=False, default=list)
    grade_range = Column(String, nullable=False)
    lesson_count = Column(Integer, nullable=False, default=0)
    student_count = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=False, default=0.0)
    review_count = Column(Integer, nullable=False, default=0)
    features = Column(JSON, nullable=False, default=list)
    image_emoji = Column(String, nullable=False)

    units = relationship("Unit", back_populates="course", cascade="all, delete-orphan", order_by="Unit.order_index")


class SkillTaxonomy(Base):
    __tablename__ = "skill_taxonomy"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = Column(Enum(Subject), nullable=False)
    skill = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("subject", "skill"),)


class Unit(Base):
    __tablename__ = "units"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)

    course = relationship("Course", back_populates="units")
    lessons = relationship("Lesson", back_populates="unit", cascade="all, delete-orphan", order_by="Lesson.order_index")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    title = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=False)
    content_blocks = Column(JSON, nullable=False, default=list)
    resources = Column(JSON, nullable=False, default=list)
    objectives = Column(JSON, nullable=False, default=list)
    homework = Column(JSON, nullable=False, default=list)
    duration_min = Column(Integer, nullable=False, default=10)
    skills = Column(JSON, nullable=False, default=list)
    review_status = Column(Enum(ReviewStatus), nullable=False, default=ReviewStatus.PUBLISHED)
    difficulty = Column(Enum(Difficulty), nullable=False, default=Difficulty.MEDIUM)
    prerequisite_lesson_id = Column(String, ForeignKey("lessons.id"), nullable=True)

    unit = relationship("Unit", back_populates="lessons")
    prerequisite = relationship("Lesson", remote_side="Lesson.id")

class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    grade_level = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    owner_user_id = Column(String, ForeignKey("users.id"), nullable=True)

    test_results = relationship("TestResult", back_populates="student", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="owned_students")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    lesson_progress = relationship("LessonProgress", back_populates="student", cascade="all, delete-orphan")
    skill_masteries = relationship("SkillMastery", back_populates="student", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.STUDENT)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owned_students = relationship("Student", back_populates="owner")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.ACTIVE)

    student = relationship("Student", back_populates="enrollments")
    __table_args__ = (UniqueConstraint("student_id", "course_id"),)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False)
    status = Column(Enum(LessonProgressStatus), nullable=False, default=LessonProgressStatus.NOT_STARTED)
    mastery_score = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="lesson_progress")
    __table_args__ = (UniqueConstraint("student_id", "lesson_id"),)


class SkillMastery(Base):
    __tablename__ = "skill_mastery"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    subject = Column(Enum(Subject), nullable=False)
    skill = Column(String, nullable=False)
    mastery_level = Column(Enum(MasteryLevel), nullable=False, default=MasteryLevel.BEGINNER)
    mastery_score = Column(Integer, nullable=False, default=0)
    repetitions = Column(Integer, nullable=False, default=0)
    easiness = Column(Float, nullable=False, default=2.5)
    interval_days = Column(Integer, nullable=False, default=1)
    due_date = Column(Date, default=datetime.utcnow, nullable=False)
    last_practiced = Column(DateTime, nullable=True)
    student = relationship("Student", back_populates="skill_masteries")
    __table_args__ = (UniqueConstraint("student_id", "subject", "skill"),)


class ExamType(str, PyEnum):
    SAT = "sat"
    ACT = "act"
    AP = "ap"
    SECTION_QUIZ = "section_quiz"


class ExamBlueprint(Base):
    __tablename__ = "exam_blueprints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    exam_type = Column(Enum(ExamType), nullable=False)
    subject = Column(Enum(Subject), nullable=True)
    section = Column(String, nullable=True)
    question_count = Column(Integer, nullable=False, default=10)
    time_limit_sec = Column(Integer, nullable=False, default=1800)
    grade_level = Column(Integer, nullable=True)
    skill_weights = Column(JSON, nullable=False, default=dict)


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    subject = Column(Enum(Subject), nullable=False)
    score = Column(Integer, nullable=False)
    grade_equivalent = Column(Integer, nullable=False)
    percentile = Column(Integer, nullable=False)
    correct_count = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    skill_breakdown = Column(JSON, nullable=False, default=dict)
    mastery_level = Column(Enum(MasteryLevel), nullable=False)
    exam_type = Column(Enum(ExamType), nullable=True)
    timed = Column(Boolean, nullable=False, default=False)
    time_limit_sec = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="test_results")
    user_answers = relationship("UserAnswer", back_populates="test_result", cascade="all, delete-orphan")


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_result_id = Column(String, ForeignKey("test_results.id"), nullable=False)
    question_id = Column(String, nullable=False)
    answer = Column(JSON, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_spent = Column(Integer, nullable=False)

    test_result = relationship("TestResult", back_populates="user_answers")


class LiveStatus(str, PyEnum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"
    CANCELLED = "cancelled"


class LiveSession(Base):
    __tablename__ = "live_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    duration_min = Column(Integer, nullable=False, default=60)
    meeting_url = Column(String(500), nullable=True)
    recording_url = Column(String(500), nullable=True)
    status = Column(Enum(LiveStatus), nullable=False, default=LiveStatus.SCHEDULED)
    max_students = Column(Integer, nullable=False, default=30)
    teacher_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    subject = Column(Enum(Subject), nullable=True)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WritingSubmission(Base):
    __tablename__ = "writing_submissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    essay_text = Column(Text, nullable=False)
    ai_feedback = Column(JSON, nullable=True)
    human_grade = Column(JSON, nullable=True)
    status = Column(String(20), default="submitted")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    xp = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)
    streak_days = Column(Integer, nullable=False, default=0)
    last_active = Column(Date, nullable=True)
    badges = Column(JSON, nullable=False, default=list)

    user = relationship("User", backref="profile")
