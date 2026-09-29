#!/usr/bin/env python3
"""Restore which module each question of a full mock belongs to.

The original import dropped the source's section index, so a mock's 147 questions came
back as one unordered pile. Given the mock's source JSON (a list of six sections, as
fetch_sat_questions.py saves per mock), this matches every stored question back to its
section and position and writes mock_module / mock_position.

    python scripts/backfill_mock_modules.py fullmock-0 fullmock_0.json          # dry run
    python scripts/backfill_mock_modules.py fullmock-0 fullmock_0.json --apply
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import models  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from scripts.seed_sat_questions import SECTION_MODULES, map_context  # noqa: E402


def _key(prompt, context, answer) -> tuple:
    return (str(prompt or "").strip(), str(context or "").strip(), str(answer or "").strip())


def plan(rows: list, sections: list) -> dict:
    """Map question id -> (module, position). Identical questions (same prompt, passage
    and key) are interchangeable, so they fill that key's slots in order."""
    slots = defaultdict(list)
    for si, section in enumerate(sections):
        for pos, q in enumerate(section):
            k = _key(q.get("question"), map_context(q.get("passage")), q.get("correct_answer"))
            slots[k].append((SECTION_MODULES[si], pos))
    out = {}
    for row in sorted(rows, key=lambda r: r.id):
        k = _key(row.prompt, row.context, row.correct_answer)
        if slots.get(k):
            out[row.id] = slots[k].pop(0)
    return out


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    source_test_id, path, apply = sys.argv[1], sys.argv[2], "--apply" in sys.argv
    sections = json.load(open(path))
    if len(sections) != len(SECTION_MODULES):
        sys.exit(f"expected {len(SECTION_MODULES)} sections, got {len(sections)}")

    db = SessionLocal()
    try:
        rows = db.query(models.Question).filter(models.Question.source_test_id == source_test_id).all()
        mapping = plan(rows, sections)
        expected = sum(len(s) for s in sections)
        print(f"{source_test_id}: {len(rows)} stored, {expected} in file, {len(mapping)} matched")
        counts = defaultdict(int)
        for module, _ in mapping.values():
            counts[module] += 1
        print("  per module:", dict(counts))
        if len(mapping) != len(rows) or len(rows) != expected:
            sys.exit("  refusing to write a partial mapping — the file and the table disagree")
        if not apply:
            print("  dry run; pass --apply to write")
            return
        for row in rows:
            row.mock_module, row.mock_position = mapping[row.id]
        db.commit()
        print("  written")
    finally:
        db.close()


if __name__ == "__main__":
    main()
