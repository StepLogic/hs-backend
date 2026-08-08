from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import Subject, QuestionType, MasteryLevel, Role, CourseType, ReviewStatus, EnrollmentStatus, LessonProgressStatus, Difficulty, ExamType, LiveStatus, CertificateStatus


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
    name: Optional[str] = None
    password: str
    role: Role = Role.STUDENT


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
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
    source_test_id: Optional[str] = None
    lesson_id: Optional[str] = None
    unit_id: Optional[str] = None
    course_id: Optional[str] = None
    is_full_test: bool = False

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
    explanation: Optional[str] = None
    hint: Optional[str] = None
    review_status: Optional[ReviewStatus] = None
    difficulty: Optional[Difficulty] = None
    source_test_id: Optional[str] = None
    lesson_id: Optional[str] = None
    unit_id: Optional[str] = None
    course_id: Optional[str] = None
    is_full_test: Optional[bool] = None


class QuestionResponse(QuestionBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def _flatten_options(options: Any) -> Optional[list[str]]:
        if options is None:
            return None
        if not isinstance(options, list):
            return None
        flat: list[str] = []
        for item in options:
            if isinstance(item, list):
                for sub in item:
                    if isinstance(sub, str):
                        flat.append(sub)
            elif isinstance(item, str):
                flat.append(item)
        return flat if flat else None

    @field_validator("options", mode="before")
    @classmethod
    def _validate_options(cls, v: Any) -> Any:
        return cls._flatten_options(v)


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
    certificate_enabled: bool = False
    certificate_passing_score: int = 70


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
    certificate_enabled: Optional[bool] = None
    certificate_passing_score: Optional[int] = None


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
    test_result_id: Optional[str] = None
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


# ─── ChatSession schemas ───
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatSessionCreate(BaseModel):
    student_id: str
    subject: Optional[Subject] = None
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: str
    student_id: str
    subject: Optional[Subject] = None
    title: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage]


# ─── WritingSubmission schemas ───
class WritingSubmissionBase(BaseModel):
    student_id: str
    prompt: str
    essay_text: str
    status: str = "submitted"

class WritingSubmissionCreate(WritingSubmissionBase):
    pass

class WritingSubmissionUpdate(BaseModel):
    ai_feedback: Optional[dict] = None
    human_grade: Optional[dict] = None
    status: Optional[str] = None

class WritingSubmissionResponse(WritingSubmissionBase):
    id: str
    ai_feedback: Optional[dict] = None
    human_grade: Optional[dict] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── DiagnosticResult schemas ───
class DiagnosticResultBase(BaseModel):
    student_id: str
    subject: Subject
    grade_level_equivalent: int
    skill_gaps: list[dict] = []
    recommended_courses: list[str] = []

class DiagnosticResultCreate(DiagnosticResultBase):
    pass

