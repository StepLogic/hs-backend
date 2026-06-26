from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict

from app.models import Subject, QuestionType, MasteryLevel, Role, CourseType, ReviewStatus, EnrollmentStatus, LessonProgressStatus, Difficulty, ExamType, LiveStatus


# ─── SkillTaxonomy schemas ───
class SkillTaxonomyBase(BaseModel):
    subject: Subject
    skill: str
    description: Optional[str] = None


class SkillTaxonomyCreate(SkillTaxonomyBase):
    pass


class SkillTaxonomyResponse(SkillTaxonomyBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Auth schemas ───
class UserCreate(BaseModel):
    email: str
    password: str
    role: Role = Role.STUDENT


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: Role
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
    role: Role
    user_id: str


# ─── Question schemas ───
class QuestionBase(BaseModel):
    subject: Subject
    grade_level: int
    question_type: QuestionType
    prompt: str
    context: Optional[str] = None
    options: Optional[list[str]] = None
    pairs: Optional[list[dict[str, str]]] = None
    items: Optional[list[str]] = None
    correct_answer: Any
    skill: str
    explanation: str
    hint: Optional[str] = None
    review_status: Optional[ReviewStatus] = None
    difficulty: Difficulty = Difficulty.MEDIUM

class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    subject: Optional[Subject] = None
    grade_level: Optional[int] = None
    question_type: Optional[QuestionType] = None
    prompt: Optional[str] = None
    context: Optional[str] = None
    options: Optional[list[str]] = None
    pairs: Optional[list[dict[str, str]]] = None
    items: Optional[list[str]] = None
    correct_answer: Optional[Any] = None
    skill: Optional[str] = None
    hint: Optional[str] = None
    review_status: Optional[ReviewStatus] = None
    difficulty: Optional[Difficulty] = None


class QuestionResponse(QuestionBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Course schemas ───
class CourseBase(BaseModel):
    subject: Subject
    course_type: CourseType = CourseType.CORE
    title: str
    short_title: str
    description: str
    icon: str
    color: str
    price: float
    original_price: Optional[float] = None
    skills: list[str]
    grade_range: str
    lesson_count: int = 0
    student_count: int = 0
    rating: float = 0.0
    review_count: int = 0
    features: list[str]
    image_emoji: str


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    subject: Optional[Subject] = None
    course_type: Optional[CourseType] = None
    title: Optional[str] = None
    short_title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    skills: Optional[list[str]] = None
    grade_range: Optional[str] = None
    lesson_count: Optional[int] = None
    student_count: Optional[int] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    features: Optional[list[str]] = None
    image_emoji: Optional[str] = None


class CourseResponse(CourseBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Student schemas ───
class StudentBase(BaseModel):
    name: str
    email: Optional[str] = None
    grade_level: int
class StudentCreate(StudentBase):
    owner_user_id: Optional[str] = None



class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    grade_level: Optional[int] = None


class StudentResponse(StudentBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── TestResult schemas ───
class TestResultBase(BaseModel):
    student_id: str
    subject: Subject
    score: int
    grade_equivalent: int
    percentile: int
    correct_count: int
    total_questions: int
    skill_breakdown: dict[str, Any]
    mastery_level: MasteryLevel
    exam_type: Optional[ExamType] = None
    timed: bool = False
    time_limit_sec: Optional[int] = None
    section: Optional[str] = None


class TestResultCreate(TestResultBase):
    pass


class TestResultUpdate(BaseModel):
    student_id: Optional[str] = None
    subject: Optional[Subject] = None
    score: Optional[int] = None
    grade_equivalent: Optional[int] = None
    percentile: Optional[int] = None
    correct_count: Optional[int] = None
    total_questions: Optional[int] = None
    skill_breakdown: Optional[dict[str, Any]] = None
    mastery_level: Optional[MasteryLevel] = None
    exam_type: Optional[ExamType] = None
    timed: Optional[bool] = None
    time_limit_sec: Optional[int] = None
    section: Optional[str] = None


class TestResultResponse(TestResultBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── UserAnswer schemas ───
class UserAnswerBase(BaseModel):
    test_result_id: str
    question_id: str
    answer: Any
    is_correct: bool
    time_spent: int


class UserAnswerCreate(UserAnswerBase):
    pass


class UserAnswerUpdate(BaseModel):
    test_result_id: Optional[str] = None
    question_id: Optional[str] = None
    answer: Optional[Any] = None
    is_correct: Optional[bool] = None
    time_spent: Optional[int] = None


class UserAnswerResponse(UserAnswerBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Unit schemas ───
class UnitBase(BaseModel):
    course_id: str
    title: str
    slug: str
    order_index: int = 0
    description: Optional[str] = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    order_index: Optional[int] = None
    description: Optional[str] = None


class UnitResponse(UnitBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Lesson schemas ───
class LessonBase(BaseModel):
    unit_id: str
    title: str
    slug: str
    order_index: int = 0
    content: str = ""
    content_blocks: list[dict] = []
    resources: list[dict] = []
    objectives: list[str] = []
    homework: list[dict] = []
    duration_min: int = 10
    skills: list[str] = []
    review_status: ReviewStatus = ReviewStatus.PUBLISHED
    difficulty: Difficulty = Difficulty.MEDIUM
    prerequisite_lesson_id: Optional[str] = None
class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    unit_id: Optional[str] = None
    title: Optional[str] = None
    slug: Optional[str] = None
    order_index: Optional[int] = None
    content: Optional[str] = None
    content_blocks: Optional[list[dict]] = None
    resources: Optional[list[dict]] = None
    objectives: Optional[list[str]] = None
    homework: Optional[list[dict]] = None
    duration_min: Optional[int] = None
    skills: Optional[list[str]] = None
    review_status: Optional[ReviewStatus] = None
    difficulty: Optional[Difficulty] = None
    prerequisite_lesson_id: Optional[str] = None


class LessonResponse(LessonBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Enrollment schemas ───
class EnrollmentBase(BaseModel):
    student_id: str
    course_id: str
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseModel):
    status: Optional[EnrollmentStatus] = None


class EnrollmentResponse(EnrollmentBase):
    id: str
    enrolled_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── LessonProgress schemas ───
class LessonProgressBase(BaseModel):
    student_id: str
    lesson_id: str
    status: LessonProgressStatus = LessonProgressStatus.NOT_STARTED
    mastery_score: int = 0
    attempts: int = 0


class LessonProgressCreate(LessonProgressBase):
    pass


class LessonProgressUpdate(BaseModel):
    status: Optional[LessonProgressStatus] = None
    mastery_score: Optional[int] = None
    attempts: Optional[int] = None


class LessonProgressResponse(LessonProgressBase):
    id: str
    last_accessed: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── SkillMastery schemas ───
class SkillMasteryBase(BaseModel):
    student_id: str
    subject: Subject
    skill: str
    mastery_level: MasteryLevel = MasteryLevel.BEGINNER
    mastery_score: int = 0
    repetitions: int = 0
    easiness: float = 2.5
    interval_days: int = 1
    due_date: date
    last_practiced: Optional[datetime] = None


class SkillMasteryCreate(SkillMasteryBase):
    pass


class SkillMasteryUpdate(BaseModel):
    mastery_level: Optional[MasteryLevel] = None
    mastery_score: Optional[int] = None
    repetitions: Optional[int] = None
    easiness: Optional[float] = None
    interval_days: Optional[int] = None
    due_date: Optional[date] = None
    last_practiced: Optional[datetime] = None


class SkillMasteryResponse(SkillMasteryBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── UserProfile schemas ───
class UserProfileBase(BaseModel):
    user_id: str
    xp: int = 0
    level: int = 1
    streak_days: int = 0
    last_active: Optional[date] = None
    badges: list[str] = []


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    xp: Optional[int] = None
    level: Optional[int] = None
    streak_days: Optional[int] = None
    last_active: Optional[date] = None
    badges: Optional[list[str]] = None


class UserProfileResponse(UserProfileBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Practice schemas ───
class PracticeAnswer(BaseModel):
    question_id: str
    answer: Any
    is_correct: bool
    time_spent: int


class PracticeSubmit(BaseModel):
    student_id: str
    subject: Subject
    lesson_id: Optional[str] = None
    answers: list[PracticeAnswer]


class PracticeSubmitResponse(BaseModel):
    test_result: TestResultResponse
    skill_mastery: list[SkillMasteryResponse]
    lesson_progress: Optional[LessonProgressResponse] = None


# ─── ExamBlueprint schemas ───
class ExamBlueprintBase(BaseModel):
    exam_type: ExamType
    subject: Optional[Subject] = None
    section: Optional[str] = None
    question_count: int = 10
    time_limit_sec: int = 1800
    grade_level: Optional[int] = None
    skill_weights: dict[str, int] = {}


class ExamBlueprintCreate(ExamBlueprintBase):
    pass


class ExamBlueprintUpdate(BaseModel):
    exam_type: Optional[ExamType] = None
    subject: Optional[Subject] = None
    section: Optional[str] = None
    question_count: Optional[int] = None
    time_limit_sec: Optional[int] = None
    grade_level: Optional[int] = None
    skill_weights: Optional[dict[str, int]] = None


class ExamBlueprintResponse(ExamBlueprintBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── LiveSession schemas ───
class LiveSessionBase(BaseModel):
    course_id: str
    title: str
    starts_at: datetime
    duration_min: int = 60
    meeting_url: Optional[str] = None
    recording_url: Optional[str] = None
    status: LiveStatus = LiveStatus.SCHEDULED
    max_students: int = 30
    teacher_id: Optional[str] = None

class LiveSessionCreate(LiveSessionBase):
    pass

class LiveSessionUpdate(BaseModel):
    course_id: Optional[str] = None
    title: Optional[str] = None
    starts_at: Optional[datetime] = None
    duration_min: Optional[int] = None
    meeting_url: Optional[str] = None
    recording_url: Optional[str] = None
    status: Optional[LiveStatus] = None
    max_students: Optional[int] = None
    teacher_id: Optional[str] = None

class LiveSessionResponse(LiveSessionBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
