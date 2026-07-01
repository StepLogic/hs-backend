"""Seed the new SAT MATH course into the hosted backend."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

BACKEND_URL = os.getenv("BACKEND_URL", "https://hs-backend-75yy.onrender.com/api/v1")
JSON_FILE = Path(__file__).parent / "sat_math_course.json"


def import_course():
    if not JSON_FILE.exists():
        print(f"ERROR: {JSON_FILE} not found")
        return 1

    data = json.loads(JSON_FILE.read_text())
    req = Request(
        f"{BACKEND_URL}/courses/import",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req) as resp:
        result = json.loads(resp.read())

    print(f"Imported: {result.get('course_title', 'unknown')}")
    print(f"  Course ID: {result.get('course_id')}")
    print(f"  Units: {result.get('units')}")
    print(f"  Lessons: {result.get('lessons')}")
    print(f"  Assessment questions: {result.get('assessment_questions')}")
    return 0


if __name__ == "__main__":
    exit(import_course())