class DiagnosticResultResponse(DiagnosticResultBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── StudyPlan schemas ───

class StudyPlanItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: str = "scheduled"


class StudyPlanItemCreate(StudyPlanItemBase):
    pass


class StudyPlanItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None


class StudyPlanItemResponse(StudyPlanItemBase):
    id: str
    study_plan_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudyPlanBase(BaseModel):
    student_id: str
    title: str
    start_date: date
    end_date: date
    target_exam: Optional[str] = None


class StudyPlanCreate(StudyPlanBase):
    items: list[StudyPlanItemCreate] = []


class StudyPlanUpdate(BaseModel):
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    target_exam: Optional[str] = None


class StudyPlanResponse(StudyPlanBase):
    id: str
    created_at: datetime
    items: list[StudyPlanItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class PlanGenerateRequest(BaseModel):
    student_id: str
    target_exam: str
    target_exam_date: date

# ─── ForumPost schemas ───

class ForumPostBase(BaseModel):
    course_id: str
    student_id: str
    title: str
    body: str
    tags: list[str] = []


class ForumPostCreate(ForumPostBase):
    pass


class ForumPostUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[str]] = None


class ForumPostResponse(ForumPostBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Leaderboard schemas ───
class LeaderboardEntry(BaseModel):
    student_id: str
    name: str
    xp_gained: int
    rank: int
# ─── Subscription schemas ───
class SubscriptionBase(BaseModel):
    user_id: str
    plan: str = "monthly"
    status: str = "active"
    current_period_end: Optional[datetime] = None

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    plan: Optional[str] = None
    status: Optional[str] = None
    current_period_end: Optional[datetime] = None

class SubscriptionResponse(SubscriptionBase):
    id: str
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Assessment schemas ───

class AssessmentQuestion(BaseModel):
    id: str
    prompt: str
    question_type: str
    options: Optional[list[str]] = None
    skill: str
    difficulty: str
    unit_tag: str


class AssessmentStartResponse(BaseModel):
    assessment_id: str
    course_id: str
    questions: list[AssessmentQuestion]


class AssessmentAnswer(BaseModel):
    question_id: str
    answer: Any
    skill: str
    unit_tag: str


class AssessmentSubmitRequest(BaseModel):
    student_id: str
    answers: list[AssessmentAnswer]


class TagResult(BaseModel):
    tag: str
    correct: int
    total: int
    percent: float
    level: str  # "weak" or "strong"


class AssessmentSubmitResponse(BaseModel):
    assessment_id: str
    student_id: str
    course_id: str
    weak_tags: list[str]
    strong_tags: list[str]
    tag_results: list[TagResult]
    total_correct: int
    total_questions: int


# ─── Personalized Course schemas ───

class PersonalizedCourseResponse(BaseModel):
    id: str
    student_id: str
    base_course_id: str
    unit_ids: list[str]
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PersonalizedCourseUpdate(BaseModel):
    unit_ids: list[str]


# ─── TutorMeeting schemas ───

class TutorMeetingBase(BaseModel):
    student_id: str
    course_id: str
    tutor_id: Optional[str] = None
    topic: str
    scheduled_at: Optional[datetime] = None
    duration_min: int = 30
    status: str = "requested"
    meeting_url: Optional[str] = None
    student_notes: Optional[str] = None
    tutor_notes: Optional[str] = None


class TutorMeetingCreate(BaseModel):
    student_id: str
    course_id: str
    topic: str
    scheduled_at: Optional[datetime] = None
    duration_min: int = 30
    student_notes: Optional[str] = None


class TutorMeetingUpdate(BaseModel):
    tutor_id: Optional[str] = None
    topic: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_min: Optional[int] = None
    status: Optional[str] = None
    meeting_url: Optional[str] = None
    student_notes: Optional[str] = None
    tutor_notes: Optional[str] = None


class TutorMeetingResponse(BaseModel):
    id: str
    student_id: str
    course_id: str
    tutor_id: Optional[str] = None
    topic: str
    scheduled_at: Optional[datetime] = None
    duration_min: int
    status: str
    meeting_url: Optional[str] = None
    student_notes: Optional[str] = None
    tutor_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Final Exam schemas ───

class FinalExamQuestion(BaseModel):
    id: str
    prompt: str
    question_type: str
    options: Optional[list[str]] = None
    skill: str
    difficulty: str


class FinalExamStartResponse(BaseModel):
    exam_id: str
    course_id: str
    questions: list[FinalExamQuestion]


class FinalExamAnswer(BaseModel):
    question_id: str
    answer: Any


class FinalExamSubmitRequest(BaseModel):
    student_id: str
    answers: list[FinalExamAnswer]


class FinalExamSubmitResponse(BaseModel):
    exam_id: str
    student_id: str
    course_id: str
    total_correct: int
    total_questions: int
    score: int
    passed: bool
    passing_score: int


# ─── Certificate schemas ───

class EligibilityResponse(BaseModel):
    eligible: bool
    lessons_completed: int
    total_lessons: int
    all_lessons_done: bool
    final_exam_taken: bool
    final_score: Optional[int] = None
    final_passed: bool
    certificate_enabled: bool


class ClaimResponse(BaseModel):
    certificate_id: str
    student_name: str
    course_title: str
    earned_at: datetime
    final_score: int
    certificate_hash: str


class CertificateResponse(BaseModel):
    id: str
    student_id: str
    course_id: str
    earned_at: datetime
    final_score: int
    status: str
    certificate_hash: str
    model_config = ConfigDict(from_attributes=True)
