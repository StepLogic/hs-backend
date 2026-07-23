#!/usr/bin/env python3
"""Seed assessment questions for all course units.

Each unit's description becomes a question skill. The assessment endpoint
matches questions to unit tags via `Question.skill == Unit.description`.
"""
import os
import sys
import random
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models


SAMPLE_QUESTIONS = {
    "multiple-choice": [
        {
            "prompt": "What is the value of x in the equation 2x + 4 = 10?",
            "options": ["2", "3", "4", "5"],
            "correct_answer": "3",
            "explanation": "Subtract 4 from both sides: 2x = 6. Then divide by 2: x = 3.",
        },
        {
            "prompt": "Which of the following is a prime number?",
            "options": ["9", "15", "17", "21"],
            "correct_answer": "17",
            "explanation": "17 is only divisible by 1 and itself.",
        },
        {
            "prompt": "What is 25% of 80?",
            "options": ["15", "20", "25", "30"],
            "correct_answer": "20",
            "explanation": "25% of 80 = 0.25 × 80 = 20.",
        },
        {
            "prompt": "If a triangle has angles 40° and 60°, what is the third angle?",
            "options": ["60°", "70°", "80°", "90°"],
            "correct_answer": "80°",
            "explanation": "The sum of angles in a triangle is 180°. 180 - 40 - 60 = 80°.",
        },
        {
            "prompt": "What is the slope of the line y = 3x - 7?",
            "options": ["-7", "3", "7", "-3"],
            "correct_answer": "3",
            "explanation": "The slope is the coefficient of x in y = mx + b form.",
        },
        {
            "prompt": "Which expression is equivalent to (x²)(x³)?",
            "options": ["x⁵", "x⁶", "x⁸", "2x⁵"],
            "correct_answer": "x⁵",
            "explanation": "When multiplying with the same base, add exponents: 2 + 3 = 5.",
        },
        {
            "prompt": "What is the area of a circle with radius 4?",
            "options": ["8π", "12π", "16π", "20π"],
            "correct_answer": "16π",
            "explanation": "Area = πr² = π(4)² = 16π.",
        },
        {
            "prompt": "Solve: 3(x - 2) = 2x + 4",
            "options": ["6", "8", "10", "12"],
            "correct_answer": "10",
            "explanation": "3x - 6 = 2x + 4 → x = 10.",
        },
        {
            "prompt": "What is the median of the set {3, 7, 1, 9, 5}?",
            "options": ["3", "5", "7", "9"],
            "correct_answer": "5",
            "explanation": "Sorted: {1, 3, 5, 7, 9}. The middle value is 5.",
        },
        {
            "prompt": "If f(x) = 2x² - 3x + 1, what is f(2)?",
            "options": ["1", "3", "5", "7"],
            "correct_answer": "3",
            "explanation": "f(2) = 2(4) - 3(2) + 1 = 8 - 6 + 1 = 3.",
        },
        {
            "prompt": "What is the probability of rolling an even number on a fair six-sided die?",
            "options": ["1/3", "1/2", "2/3", "1/6"],
            "correct_answer": "1/2",
            "explanation": "Even numbers are 2, 4, 6. Probability = 3/6 = 1/2.",
        },
        {
            "prompt": "Which ratio is equivalent to 3:4?",
            "options": ["6:7", "9:12", "12:16", "9:12 and 12:16"],
            "correct_answer": "9:12 and 12:16",
            "explanation": "Both 9:12 and 12:16 simplify to 3:4.",
        },
    ],
    "fill-in": [
        {
            "prompt": "What is 7 × 8?",
            "correct_answer": "56",
            "explanation": "7 × 8 = 56.",
        },
        {
            "prompt": "What is the square root of 144?",
            "correct_answer": "12",
            "explanation": "12 × 12 = 144.",
        },
    ],
}


