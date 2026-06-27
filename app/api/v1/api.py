from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics, auth, content, courses, diagnostics, enrollments, exams, learning, lessons, live, notifications, plans, practice, profiles, questions, results, roster, sat, skills, social, students, transcripts, tutor, units, uploads, writing,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(practice.router, prefix="/practice", tags=["practice"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(transcripts.router, prefix="/transcripts", tags=["transcripts"])
api_router.include_router(roster.router, prefix="/roster", tags=["roster"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(units.router, prefix="/units", tags=["units"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["enrollments"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(results.router, prefix="/results", tags=["results"])
api_router.include_router(
    results.answers_router, prefix="/answers", tags=["answers"]
)
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(live.router, prefix="/live", tags=["live"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["tutor"])
api_router.include_router(writing.router, prefix="/writing", tags=["writing"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(social.router, prefix="/social", tags=["social"])
api_router.include_router(sat.router, prefix="/sat", tags=["sat"])