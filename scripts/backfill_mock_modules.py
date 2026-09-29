#!/usr/bin/env python3
"""Restore which module each question of a full mock belongs to.

The original import dropped the source's section index, so a mock's 147 questions came
back as one unordered pile. Given the mock's source JSON (a list of six sections, as
fetch_sat_questions.py saves per mock), this matches every stored question back to its
section and position and writes mock_module / mock_position.

    python scripts/backfill_mock_modules.py fullmock-0 fullmock_0.json          # dry run
    python scripts/backfill_mock_modules.py fullmock-0 fullmock_0.json --apply

or every mock at once from the fetch script's combined output, whose questions each carry
_source_test_id and _section_idx:

    python scripts/backfill_mock_modules.py --all data/all_sat_questions.json [--apply]
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


def sections_by_mock(flat: list) -> dict:
    """The combined file is flat, in fetch order; regroup it into each mock's sections."""
    mocks: dict = defaultdict(lambda: [[] for _ in SECTION_MODULES])
    for q in flat:
        mock = str(q.get("_source_test_id") or "")
        if mock.startswith("fullmock-"):
            mocks[mock][q["_section_idx"]].append(q)
    return dict(mocks)


def backfill(db, source_test_id: str, sections: list, apply: bool) -> bool:
    rows = db.query(models.Question).filter(models.Question.source_test_id == source_test_id).all()
    mapping = plan(rows, sections)
    expected = sum(len(s) for s in sections)
    counts = defaultdict(int)
    for module, _ in mapping.values():
        counts[module] += 1
    ok = len(mapping) == len(rows) == expected
    print(f"{source_test_id}: {len(rows)} stored, {expected} in file, {len(mapping)} matched "
          f"{dict(counts)}{'' if ok else '  -> SKIPPED, the file and the table disagree'}")
    if ok and apply:
        for row in rows:
            row.mock_module, row.mock_position = mapping[row.id]
    return ok


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--apply"]
    apply = "--apply" in sys.argv
    if len(args) != 2:
        sys.exit(__doc__)
    if args[0] == "--all":
        todo = sorted(sections_by_mock(json.load(open(args[1]))).items())
    else:
        todo = [(args[0], json.load(open(args[1])))]
    for mock, sections in todo:
        if len(sections) != len(SECTION_MODULES):
            sys.exit(f"{mock}: expected {len(SECTION_MODULES)} sections, got {len(sections)}")

    db = SessionLocal()
    try:
        results = [backfill(db, mock, sections, apply) for mock, sections in todo]
        print(f"{sum(results)}/{len(results)} mocks fully matched")
        if apply:
            db.commit()  # one transaction: mismatched mocks were left untouched
            print("written")
        else:
            print("dry run; pass --apply to write")
    finally:
        db.close()


if __name__ == "__main__":
    main()
