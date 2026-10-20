#!/usr/bin/env python3
"""Load a fixed diagnostic test (data/diagnostic_*.json) and attach it to a course.

    python scripts/seed_diagnostic.py data/diagnostic_math.json --course <course_id>

A course with a diagnostic set serves it, in order, instead of the adaptive placement
(see assessment.next_assessment_question). Each question's `skill` must equal a unit
title in that course, or a miss on it cannot point the study plan at a unit.

Ids are stable (`diagnostic-math-01`), so re-running updates in place.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app import models


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--course", required=True, help="course id the diagnostic belongs to")
    args = ap.parse_args()

    data = json.loads(Path(args.file).read_text())
    test_id = data["source_test_id"]
    db = SessionLocal()
    try:
        course = db.query(models.Course).filter(models.Course.id == args.course).first()
        if not course:
            sys.exit(f"No course {args.course}")
        units = {u.title for u in db.query(models.Unit).filter(models.Unit.course_id == course.id)}
        missing = sorted({q["skill"] for q in data["questions"]} - units)
        if missing:
            sys.exit(f"{course.title} has no unit for: {missing}")

        for n, q in enumerate(data["questions"], 1):
            db.merge(models.Question(
                id=f"{test_id}-{n:02d}",
                subject=data["subject"],
                grade_level=11,
                question_type="multiple-choice" if q.get("options") else "fill-in",
                prompt=q["prompt"],
                context=q.get("context"),
                options=q.get("options"),
                correct_answer=q["correct_answer"],
                skill=q["skill"],
                explanation=q["explanation"],
                difficulty=q["difficulty"],
                review_status="published",
                source_test_id=test_id,
                mock_position=n,
                image_url=q.get("image_url"),
                image_alt=q.get("image_alt"),
                figure_table=q.get("figure_table"),
                course_id=course.id,
            ))
        db.commit()
        print(f"{test_id}: {len(data['questions'])} questions -> {course.title}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
