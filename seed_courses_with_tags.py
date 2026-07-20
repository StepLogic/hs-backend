#!/usr/bin/env python3
"""Seed script for course-agnostic platform with tag-based personalization.

Creates courses with tagged units and AI-generated questions for testing.
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import Base
from app import models
from app.security import hash_password

# Override database URL if provided via environment
if os.environ.get("DATABASE_URL"):
    settings.sqlalchemy_database_url = os.environ["DATABASE_URL"]


def seed_courses():
    """Seed courses with tagged units and questions."""
    engine = create_engine(settings.sqlalchemy_database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        now = datetime.utcnow()

        # ── 1. Create Courses with Tag-Based Units ───────────────────────────
        print("Seeding courses with tagged units...")

        courses_data = [
            {
                "id": "course-sat-math-001",
                "title": "SAT Math Mastery",
                "short_title": "SAT Math",
                "description": "Complete SAT Math preparation with personalized learning paths based on your weak areas.",
                "subject": models.Subject.MATH,
                "course_type": models.CourseType.TEST_PREP,
                "icon": "📐",
                "color": "#4F46E5",
                "price": 49.99,
                "original_price": 99.99,
                "grade_range": "9-12",
                "image_emoji": "📚",
                "features": ["Adaptive learning", "Personalized paths", "500+ practice questions"],
                "units": [
                    {
                        "title": "Algebra Fundamentals",
                        "slug": "algebra-fundamentals",
                        "tag": "algebra",
                        "description": "Linear equations, inequalities, and systems",
                        "lessons": [
                            {
                                "title": "Solving Linear Equations",
                                "slug": "solving-linear-equations",
                                "content": "A linear equation is an equation where the highest power of the variable is 1. To solve, isolate the variable on one side.",
                                "duration_min": 15,
                                "skills": ["linear-equations"],
                            },
                            {
                                "title": "Systems of Equations",
                                "slug": "systems-of-equations",
                                "content": "A system of equations has multiple equations with shared solutions. Solve by substitution or elimination.",
                                "duration_min": 20,
                                "skills": ["systems-of-equations"],
                            },
                        ],
                    },
                    {
                        "title": "Geometry Essentials",
                        "slug": "geometry-essentials",
                        "tag": "geometry",
                        "description": "Angles, triangles, circles, and coordinate geometry",
                        "lessons": [
                            {
                                "title": "Triangle Properties",
                                "slug": "triangle-properties",
                                "content": "The sum of angles in a triangle is 180°. Pythagorean theorem: a² + b² = c² for right triangles.",
                                "duration_min": 18,
                                "skills": ["triangles"],
                            },
                            {
                                "title": "Circle Theorems",
                                "slug": "circle-theorems",
                                "content": "Key circle formulas: circumference = 2πr, area = πr². Central angles equal their arc measure.",
                                "duration_min": 22,
                                "skills": ["circles"],
                            },
                        ],
                    },
                    {
                        "title": "Advanced Algebra",
                        "slug": "advanced-algebra",
                        "tag": "quadratics",
                        "description": "Quadratic equations, polynomials, and functions",
                        "lessons": [
                            {
                                "title": "Quadratic Equations",
                                "slug": "quadratic-equations",
                                "content": "Standard form: ax² + bx + c = 0. Solve using factoring, completing the square, or quadratic formula.",
                                "duration_min": 25,
                                "skills": ["quadratics"],
                            },
                            {
                                "title": "Functions and Graphs",
                                "slug": "functions-and-graphs",
                                "content": "A function maps each input to exactly one output. f(x) notation represents the output.",
                                "duration_min": 20,
                                "skills": ["functions"],
                            },
                        ],
                    },
                    {
                        "title": "Data Analysis & Statistics",
                        "slug": "data-analysis",
                        "tag": "data-analysis",
                        "description": "Interpreting graphs, statistics, and probability",
                        "lessons": [
                            {
                                "title": "Reading Graphs and Tables",
                                "slug": "reading-graphs",
                                "content": "Always check axes labels and scales. Look for trends, outliers, and relationships.",
                                "duration_min": 15,
                                "skills": ["data-interpretation"],
                            },
                            {
                                "title": "Mean, Median, Mode",
                                "slug": "mean-median-mode",
                                "content": "Mean = average. Median = middle value. Mode = most frequent value.",
                                "duration_min": 12,
                                "skills": ["statistics"],
                            },
                        ],
                    },
                ],
            },
            {
                "id": "course-gre-math-001",
                "title": "GRE Quantitative Reasoning",
                "short_title": "GRE Math",
                "description": "Master GRE quantitative reasoning with adaptive practice and personalized feedback.",
                "subject": models.Subject.MATH,
                "course_type": models.CourseType.TEST_PREP,
                "icon": "📊",
                "color": "#059669",
                "price": 59.99,
                "original_price": 119.99,
                "grade_range": "College+",
                "image_emoji": "🎓",
                "features": ["GRE-focused", "Quantitative comparisons", "Data interpretation"],
                "units": [
                    {
                        "title": "Arithmetic",
                        "slug": "arithmetic",
                        "tag": "arithmetic",
                        "description": "Number properties, ratios, percentages",
                        "lessons": [
                            {
                                "title": "Number Properties",
                                "slug": "number-properties",
                                "content": "Integers, primes, divisibility rules. Even/odd and positive/negative properties.",
                                "duration_min": 20,
                                "skills": ["number-theory"],
                            },
                            {
                                "title": "Ratios and Percentages",
                                "slug": "ratios-percentages",
                                "content": "Ratio a:b = a/b. Percentage = (part/whole) × 100.",
                                "duration_min": 18,
                                "skills": ["ratios"],
                            },
                        ],
                    },
                    {
                        "title": "Algebra Review",
                        "slug": "algebra-review",
                        "tag": "algebra",
                        "description": "Equations, inequalities, word problems",
                        "lessons": [
                            {
                                "title": "Linear Equations and Inequalities",
                                "slug": "linear-inequalities",
                                "content": "Solve equations and inequalities. Remember to flip inequality sign when multiplying/dividing by negative.",
                                "duration_min": 22,
                                "skills": ["inequalities"],
                            },
                        ],
                    },
                ],
            },
            {
                "id": "course-spanish-101",
                "title": "Spanish for Beginners",
                "short_title": "Spanish 101",
                "description": "Learn Spanish from scratch with interactive lessons and AI-powered pronunciation feedback.",
                "subject": models.Subject.WORLD_LANGUAGES,
                "course_type": models.CourseType.CORE,
                "icon": "🇪🇸",
                "color": "#DC2626",
                "price": 39.99,
                "original_price": 79.99,
                "grade_range": "All ages",
                "image_emoji": "💬",
                "features": ["Native speaker audio", "Conversation practice", "Cultural context"],
                "units": [
                    {
                        "title": "Greetings and Introductions",
                        "slug": "greetings",
                        "tag": "greetings",
                        "description": "Basic greetings, introductions, and farewells",
                        "lessons": [
                            {
                                "title": "Hola y Adiós",
                                "slug": "hola-adios",
                                "content": "Hola = Hello, Buenos días = Good morning, Buenas tardes = Good afternoon, Buenas noches = Good night. Adiós = Goodbye, Hasta luego = See you later.",
                                "duration_min": 10,
                                "skills": ["greetings"],
                            },
                        ],
                    },
                    {
                        "title": "Numbers and Counting",
                        "slug": "numbers",
                        "tag": "numbers",
                        "description": "Numbers 1-100, counting, basic math in Spanish",
                        "lessons": [
                            {
                                "title": "Los Números",
                                "slug": "los-numeros",
                                "content": "1-10: uno, dos, tres, cuatro, cinco, seis, siete, ocho, nueve, diez. 11-20: once, doce, trece, catorce, quince, dieciséis, diecisiete, dieciocho, diecinueve, veinte.",
                                "duration_min": 15,
                                "skills": ["numbers"],
                            },
                        ],
                    },
                    {
                        "title": "Basic Grammar",
                        "slug": "basic-grammar",
                        "tag": "grammar",
                        "description": "Articles, noun gender, verb conjugation basics",
                        "lessons": [
                            {
                                "title": "Articles and Gender",
                                "slug": "articles-gender",
                                "content": "El (masculine) / La (feminine) = The. Un (masc) / Una (fem) = A/An. Most nouns ending in -o are masculine, -o are feminine.",
                                "duration_min": 20,
                                "skills": ["articles"],
                            },
                        ],
                    },
                ],
            },
        ]

        for course_data in courses_data:
            # Create course
            course = models.Course(
                id=course_data["id"],
                title=course_data["title"],
                short_title=course_data["short_title"],
                description=course_data["description"],
                subject=course_data["subject"],
                course_type=course_data["course_type"],
                icon=course_data["icon"],
                color=course_data["color"],
                price=course_data["price"],
                original_price=course_data["original_price"],
                grade_range=course_data["grade_range"],
                image_emoji=course_data["image_emoji"],
                features=course_data["features"],
                skills=[],  # Will be populated from unit tags
                lesson_count=sum(len(u["lessons"]) for u in course_data["units"]),
                student_count=0,
                rating=0.0,
                review_count=0,
            )
            db.merge(course)
            db.commit()

            # Create units with tags
            for unit_idx, unit_data in enumerate(course_data["units"]):
                unit = models.Unit(
                    id=f"{course_data['id']}-unit-{unit_idx:03d}",
                    course_id=course_data["id"],
                    title=unit_data["title"],
                    slug=unit_data["slug"],
                    order_index=unit_idx,
                    description=unit_data["description"],
                )
                db.merge(unit)
                db.commit()

                # Create lessons
                for lesson_idx, lesson_data in enumerate(unit_data["lessons"]):
                    lesson = models.Lesson(
                        id=f"{unit.id}-lesson-{lesson_idx:03d}",
                        unit_id=unit.id,
                        title=lesson_data["title"],
                        slug=lesson_data["slug"],
                        order_index=lesson_idx,
                        content=lesson_data["content"],
                        content_blocks=[
                            {"type": "text", "content": lesson_data["content"]},
                            {"type": "video", "url": "https://www.youtube.com/embed/aTsc4WIT2cs"},
                        ],
                        resources=[],
                        objectives=[f"Master {lesson_data['skills'][0]}"],
                        homework=[],
                        duration_min=lesson_data["duration_min"],
                        skills=lesson_data["skills"],
                        difficulty=models.Difficulty.MEDIUM,
                        review_status=models.ReviewStatus.PUBLISHED,
                    )
                    db.merge(lesson)
                    db.commit()

                    # Generate questions for this lesson/unit
                    questions = generate_questions_for_lesson(
                        lesson=lesson,
                        unit_tag=unit_data["tag"],
                        subject=course_data["subject"],
                        grade_level=10,
                    )
                    for q in questions:
                        db.merge(q)
                    db.commit()

        print(f"  ✓ {len(courses_data)} courses seeded")

        # ── 2. Create Enrollments for Demo Students ──────────────────────────
        print("Creating demo enrollments...")
        students = db.query(models.Student).all()
        courses = db.query(models.Course).all()

        enrollments = []
        for student in students[:2]:  # First 2 students
            for course in courses:
                enrollment = models.Enrollment(
                    id=f"enr-{student.id}-{course.id}",
                    student_id=student.id,
                    course_id=course.id,
                    status=models.EnrollmentStatus.ACTIVE,
                )
                enrollments.append(enrollment)
                db.merge(enrollment)
        db.commit()
        print(f"  ✓ {len(enrollments)} enrollments created")

        # ── 3. Summary ────────────────────────────────────────────────────────
        print("\n" + "=" * 50)
        print("COURSE SEEDING COMPLETE")
        print("=" * 50)
        for course_data in courses_data:
            print(f"\n  Course: {course_data['title']}")
            print(f"  ID: {course_data['id']}")
            for unit in course_data["units"]:
                print(f"    - Unit: {unit['title']} (tag: {unit['tag']})")

        print("\n  To seed questions for a course, run:")
        print(f"    python scripts/seed_course_questions.py --course-id {courses_data[0]['id']}")

    finally:
        db.close()


def generate_questions_for_lesson(lesson, unit_tag, subject, grade_level):
    """Generate practice questions for a lesson.

    In production, this would call AI (gemma3B:cloud via OLLAMA).
    For seeding, we create template-based questions.
    """
    questions = []

    # Template questions based on common patterns
    question_templates = [
        {
            "prompt": f"Solve for x: 2x + 5 = 13",
            "correct_answer": ["4"],
            "options": [["3"], ["4"], ["5"], ["6"]],
            "skill": "linear-equations",
            "difficulty": models.Difficulty.EASY,
        },
        {
            "prompt": f"What is the value of x if 3x - 7 = 14?",
            "correct_answer": ["7"],
            "options": [["5"], ["6"], ["7"], ["8"]],
            "skill": "linear-equations",
            "difficulty": models.Difficulty.MEDIUM,
        },
        {
            "prompt": f"Which of the following is a solution to x² - 4 = 0?",
            "correct_answer": ["2"],
            "options": [["-4"], ["-2"], ["2"], ["4"]],
            "skill": "quadratics",
            "difficulty": models.Difficulty.MEDIUM,
        },
        {
            "prompt": f"What is the area of a triangle with base 6 and height 8?",
            "correct_answer": ["24"],
            "options": [["12"], ["24"], ["36"], ["48"]],
            "skill": "geometry",
            "difficulty": models.Difficulty.EASY,
        },
        {
            "prompt": f"If f(x) = 2x + 3, what is f(5)?",
            "correct_answer": ["13"],
            "options": [["10"], ["11"], ["12"], ["13"]],
            "skill": "functions",
            "difficulty": models.Difficulty.MEDIUM,
        },
        {
            "prompt": f"What is the mean of: 2, 4, 6, 8, 10?",
            "correct_answer": ["6"],
            "options": [["4"], ["5"], ["6"], ["7"]],
            "skill": "statistics",
            "difficulty": models.Difficulty.EASY,
        },
        {
            "prompt": f"Translate to Spanish: 'Good morning'",
            "correct_answer": ["Buenos días"],
            "options": [["Buenas noches"], ["Buenos días"], ["Buenas tardes"], ["Hola"]],
            "skill": "greetings",
            "difficulty": models.Difficulty.EASY,
        },
        {
            "prompt": f"What is the feminine form of 'el niño'?",
            "correct_answer": ["la niña"],
            "options": [["el niña"], ["la niño"], ["la niña"], ["los niños"]],
            "skill": "grammar",
            "difficulty": models.Difficulty.MEDIUM,
        },
    ]

    for i, template in enumerate(question_templates[:4]):  # 4 questions per lesson
        q = models.Question(
            id=f"q-{lesson.id}-{i:03d}",
            subject=subject,
            grade_level=grade_level,
            question_type=models.QuestionType.MULTIPLE_CHOICE,
            prompt=template["prompt"],
            context=None,
            options=template["options"],
            correct_answer=template["correct_answer"],
            skill=unit_tag,  # Tag from unit
            explanation=f"The correct answer is {template['correct_answer'][0]}.",
            hint="Try substituting the answer choices back into the equation.",
            difficulty=template["difficulty"],
            review_status=models.ReviewStatus.PUBLISHED,
        )
        questions.append(q)

    return questions


if __name__ == "__main__":
    seed_courses()
