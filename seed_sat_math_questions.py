#!/usr/bin/env python3
"""Seed SAT Math questions from scraped markdown file.

Parses sat-math-free-form-questions.md and seeds questions into the database.
Maps questions to the SAT Math course units by skill/topic.
"""
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models

MARKDOWN_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sat-math-free-form-questions.md"
)

# Map scraped categories to unit description tags
CATEGORY_TO_SKILL = {
    "CENTER AND SPREAD": "Center and Spread",
    "RATIO RATES AND PROPORTION": "Ratio, Rates, and Proportion",
    "PERCENTAGES": "Percentages",
    "SYSTEMS OF 2 LINEAR EQUATIONS": "Systems of 2 Linear Equations",
    "LINEAR EQUATIONS": "Linear Equations",
    "DATA_INTERPRETATION": "Data Interpretation",
    "ALGEBRAIC EXPRESSIONS": "Algebraic Expressions",
    "RIGHT TRIANGLES & TRIGONOMETRY": "Right Triangles and Trigonometry",
    "LINES, ANGLES, AND TRIANGLES": "Lines, Angles, and Triangles",
    "QUADRATICS": "Quadratics",
    "EXPONENTIAL EXPRESSIONS": "Exponential Expressions",
    "GEOMETRY AND TRIGONOMETRY": "Geometry and Trigonometry",
    "PROBLEM SOLVING AND DATA ANALYSIS": "Problem Solving and Data Analysis",
    "ALGEBRA": "Algebra",
    "ADVANCED MATH": "Advanced Math",
}


def parse_markdown_questions(filepath: str) -> list[dict]:
    """Parse questions from markdown file."""
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return []

    content = open(filepath, "r", encoding="utf-8").read()

    # Split by question sections - handle both "## Question 1:" and "## Question 1: Title"
    question_blocks = re.split(r"\n## Question \d+: ", content)[1:]

    questions = []
    for block in question_blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        # First line is the question name (after the split removed "Question X: ")
        question_name = lines[0].strip()

        # Parse metadata
        category = ""
        topic = ""
        difficulty = ""
        question_text = ""
        answer_choices = []
        correct_answer = ""
        explanation = ""

        in_question = False
        in_choices = False
        in_explanation = False

        for line in lines[1:]:
            line = line.strip()

            if line.startswith("**Category:**"):
                category = line.replace("**Category:**", "").strip().upper()
            elif line.startswith("**Topic:**"):
                topic = line.replace("**Topic:**", "").strip()
            elif line.startswith("**Difficulty:**"):
                difficulty = line.replace("**Difficulty:**", "").strip()
            elif line.startswith("### Question"):
                in_question = True
                in_choices = False
                in_explanation = False
            elif line.startswith("### Answer Choices"):
                in_question = False
                in_choices = True
                in_explanation = False
            elif line.startswith("### Explanation"):
                in_question = False
                in_choices = False
                in_explanation = True
            elif in_question and line and not line.startswith("**"):
                question_text += line + "\n"
            elif in_choices and line.startswith("- **"):
                # Parse: "- **A.** Answer text ✅"
                choice_match = re.match(r"- \*\*([A-E])\.\*\* (.+)", line)
                if choice_match:
                    choice_text = choice_match.group(2).replace(" ✅", "")
                    is_correct = "✅" in line
                    answer_choices.append({
                        "label": choice_match.group(1),
                        "text": choice_text,
                        "is_correct": is_correct
                    })
                    if is_correct:
                        correct_answer = choice_match.group(1)
            elif in_explanation and line and not line.startswith("**"):
                explanation += line + "\n"

        if question_text and answer_choices:
            questions.append({
                "name": question_name,
                "category": category,
                "topic": topic,
                "difficulty": difficulty,
                "prompt": question_text.strip(),
                "options": [f"{c['label']}. {c['text']}" for c in answer_choices],
                "correct_answer": correct_answer,
                "explanation": explanation.strip(),
            })

    return questions


def seed_questions():
    """Seed questions into the database."""
    db = SessionLocal()
    try:
        questions = parse_markdown_questions(MARKDOWN_FILE)
        if not questions:
            print("No questions parsed from markdown file")
            return

        print(f"Parsed {len(questions)} questions from markdown")

        # Find or create SAT Math course
        course = db.query(models.Course).filter(
            models.Course.title == "SAT Math Complete Prep"
        ).first()

        if not course:
            print("SAT Math course not found. Creating...")
            course = models.Course(
                id=f"course-sat-math-{uuid.uuid4().hex[:8]}",
                title="SAT Math Complete Prep",
                short_title="SAT Math",
                subject="test_prep",
                description="Comprehensive SAT Math preparation with adaptive assessment",
                grade_range="9-12",
                price=0,
                original_price=0,
                rating=0.0,
                review_count=0,
                icon="📐",
                color="bg-indigo-500",
                image_emoji="📐",
                features=[],
                skills=[],
            )
            db.add(course)
            db.commit()
            print(f"Created SAT Math course: {course.id}")

        # Map categories to skills and seed questions
        seeded_count = 0
        for q in questions:
            skill = CATEGORY_TO_SKILL.get(q["category"], q["topic"])

            # Check if question already exists
            existing = db.query(models.Question).filter(
                models.Question.prompt == q["prompt"][:100]
            ).first()
            if existing:
                continue

            question = models.Question(
                id=f"q-sat-{uuid.uuid4().hex[:8]}",
                prompt=q["prompt"],
                question_type=models.QuestionType.MULTIPLE_CHOICE,
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                skill=skill,
                subject="math",
                grade_level=10,
                difficulty=models.Difficulty.MEDIUM,
                review_status=models.ReviewStatus.PUBLISHED,
            )
            db.add(question)
            seeded_count += 1

        db.commit()
        print(f"Seeded {seeded_count} SAT Math questions")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_questions()
