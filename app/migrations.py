"""Safe migration: adds missing columns to existing tables on production.
Idempotent — checks if column exists before adding.
"""
from sqlalchemy import text
from app.database import engine

MIGRATIONS = [
    # lessons table
    ("lessons", "content_blocks", "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS content_blocks JSON DEFAULT '[]' NOT NULL"),
    ("lessons", "resources", "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS resources JSON DEFAULT '[]' NOT NULL"),
    ("lessons", "objectives", "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS objectives JSON DEFAULT '[]' NOT NULL"),
    ("lessons", "homework", "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS homework JSON DEFAULT '[]' NOT NULL"),
    ("lessons", "difficulty", "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS difficulty VARCHAR DEFAULT 'medium' NOT NULL"),
    ("lessons", "review_status", "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS review_status VARCHAR DEFAULT 'published' NOT NULL"),
    ("lessons", "prerequisite_lesson_id", "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS prerequisite_lesson_id VARCHAR REFERENCES lessons(id)"),
    ("lessons", "skills", "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS skills JSON DEFAULT '[]' NOT NULL"),

    # user_answers: make test_result_id nullable
    ("user_answers", "test_result_id_nullable", "ALTER TABLE user_answers ALTER COLUMN test_result_id DROP NOT NULL"),

    # courses: add missing columns
    ("courses", "course_type", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS course_type VARCHAR DEFAULT 'core' NOT NULL"),
    ("courses", "price", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS price FLOAT DEFAULT 0 NOT NULL"),
    ("courses", "original_price", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS original_price FLOAT"),
    ("courses", "skills", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS skills JSON DEFAULT '[]' NOT NULL"),
    ("courses", "grade_range", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS grade_range VARCHAR DEFAULT '9-12' NOT NULL"),
    ("courses", "lesson_count", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS lesson_count INTEGER DEFAULT 0 NOT NULL"),
    ("courses", "student_count", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS student_count INTEGER DEFAULT 0 NOT NULL"),
    ("courses", "rating", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS rating FLOAT DEFAULT 0 NOT NULL"),
    ("courses", "review_count", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0 NOT NULL"),
    ("courses", "features", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS features JSON DEFAULT '[]' NOT NULL"),
    ("courses", "image_emoji", "ALTER TABLE courses ADD COLUMN IF NOT EXISTS image_emoji VARCHAR DEFAULT '📚' NOT NULL"),
]


def run_safe_migrations():
    """Run all migrations. SQLite ignores most ALTER statements, Postgres supports them."""
    applied = []
    skipped = []
    for table, check_name, sql in MIGRATIONS:
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
                applied.append(f"{table}.{check_name}")
        except Exception as e:
            skipped.append(f"{table}.{check_name}: {str(e)[:80]}")
    return {"applied": applied, "skipped": skipped}