#!/usr/bin/env python3
"""Add source_test_id column to questions table if it doesn't exist."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


def main():
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='questions' AND column_name='source_test_id'"
            )
        )
        if result.fetchone():
            print("source_test_id column already exists")
        else:
            conn.execute(text("ALTER TABLE questions ADD COLUMN source_test_id VARCHAR"))
            print("source_test_id column added successfully")

        result = conn.execute(text("SELECT COUNT(*) FROM questions"))
        count = result.scalar()
        print(f"Current questions in DB: {count}")


if __name__ == "__main__":
    main()
