#!/usr/bin/env python3
"""
Seed all scraped SAT questions into the backend database,
preserving the original test name in source_test_id.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models


def map_difficulty(src: str) -> str:
    if not src:
        return "medium"
    d = src.lower()
    return d if d in ("easy", "medium", "hard") else "medium"


def map_choices(choices: dict) -> list[str]:
    if not choices:
        return []
    return [f"{k}. {v}" for k, v in sorted(choices.items())]


def build_explanation(q: dict) -> str:
    parts = []
    if q.get("explanation"):
        parts.append(str(q["explanation"]))
    de = q.get("distractor_explanation")
    if de:
        if isinstance(de, list):
            parts.append("\n\nDistractor explanations:")
            for item in de:
                parts.append(str(item))
        else:
            parts.append("\n\nDistractor explanations:\n" + str(de))
    return "\n\n".join(parts)


def map_context(passage) -> str | None:
    if not passage:
        return None
    if isinstance(passage, dict):
        texts = []
        for key in sorted(passage.keys()):
            texts.append(str(passage[key]))
        return "\n\n".join(texts)
    return str(passage)


def transform_and_insert(db: Session, questions_data: list[dict]):
    total = len(questions_data)
    success = 0
    errors = 0

    for i, q in enumerate(questions_data, 1):
        try:
            is_math = bool(q.get("is_math"))
            subject = "math" if is_math else "english_language_arts"

            prompt = str(q.get("question", ""))
            context = map_context(q.get("passage"))
            options = map_choices(q.get("choices", {}))
            correct_answer = str(q.get("correct_answer", ""))
            skill = q.get("skill", "SAT Prep") or q.get("domain", "SAT Prep")
            explanation = build_explanation(q)
            difficulty = map_difficulty(q.get("difficulty"))
            source_test_id = q.get("_source_test_id") or q.get("test_id") or "unknown"

            db_question = models.Question(
                subject=subject,
                grade_level=11,
                question_type="multiple-choice",
                prompt=prompt,
                context=context,
                options=options,
                correct_answer=correct_answer,
                skill=skill,
                explanation=explanation,
                review_status="published",
                difficulty=difficulty,
                source_test_id=source_test_id,
            )
            db.add(db_question)
            success += 1

            if i % 100 == 0:
                db.commit()
                print(f"  committed {i}/{total}")

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  ERROR on question {i} (id={q.get('id')}): {e}")

    db.commit()
    return success, errors


def main():
    data_file = Path(__file__).parent.parent / "data" / "sat_questions" / "all_sat_questions.json"
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        print("Run fetch_sat_questions.py first.")
        sys.exit(1)

    print(f"Loading questions from {data_file}...")
    with open(data_file, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    print(f"Loaded {len(questions_data)} questions.\n")

    db = SessionLocal()
    try:
        success, errors = transform_and_insert(db, questions_data)
        print(f"\n=== SEED COMPLETE ===")
        print(f"Total processed: {len(questions_data)}")
        print(f"Successfully inserted: {success}")
        print(f"Errors: {errors}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
