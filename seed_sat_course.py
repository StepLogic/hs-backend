"""
Seed SAT Math Prep course via the source-agnostic import endpoint.

Usage:
  python3 seed_sat_course.py          # imports from local JSON file
  python3 seed_sat_course.py --url URL # imports from a remote URL (B2, GitHub, etc.)

The course definition lives in sat_math_prep_course.json.
The platform is course-agnostic — any JSON in the same format can be imported.
"""
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

# ── Config ──
BACKEND_URL = "http://localhost:8000/api/v1"
JSON_FILE = Path(__file__).parent / "sat_math_prep_course.json"


def import_from_file(filepath: str):
    """Import a course JSON from a local file."""
    data = json.loads(Path(filepath).read_text())
    req = Request(
        f"{BACKEND_URL}/courses/import",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req) as resp:
        result = json.loads(resp.read())
    return result


def import_from_url(url: str):
    """Import a course JSON from a URL (B2, GitHub, S3, etc.)."""
    # Backend fetches the URL itself
    req = Request(
        f"{BACKEND_URL}/courses/import-url?url={url}",
        method="POST",
    )
    with urlopen(req) as resp:
        result = json.loads(resp.read())
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--url" and len(sys.argv) > 2:
        print(f"Importing course from URL: {sys.argv[2]}")
        result = import_from_url(sys.argv[2])
    else:
        print(f"Importing course from: {JSON_FILE}")
        if not JSON_FILE.exists():
            print(f"ERROR: {JSON_FILE} not found")
            sys.exit(1)
        result = import_from_file(str(JSON_FILE))

    print(f"✓ Imported: {result.get('course_title', 'unknown')}")
    print(f"  Course ID: {result.get('course_id')}")
    print(f"  Units: {result.get('units')}")
    print(f"  Lessons: {result.get('lessons')}")
    print(f"  Assessment questions: {result.get('assessment_questions')}")