def create_question(db: SessionLocal, subject: models.Subject, grade_level: int, skill: str, template: dict, qtype: models.QuestionType):
    """Create a single question from a template."""
    q = models.Question(
        id=str(uuid.uuid4()),
        subject=subject,
        grade_level=grade_level,
        question_type=qtype,
        prompt=template["prompt"],
        options=template.get("options"),
        correct_answer=template["correct_answer"],
        skill=skill,
        explanation=template["explanation"],
        review_status=models.ReviewStatus.PUBLISHED,
        difficulty=random.choice([models.Difficulty.EASY, models.Difficulty.MEDIUM, models.Difficulty.HARD]),
    )
    db.add(q)
    return q


def seed_questions_for_course(db: SessionLocal, course: models.Course, questions_per_tag: int = 5):
    """Seed questions for all units in a course."""
    units = db.query(models.Unit).filter(models.Unit.course_id == course.id).all()
    if not units:
        print(f"  ⚠️  Course '{course.title}' has no units — skipping.")
        return 0

    created = 0
    for unit in units:
        tag = unit.description or unit.title
        if not tag:
            continue

        # Check how many questions already exist for this skill
        existing = db.query(models.Question).filter(
            models.Question.skill == tag,
            models.Question.review_status == models.ReviewStatus.PUBLISHED,
        ).count()

        needed = max(0, questions_per_tag - existing)
        if needed == 0:
            print(f"  ✅  {tag}: already has {existing} questions")
            continue

        # Generate questions from templates
        templates = random.choices(
            SAMPLE_QUESTIONS["multiple-choice"],
            k=needed,
        )

        for tmpl in templates:
            create_question(
                db,
                subject=course.subject,
                grade_level=10,
                skill=tag,
                template=tmpl,
                qtype=models.QuestionType.MULTIPLE_CHOICE,
            )
            created += 1

        print(f"  ➕  {tag}: added {needed} questions (now {existing + needed} total)")

    return created


def preview_assessment(db: SessionLocal, course: models.Course):
    """Preview what the assessment endpoint would return."""
    units = db.query(models.Unit).filter(models.Unit.course_id == course.id).all()
    if not units:
        return None

    unit_tags = list({u.description for u in units if u.description})
    preview = []

    for tag in unit_tags:
        tag_questions = (
            db.query(models.Question)
            .filter(
                models.Question.skill == tag,
                models.Question.review_status == models.ReviewStatus.PUBLISHED,
            )
            .limit(10)
            .all()
        )
        sample_size = min(3, len(tag_questions))
        sampled = random.sample(tag_questions, sample_size) if sample_size > 0 else []
        preview.append({
            "tag": tag,
            "available": len(tag_questions),
            "sampled": sample_size,
            "questions": [
                {"id": q.id, "prompt": q.prompt, "skill": q.skill, "difficulty": q.difficulty.value}
                for q in sampled
            ],
        })

    return preview


def main():
    print("=" * 60)
    print("SEED ASSESSMENT QUESTIONS")
    print("=" * 60)

    db = SessionLocal()
    try:
        courses = db.query(models.Course).all()
        print(f"\nFound {len(courses)} courses:\n")

        total_created = 0
        for course in courses:
            print(f"📚 {course.title} ({course.id})")
            created = seed_questions_for_course(db, course, questions_per_tag=5)
            total_created += created
            print()

        if total_created > 0:
            db.commit()
            print(f"✅ Committed {total_created} new questions to the database.\n")
        else:
            print("ℹ️  No new questions needed — all units already have enough.\n")

        # Preview assessments
        print("=" * 60)
        print("ASSESSMENT PREVIEW")
        print("=" * 60)

        for course in courses:
            print(f"\n📋 {course.title}\n")
            preview = preview_assessment(db, course)
            if not preview:
                print("  (no units)")
                continue

            for group in preview:
                print(f"  🏷️  Tag: '{group['tag']}'")
                print(f"     Available: {group['available']} | Sampled for assessment: {group['sampled']}")
                for q in group["questions"]:
                    print(f"        • [{q['difficulty']}] {q['prompt'][:80]}...")
                print()

    finally:
        db.close()
        print("Done. 🎉")


if __name__ == "__main__":
    main()
