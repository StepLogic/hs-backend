"""Upload course JSON to B2 and return the public URL."""
import sys
from pathlib import Path

from app.b2 import get_bucket, PUBLIC_BASE


def upload_course_json(filepath: str, key: str = None) -> str:
    """Upload a course JSON file to B2. Returns the public URL."""
    p = Path(filepath)
    if not p.exists():
        print(f"ERROR: {filepath} not found")
        sys.exit(1)

    key = key or f"courses/{p.name}"
    data = p.read_bytes()

    bucket = get_bucket()
    bucket.upload_bytes(data, key)
    url = f"{PUBLIC_BASE}/{key}"
    print(f"✓ Uploaded {p.name} to B2: {url}")
    print(f"  Key: {key}")
    print(f"  Size: {len(data)} bytes")
    return url


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "sat_math_prep_course.json"
    key = sys.argv[2] if len(sys.argv) > 2 else None
    url = upload_course_json(filepath, key)
    print(f"\nTo import on production:")
    print(f"  curl -X POST 'https://hs-backend-75yy.onrender.com/api/v1/courses/import-url?url={url}'")