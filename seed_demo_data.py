#!/usr/bin/env python3
"""Comprehensive seed script for realistic demo data across all hs-backend tables."""

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import Base
from app import models
from app.security import hash_password


def seed():
    engine = create_engine(settings.sqlalchemy_database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        now = datetime.utcnow()
        today = date.today()

        # ── 1. Users ─────────────────────────────────────────────────────────
        print("Seeding users...")
        users = [
            models.User(
                id="user-student-001",
                email="demo.student@homeschool.com",
                password_hash=hash_password("demo1234"),
                role=models.Role.STUDENT,
                created_at=now - timedelta(days=30),
            ),
            models.User(
                id="user-parent-001",
                email="demo.parent@homeschool.com",
                password_hash=hash_password("demo1234"),
                role=models.Role.PARENT,
                created_at=now - timedelta(days=60),
            ),
            models.User(
                id="user-admin-001",
                email="demo.admin@homeschool.com",
                password_hash=hash_password("admin1234"),
                role=models.Role.ADMIN,
                created_at=now - timedelta(days=90),
            ),
            models.User(
                id="user-teacher-001",
                email="demo.teacher@homeschool.com",
                password_hash=hash_password("teacher1234"),
                role=models.Role.TEACHER,
                created_at=now - timedelta(days=45),
            ),
        ]
        for u in users:
            db.merge(u)
        db.commit()
        print(f"  ✓ {len(users)} users")

        # ── 2. Students ──────────────────────────────────────────────────────
        print("Seeding students...")
        students = [
            models.Student(
                id="student-001",
                name="Ava Johnson",
                email="ava.j@school.edu",
                grade_level=10,
                created_at=now - timedelta(days=30),
                owner_user_id="user-parent-001",
            ),
            models.Student(
                id="student-002",
                name="Marcus Chen",
                email="marcus.c@school.edu",
                grade_level=11,
                created_at=now - timedelta(days=25),
                owner_user_id="user-parent-001",
            ),
            models.Student(
                id="student-003",
                name="Sophia Williams",
                email="sophia.w@school.edu",
                grade_level=9,
                created_at=now - timedelta(days=20),
                owner_user_id="user-parent-001",
            ),
        ]
        for s in students:
            db.merge(s)
        db.commit()
        print(f"  ✓ {len(students)} students")

        # ── 3. User Profiles ───────────────────────────────────────────────
        print("Seeding user profiles...")
        profiles = [
            models.UserProfile(
                id="profile-001",
                user_id="user-student-001",
                xp=2450,
                level=8,
                streak_days=12,
                last_active=today - timedelta(days=1),
                badges=json.dumps(["first_test", "perfect_score", "streak_7", "essay_hero"]),
            ),
            models.UserProfile(
                id="profile-002",
                user_id="user-parent-001",
                xp=120,
                level=2,
                streak_days=3,
                last_active=today - timedelta(days=2),
                badges=json.dumps(["early_adopter"]),
            ),
            models.UserProfile(
                id="profile-003",
                user_id="user-admin-001",
                xp=500,
                level=3,
                streak_days=0,
                last_active=today - timedelta(days=5),
                badges=json.dumps(["admin_badge"]),
            ),
        ]
        for p in profiles:
            db.merge(p)
        db.commit()
        print(f"  ✓ {len(profiles)} profiles")

        # ── 4. Exam Blueprints ───────────────────────────────────────────────
        print("Seeding exam blueprints...")
        blueprints = [
            models.ExamBlueprint(
                id="bp-sat-math-001",
                exam_type=models.ExamType.SAT,
                subject=models.Subject.MATH,
                section="Math (No Calculator)",
                question_count=20,
                time_limit_sec=1500,
                grade_level=11,
                skill_weights=json.dumps({
                    "linear-equations": 0.25,
                    "systems-of-equations": 0.15,
                    "quadratics": 0.20,
                    "functions": 0.15,
                    "geometry": 0.15,
                    "data-analysis": 0.10,
                }),
            ),
            models.ExamBlueprint(
                id="bp-sat-reading-001",
                exam_type=models.ExamType.SAT,
                subject=models.Subject.ENGLISH_LANGUAGE_ARTS,
                section="Reading & Writing",
                question_count=25,
                time_limit_sec=1800,
                grade_level=11,
                skill_weights=json.dumps({
                    "reading-comprehension": 0.30,
                    "grammar": 0.25,
                    "vocabulary": 0.20,
                    "inference": 0.15,
                    "main-idea": 0.10,
                }),
            ),
            models.ExamBlueprint(
                id="bp-section-quiz-001",
                exam_type=models.ExamType.SECTION_QUIZ,
                subject=models.Subject.MATH,
                section="Linear Equations",
                question_count=10,
                time_limit_sec=600,
                grade_level=9,
                skill_weights=json.dumps({"linear-equations": 1.0}),
            ),
        ]
        for b in blueprints:
            db.merge(b)
        db.commit()
        print(f"  ✓ {len(blueprints)} blueprints")

        # ── 5. Test Results ────────────────────────────────────────────────────
        print("Seeding test results...")
        test_results = [
            models.TestResult(
                id="tr-001",
                student_id="student-001",
                subject=models.Subject.MATH,
                score=78,
                grade_equivalent=10,
                percentile=82,
                correct_count=16,
                total_questions=20,
                skill_breakdown=json.dumps({
                    "linear-equations": {"correct": 5, "total": 5, "percent": 100},
                    "systems-of-equations": {"correct": 3, "total": 4, "percent": 75},
                    "quadratics": {"correct": 4, "total": 5, "percent": 80},
                    "functions": {"correct": 2, "total": 4, "percent": 50},
                    "geometry": {"correct": 2, "total": 2, "percent": 100},
                }),
                mastery_level=models.MasteryLevel.PROFICIENT,
                exam_type=models.ExamType.SAT,
                timed=True,
                time_limit_sec=1500,
                section="Math (No Calculator)",
                created_at=now - timedelta(days=7),
            ),
            models.TestResult(
                id="tr-002",
                student_id="student-001",
                subject=models.Subject.ENGLISH_LANGUAGE_ARTS,
                score=65,
                grade_equivalent=10,
                percentile=60,
                correct_count=13,
                total_questions=20,
                skill_breakdown=json.dumps({
                    "reading-comprehension": {"correct": 4, "total": 6, "percent": 67},
                    "grammar": {"correct": 3, "total": 5, "percent": 60},
                    "vocabulary": {"correct": 4, "total": 5, "percent": 80},
                    "inference": {"correct": 2, "total": 4, "percent": 50},
                }),
                mastery_level=models.MasteryLevel.DEVELOPING,
                exam_type=models.ExamType.SAT,
                timed=True,
                time_limit_sec=1800,
                section="Reading & Writing",
                created_at=now - timedelta(days=14),
            ),
            models.TestResult(
                id="tr-003",
                student_id="student-002",
                subject=models.Subject.MATH,
                score=92,
                grade_equivalent=11,
                percentile=95,
                correct_count=18,
                total_questions=20,
                skill_breakdown=json.dumps({
                    "linear-equations": {"correct": 5, "total": 5, "percent": 100},
                    "systems-of-equations": {"correct": 4, "total": 4, "percent": 100},
                    "quadratics": {"correct": 5, "total": 5, "percent": 100},
                    "functions": {"correct": 3, "total": 4, "percent": 75},
                    "geometry": {"correct": 1, "total": 2, "percent": 50},
                }),
                mastery_level=models.MasteryLevel.ADVANCED,
                exam_type=models.ExamType.SAT,
                timed=True,
                time_limit_sec=1500,
                section="Math (No Calculator)",
                created_at=now - timedelta(days=3),
            ),
        ]
        for tr in test_results:
            db.merge(tr)
        db.commit()
        print(f"  ✓ {len(test_results)} test results")

        # ── 6. User Answers ──────────────────────────────────────────────────
        print("Seeding user answers...")
        # Get first 20 question IDs for realistic answers
        q_ids = [q[0] for q in db.query(models.Question.id).limit(20).all()]
        if len(q_ids) >= 20:
            answers = []
            for i, qid in enumerate(q_ids[:16]):
                answers.append(models.UserAnswer(
                    id=f"ua-001-{i:03d}",
                    test_result_id="tr-001",
                    question_id=qid,
                    answer=json.dumps(["A"]),
                    is_correct=(i % 5 != 0),  # ~80% correct
                    time_spent=45 + (i % 10) * 5,
                ))
            for i, qid in enumerate(q_ids[:13]):
                answers.append(models.UserAnswer(
                    id=f"ua-002-{i:03d}",
                    test_result_id="tr-002",
                    question_id=qid,
                    answer=json.dumps(["B"]),
                    is_correct=(i % 3 != 0),  # ~67% correct
                    time_spent=50 + (i % 8) * 5,
                ))
            for i, qid in enumerate(q_ids[:18]):
                answers.append(models.UserAnswer(
                    id=f"ua-003-{i:03d}",
                    test_result_id="tr-003",
                    question_id=qid,
                    answer=json.dumps(["C"]),
                    is_correct=(i % 10 != 0),  # ~90% correct
                    time_spent=40 + (i % 6) * 5,
                ))
            for a in answers:
                db.merge(a)
            db.commit()
            print(f"  ✓ {len(answers)} user answers")
        else:
            print(f"  ⚠ Only {len(q_ids)} questions available, skipping user answers")

        # ── 7. Study Plans ───────────────────────────────────────────────────
        print("Seeding study plans...")
        plans = [
            models.StudyPlan(
                id="plan-001",
                student_id="student-001",
                title="SAT Math Mastery Plan",
                start_date=today - timedelta(days=14),
                end_date=today + timedelta(days=30),
                target_exam="SAT",
                created_at=now - timedelta(days=14),
            ),
            models.StudyPlan(
                id="plan-002",
                student_id="student-002",
                title="Reading & Writing Boost",
                start_date=today - timedelta(days=7),
                end_date=today + timedelta(days=21),
                target_exam="SAT",
                created_at=now - timedelta(days=7),
            ),
        ]
        for p in plans:
            db.merge(p)
        db.commit()

        plan_items = [
            models.StudyPlanItem(
                id="pi-001", study_plan_id="plan-001", title="Master Linear Equations",
                description="Complete all practice sets for linear equations", due_date=today + timedelta(days=3), status="in_progress", created_at=now,
            ),
            models.StudyPlanItem(
                id="pi-002", study_plan_id="plan-001", title="Quadratics Deep Dive",
                description="Watch video lessons and complete 5 quizzes", due_date=today + timedelta(days=7), status="scheduled", created_at=now,
            ),
            models.StudyPlanItem(
                id="pi-003", study_plan_id="plan-001", title="Full Mock Test",
                description="Complete a timed full-length practice test", due_date=today + timedelta(days=14), status="scheduled", created_at=now,
            ),
            models.StudyPlanItem(
                id="pi-004", study_plan_id="plan-002", title="Grammar Rules Review",
                description="Review all 20 core grammar rules", due_date=today + timedelta(days=2), status="completed", created_at=now,
            ),
            models.StudyPlanItem(
                id="pi-005", study_plan_id="plan-002", title="Vocabulary Flashcards",
                description="Master 100 SAT vocabulary words", due_date=today + timedelta(days=5), status="in_progress", created_at=now,
            ),
        ]
        for pi in plan_items:
            db.merge(pi)
        db.commit()
        print(f"  ✓ {len(plans)} plans, {len(plan_items)} items")

        # ── 8. Writing Submissions ─────────────────────────────────────────────
        print("Seeding writing submissions...")
        submissions = [
            models.WritingSubmission(
                id="ws-001",
                student_id="student-001",
                prompt="To understand the most important characteristics of a society, one must study its major cities.",
                essay_text="In examining the major cities of any society, we can uncover the most significant characteristics that define that culture. Cities serve as melting pots where diverse populations converge, bringing with them their traditions, values, and innovations. For instance, New York City exemplifies American capitalism and cultural diversity, while Tokyo demonstrates Japan's blend of technological advancement and traditional values. However, focusing solely on cities may overlook the rural traditions and values that equally define a society. Therefore, while cities reveal important characteristics, a comprehensive understanding requires examining both urban and rural contexts.",
                ai_feedback=json.dumps({
                    "overall": 4,
                    "rubric": {"reading": 4, "analysis": 4, "writing": 4},
                    "comments": ["Strong thesis and clear argumentation"],
                    "suggestions": ["Add more specific examples", "Strengthen the conclusion"],
                }),
                status="reviewed",
                created_at=now - timedelta(days=5),
            ),
            models.WritingSubmission(
                id="ws-002",
                student_id="student-001",
                prompt="The best way to teach is to praise positive actions and ignore negative ones.",
                essay_text="While praising positive actions can be an effective motivational tool, completely ignoring negative behaviors is not the best approach to teaching. Positive reinforcement does encourage students to repeat desirable behaviors, but constructive criticism is equally important for growth. Teachers must balance praise with guidance on how to improve. Ignoring negative actions may allow bad habits to persist unchecked. A comprehensive teaching approach addresses both strengths and weaknesses, providing students with a complete picture of their performance and clear pathways for improvement.",
                ai_feedback=json.dumps({
                    "overall": 5,
                    "rubric": {"reading": 5, "analysis": 5, "writing": 5},
                    "comments": ["Excellent nuanced argument"],
                    "suggestions": ["Consider adding a counterexample"],
                }),
                status="reviewed",
                created_at=now - timedelta(days=3),
            ),
            models.WritingSubmission(
                id="ws-003",
                student_id="student-002",
                prompt="Governments should place few, if any, restrictions on scientific research and development.",
                essay_text="Scientific research drives human progress, but unrestricted research can lead to ethical dilemmas and dangerous outcomes. The development of nuclear technology, while beneficial for energy, also created weapons of mass destruction. Genetic research promises cures for diseases but raises concerns about designer babies. Therefore, governments should implement thoughtful restrictions that protect public safety and ethical standards while still encouraging innovation. These restrictions should be developed in collaboration with scientists to ensure they are reasonable and do not stifle beneficial research.",
                ai_feedback=json.dumps({
                    "overall": 5,
                    "rubric": {"reading": 5, "analysis": 5, "writing": 5},
                    "comments": ["Outstanding critical thinking"],
                    "suggestions": [],
                }),
                status="reviewed",
                created_at=now - timedelta(days=2),
            ),
        ]
        for ws in submissions:
            db.merge(ws)
        db.commit()
        print(f"  ✓ {len(submissions)} writing submissions")

        # ── 9. Forum Posts ───────────────────────────────────────────────────
        print("Seeding forum posts...")
        posts = [
            models.ForumPost(
                id="fp-001",
                course_id="3d74b223-f3cd-4ba8-9fa5-0d2f14a93413",
                student_id="student-001",
                title="Tips for Solving Systems of Equations Faster",
                body="I've been struggling with timing on the systems of equations questions. Does anyone have strategies for solving them more quickly? I usually use substitution but it takes too long.",
                tags=json.dumps(["math", "sat", "systems-of-equations", "time-management"]),
                created_at=now - timedelta(days=2),
            ),
            models.ForumPost(
                id="fp-002",
                course_id="3d74b223-f3cd-4ba8-9fa5-0d2f14a93413",
                student_id="student-002",
                title="Best Resources for Quadratic Functions",
                body="Just completed the quadratic functions unit and wanted to share some great practice resources I found. The Khan Academy practice sets are excellent, and the Desmos graphing tool really helps visualize the parabolas.",
                tags=json.dumps(["math", "quadratics", "resources", "recommendations"]),
                created_at=now - timedelta(days=1),
            ),
            models.ForumPost(
                id="fp-003",
                course_id="3d74b223-f3cd-4ba8-9fa5-0d2f14a93413",
                student_id="student-003",
                title="Need Help with Word Problems",
                body="I'm having trouble translating word problems into equations. Does anyone have a step-by-step method they use? Any tips would be greatly appreciated!",
                tags=json.dumps(["math", "word-problems", "help"]),
                created_at=now - timedelta(hours=12),
            ),
        ]
        for p in posts:
            db.merge(p)
        db.commit()
        print(f"  ✓ {len(posts)} forum posts")

        # ── 10. Enrollments ────────────────────────────────────────────────────
        print("Seeding enrollments...")
        enrollments = [
            models.Enrollment(
                id="enr-001",
                student_id="student-001",
                course_id="3d74b223-f3cd-4ba8-9fa5-0d2f14a93413",
                enrolled_at=now - timedelta(days=30),
                status=models.EnrollmentStatus.ACTIVE,
            ),
            models.Enrollment(
                id="enr-002",
                student_id="student-002",
                course_id="3d74b223-f3cd-4ba8-9fa5-0d2f14a93413",
                enrolled_at=now - timedelta(days=20),
                status=models.EnrollmentStatus.ACTIVE,
            ),
            models.Enrollment(
                id="enr-003",
                student_id="student-003",
                course_id="3d74b223-f3cd-4ba8-9fa5-0d2f14a93413",
                enrolled_at=now - timedelta(days=10),
                status=models.EnrollmentStatus.ACTIVE,
            ),
        ]
        for e in enrollments:
            db.merge(e)
        db.commit()
        print(f"  ✓ {len(enrollments)} enrollments")

        # ── 11. Lesson Progress ──────────────────────────────────────────────
        print("Seeding lesson progress...")
        lesson_ids = [l[0] for l in db.query(models.Lesson.id).limit(10).all()]
        progress = []
        for i, lid in enumerate(lesson_ids[:5]):
            progress.append(models.LessonProgress(
                id=f"lp-001-{i:03d}",
                student_id="student-001",
                lesson_id=lid,
                status=models.LessonProgressStatus.COMPLETED,
                mastery_score=80 + i * 3,
                attempts=1,
                last_accessed=now - timedelta(days=20 - i),
            ))
        for i, lid in enumerate(lesson_ids[5:8]):
            progress.append(models.LessonProgress(
                id=f"lp-002-{i:03d}",
                student_id="student-001",
                lesson_id=lid,
                status=models.LessonProgressStatus.IN_PROGRESS,
                mastery_score=45 + i * 10,
                attempts=2,
                last_accessed=now - timedelta(days=5 - i),
            ))
        for i, lid in enumerate(lesson_ids[:7]):
            progress.append(models.LessonProgress(
                id=f"lp-003-{i:03d}",
                student_id="student-002",
                lesson_id=lid,
                status=models.LessonProgressStatus.COMPLETED,
                mastery_score=90 + i * 1,
                attempts=1,
                last_accessed=now - timedelta(days=15 - i),
            ))
        for p in progress:
            db.merge(p)
        db.commit()
        print(f"  ✓ {len(progress)} lesson progress entries")

        # ── 12. Skill Mastery ────────────────────────────────────────────────
        print("Seeding skill mastery...")
        skills = [
            ("student-001", models.Subject.MATH, "linear-equations", models.MasteryLevel.ADVANCED, 95),
            ("student-001", models.Subject.MATH, "systems-of-equations", models.MasteryLevel.PROFICIENT, 78),
            ("student-001", models.Subject.MATH, "quadratics", models.MasteryLevel.PROFICIENT, 82),
            ("student-001", models.Subject.MATH, "functions", models.MasteryLevel.DEVELOPING, 55),
            ("student-001", models.Subject.MATH, "geometry", models.MasteryLevel.ADVANCED, 92),
            ("student-001", models.Subject.ENGLISH_LANGUAGE_ARTS, "reading-comprehension", models.MasteryLevel.DEVELOPING, 62),
            ("student-001", models.Subject.ENGLISH_LANGUAGE_ARTS, "grammar", models.MasteryLevel.PROFICIENT, 75),
            ("student-001", models.Subject.ENGLISH_LANGUAGE_ARTS, "vocabulary", models.MasteryLevel.PROFICIENT, 80),
            ("student-002", models.Subject.MATH, "linear-equations", models.MasteryLevel.ADVANCED, 98),
            ("student-002", models.Subject.MATH, "systems-of-equations", models.MasteryLevel.ADVANCED, 95),
            ("student-002", models.Subject.MATH, "quadratics", models.MasteryLevel.ADVANCED, 96),
            ("student-002", models.Subject.MATH, "functions", models.MasteryLevel.PROFICIENT, 80),
            ("student-002", models.Subject.MATH, "geometry", models.MasteryLevel.DEVELOPING, 60),
            ("student-002", models.Subject.ENGLISH_LANGUAGE_ARTS, "reading-comprehension", models.MasteryLevel.PROFICIENT, 85),
            ("student-002", models.Subject.ENGLISH_LANGUAGE_ARTS, "grammar", models.MasteryLevel.ADVANCED, 90),
            ("student-003", models.Subject.MATH, "linear-equations", models.MasteryLevel.BEGINNER, 40),
            ("student-003", models.Subject.MATH, "systems-of-equations", models.MasteryLevel.BEGINNER, 35),
            ("student-003", models.Subject.MATH, "quadratics", models.MasteryLevel.BEGINNER, 30),
            ("student-003", models.Subject.ENGLISH_LANGUAGE_ARTS, "reading-comprehension", models.MasteryLevel.DEVELOPING, 50),
        ]
        for i, (sid, subj, skill, level, score) in enumerate(skills):
            db.merge(models.SkillMastery(
                id=f"sm-{i:03d}",
                student_id=sid,
                subject=subj,
                skill=skill,
                mastery_level=level,
                mastery_score=score,
                repetitions=5 + i % 10,
                easiness=2.5 + (score / 100) * 1.5,
                interval_days=1 + i % 7,
                due_date=today + timedelta(days=i % 5),
                last_practiced=now - timedelta(days=i % 10),
            ))
        db.commit()
        print(f"  ✓ {len(skills)} skill mastery entries")

        # ── 13. Diagnostic Results ───────────────────────────────────────────
        print("Seeding diagnostic results...")
        diagnostics = [
            models.DiagnosticResult(
                id="diag-001",
                student_id="student-001",
                subject=models.Subject.MATH,
                grade_level_equivalent=10,
                skill_gaps=json.dumps(["functions", "data-analysis"]),
                recommended_courses=json.dumps(["3d74b223-f3cd-4ba8-9fa5-0d2f14a93413"]),
                created_at=now - timedelta(days=30),
            ),
            models.DiagnosticResult(
                id="diag-002",
                student_id="student-002",
                subject=models.Subject.MATH,
                grade_level_equivalent=11,
                skill_gaps=json.dumps(["geometry"]),
                recommended_courses=json.dumps(["3d74b223-f3cd-4ba8-9fa5-0d2f14a93413"]),
                created_at=now - timedelta(days=20),
            ),
        ]
        for d in diagnostics:
            db.merge(d)
        db.commit()
        print(f"  ✓ {len(diagnostics)} diagnostic results")

        # ── 14. Subscriptions ────────────────────────────────────────────────
        print("Seeding subscriptions...")
        subs = [
            models.Subscription(
                id="sub-001",
                user_id="user-parent-001",
                plan="annual",
                status="active",
                current_period_end=now + timedelta(days=180),
                created_at=now - timedelta(days=60),
            ),
            models.Subscription(
                id="sub-002",
                user_id="user-student-001",
                plan="monthly",
                status="active",
                current_period_end=now + timedelta(days=15),
                created_at=now - timedelta(days=15),
            ),
        ]
        for s in subs:
            db.merge(s)
        db.commit()
        print(f"  ✓ {len(subs)} subscriptions")

        # ── 15. Chat Sessions ────────────────────────────────────────────────
        print("Seeding chat sessions...")
        chats = [
            models.ChatSession(
                id="chat-001",
                student_id="student-001",
                subject=models.Subject.MATH,
                title="Help with Quadratic Formula",
                created_at=now - timedelta(days=3),
            ),
            models.ChatSession(
                id="chat-002",
                student_id="student-002",
                subject=models.Subject.ENGLISH_LANGUAGE_ARTS,
                title="Essay Feedback Session",
                created_at=now - timedelta(days=1),
            ),
        ]
        for c in chats:
            db.merge(c)
        db.commit()

        chat_messages = [
            models.ChatMessage(id="cm-001", session_id="chat-001", role="user", content="I don't understand how to use the quadratic formula when the discriminant is negative.", created_at=now - timedelta(days=3, hours=2)),
            models.ChatMessage(id="cm-002", session_id="chat-001", role="assistant", content="When the discriminant (b² - 4ac) is negative, the quadratic equation has no real solutions. Instead, you get two complex solutions. For example, in x² + 4 = 0, the discriminant is 0 - 16 = -16, so the solutions are x = ±2i.", created_at=now - timedelta(days=3, hours=2)),
            models.ChatMessage(id="cm-003", session_id="chat-001", role="user", content="That makes sense! So complex numbers are always paired as conjugates?", created_at=now - timedelta(days=3, hours=1)),
            models.ChatMessage(id="cm-004", session_id="chat-001", role="assistant", content="Exactly! For real-coefficient quadratics, complex roots always come in conjugate pairs (a + bi and a - bi). This is the Complex Conjugate Root Theorem.", created_at=now - timedelta(days=3, hours=1)),
            models.ChatMessage(id="cm-005", session_id="chat-002", role="user", content="Can you review my essay thesis statement? 'The government should regulate social media to protect mental health.'", created_at=now - timedelta(days=1, hours=2)),
            models.ChatMessage(id="cm-006", session_id="chat-002", role="assistant", content="Your thesis is clear and arguable. To strengthen it, consider adding a specific mechanism or consequence. For example: 'The government should regulate social media platforms' algorithms to limit addictive content cycles, thereby protecting adolescent mental health.' This specificity gives you more to analyze in your body paragraphs.", created_at=now - timedelta(days=1, hours=2)),
        ]
        for cm in chat_messages:
            db.merge(cm)
        db.commit()
        print(f"  ✓ {len(chats)} chat sessions, {len(chat_messages)} messages")

        # ── Summary ──────────────────────────────────────────────────────────
        print("\n" + "=" * 50)
        print("DEMO DATA SEED COMPLETE")
        print("=" * 50)
        print(f"  Users:            4")
        print(f"  Students:         3")
        print(f"  Profiles:         3")
        print(f"  Test Results:     3")
        print(f"  Study Plans:      2")
        print(f"  Writing Subs:     3")
        print(f"  Forum Posts:      3")
        print(f"  Enrollments:      3")
        print(f"  Lesson Progress:  {len(progress)}")
        print(f"  Skill Mastery:    {len(skills)}")
        print(f"  Diagnostics:      2")
        print(f"  Subscriptions:    2")
        print(f"  Chat Sessions:    2")
        print(f"  Exam Blueprints:  3")
        print("\nDemo login credentials:")
        print("  Student:  demo.student@homeschool.com / demo1234")
        print("  Parent:   demo.parent@homeschool.com  / demo1234")
        print("  Admin:    demo.admin@homeschool.com   / admin1234")
        print("  Teacher:  demo.teacher@homeschool.com / teacher1234")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
