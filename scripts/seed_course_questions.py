#!/usr/bin/env python3
"""Generate AI questions for each unit tag in a course.

Usage:
    python scripts/seed_course_questions.py --course-id <id> [--questions-per-tag 10]

Reads lesson content from each unit, prompts an LLM via OLLAMA Cloud API
to generate multiple-choice questions, and stores them in the database.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# --- OLLAMA Cloud API config ---
OLLAMA_CLOUD_API_KEY = os.getenv("OLLAMA_CLOUD_API_KEY", "")
OLLAMA_CLOUD_MODEL = os.getenv("OLLAMA_CLOUD_MODEL", "gemma4:31b-cloud")

# Load .env if present
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)
    OLLAMA_CLOUD_API_KEY = os.getenv("OLLAMA_CLOUD_API_KEY", "")
    OLLAMA_CLOUD_MODEL = os.getenv("OLLAMA_CLOUD_MODEL", OLLAMA_CLOUD_MODEL)


def _ollama_cloud_chat(prompt: str) -> str:
    """Ollama Cloud API — hosts models remotely, no local download."""
    url = "https://ollama.com/api/chat"
    headers = {
        "Authorization": f"Bearer {OLLAMA_CLOUD_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OLLAMA_CLOUD_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert K-12 curriculum designer. "
                    "Return ONLY valid JSON. No markdown. No explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode())
        return body["message"]["content"]


def _parse_json_response(text: str) -> list | dict:
    """Extract JSON from LLM response, handling markdown wrappers."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def generate_questions_with_ai(lesson_content: str, tag: str, count: int = 10) -> list[dict]:
    """Use OLLAMA Cloud API to generate questions from lesson content."""
    if not OLLAMA_CLOUD_API_KEY:
        print("  WARNING: OLLAMA_CLOUD_API_KEY not set. Set it in .env or environment.")
        return []

    prompt = f"""Generate {count} multiple-choice questions about: {tag}

Lesson content:
{lesson_content[:2000]}

Return a JSON object with a "questions" array. Each question object must have:
- prompt: question text (string)
- options: array of exactly 4 choices (strings)
- correct_answer: array with the single correct choice (e.g. ["Paris"])
- explanation: why it's correct (string)
- difficulty: "easy", "medium", or "hard" (string)

Output ONLY valid JSON, no other text."""

    try:
        response = _ollama_cloud_chat(prompt)
        parsed = _parse_json_response(response)
        questions = parsed if isinstance(parsed, list) else parsed.get("questions", [])
        return [q for q in questions if isinstance(q, dict) and "prompt" in q]
    except Exception as e:
        print(f"  AI generation failed: {e}")
        return []


def seed_questions(course_id: str, questions_per_tag: int = 10):
    """Generate and store questions for each unit tag in a course."""
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()

    try:
        course = db.query(models.Course).filter(models.Course.id == course_id).first()
        if not course:
            print(f"Course {course_id} not found")
            return

        units = db.query(models.Unit).filter(models.Unit.course_id == course_id).all()
        print(f"Course: {course.title}")
        print(f"Units: {len(units)}")

        total_created = 0
        for unit in units:
            tag = unit.description or unit.title.lower().replace(" ", "-")
            print(f"\n  Unit: {unit.title} (tag: {tag})")

            # Collect lesson content for context
            lessons = db.query(models.Lesson).filter(models.Lesson.unit_id == unit.id).all()
            combined_content = "\n\n".join(l.content for l in lessons if l.content)

            if not combined_content:
                print(f"    No lesson content, skipping")
                continue

            # Check existing question count for this tag
            existing = db.query(models.Question).filter(
                models.Question.skill == tag,
                models.Question.subject == course.subject,
            ).count()

            if existing >= questions_per_tag:
                print(f"    Already has {existing} questions, skipping")
                continue

            needed = questions_per_tag - existing
            print(f"    Generating {needed} questions...")

            questions = generate_questions_with_ai(combined_content, tag, needed)

            for q in questions:
                # Normalize correct_answer to a list
                correct = q.get("correct_answer", [])
                if isinstance(correct, str):
                    correct = [correct]
                elif not isinstance(correct, list):
                    correct = [str(correct)]

                # Normalize options to a list of strings
                options = q.get("options", [])
                if not isinstance(options, list):
                    options = []

                difficulty_str = str(q.get("difficulty", "medium")).lower()
                try:
                    difficulty = models.Difficulty(difficulty_str)
                except ValueError:
                    difficulty = models.Difficulty.MEDIUM

                db.add(
                    models.Question(
                        subject=course.subject,
                        grade_level=10,
                        question_type=models.QuestionType.MULTIPLE_CHOICE,
                        prompt=q["prompt"],
                        options=options,
                        correct_answer=correct,
                        skill=tag,
                        explanation=q.get("explanation", ""),
                        difficulty=difficulty,
                        review_status=models.ReviewStatus.PUBLISHED,
                    )
                )
                total_created += 1

            db.commit()
            print(f"    Created {len(questions)} questions")

        print(f"\nDone. {total_created} questions created across {len(units)} units.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed AI-generated questions for a course"
    )
    parser.add_argument(
        "--course-id", required=True, help="Course ID to generate questions for"
    )
    parser.add_argument(
        "--questions-per-tag",
        type=int,
        default=10,
        help="Target questions per unit tag (default: 10)",
    )
    args = parser.parse_args()

    seed_questions(args.course_id, args.questions_per_tag)
