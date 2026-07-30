#!/usr/bin/env python3
"""
Fetch all SAT questions from the Bloom Academy API and save as JSON.
"""
import json
import requests
import time
import sys
from pathlib import Path

BASE_URL = "https://7fr62ee3qc.execute-api.us-west-2.amazonaws.com/prod"
USER = "test@test-ninjas.com"

def fetch_fullmock(mock_id):
    url = f"{BASE_URL}/fullmock?user={USER}&mock={mock_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_test(test_id):
    url = f"{BASE_URL}/test?test_id={test_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def extract_questions(data, source_test_id):
    """Extract flat list of questions from API response."""
    questions = []
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], list):
            # fullmock format: list of sections, each section is list of questions
            for section_idx, section in enumerate(data):
                for q in section:
                    q["_source_test_id"] = source_test_id
                    q["_section_idx"] = section_idx
                    questions.append(q)
        elif len(data) > 0 and isinstance(data[0], dict):
            # test format: flat list of questions
            for q in data:
                q["_source_test_id"] = source_test_id
                q["_section_idx"] = 0
                questions.append(q)
    return questions

def main():
    output_dir = Path(__file__).parent.parent / "data" / "sat_questions"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_questions = []
    seen_ids = set()

    # 1. Fetch 20 full practice tests (mock IDs 0-19)
    print("Fetching 20 full practice tests...")
    for mock_id in range(20):
        try:
            data = fetch_fullmock(mock_id)
            questions = extract_questions(data, f"fullmock-{mock_id}")
            new_count = 0
            for q in questions:
                qid = q.get("id")
                if qid and qid not in seen_ids:
                    seen_ids.add(qid)
                    all_questions.append(q)
                    new_count += 1
            print(f"  mock={mock_id}: {len(questions)} questions, {new_count} new")
            time.sleep(0.3)
        except Exception as e:
            print(f"  mock={mock_id}: ERROR - {e}")

    # 2. Fetch sectional practice tests
    skills = [
        "boundaries", "central-ideas-and-details", "command-of-evidence",
        "command-of-evidence-quantitative", "cross-text-connections",
        "form-structure-and-sense", "inferences", "rhetorical-synthesis",
        "text-structure-and-purpose", "transitions", "words-in-context"
    ]

    print("\nFetching sectional practice tests...")
    for skill in skills:
        for set_num in range(1, 31):
            test_id = f"ps-{skill}-{set_num}"
            try:
                data = fetch_test(test_id)
                questions = extract_questions(data, test_id)
                new_count = 0
                for q in questions:
                    qid = q.get("id")
                    if qid and qid not in seen_ids:
                        seen_ids.add(qid)
                        all_questions.append(q)
                        new_count += 1
                print(f"  {test_id}: {len(questions)} questions, {new_count} new")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {test_id}: ERROR - {e}")

    # 3. Fetch guided practice tests
    guided_tests = [
        "guided-word-in-context", "guided-word-in-context-hard",
        "guided-word-in-context-hard-2", "guided-word-in-context-hard-3",
        "guided-central-ideas-and-details", "guided-central-ideas-and-details-poem",
        "guided-cross-text-connections", "guided-rhetorical-synthesis",
        "guided-rhetorical-synthesis-hard", "guided-text-structure-and-purpose",
        "guided-text-structure-and-purpose-hard", "guided-boundaries",
        "guided-command-of-evidence-poem", "guided-command-of-evidence",
        "guided-inferences", "guided-form-structure-and-sense",
        "guided-transitions", "guided-transitions-hard"
    ]

    print("\nFetching guided practice tests...")
    for test_id in guided_tests:
        try:
            data = fetch_test(test_id)
            questions = extract_questions(data, test_id)
            new_count = 0
            for q in questions:
                qid = q.get("id")
                if qid and qid not in seen_ids:
                    seen_ids.add(qid)
                    all_questions.append(q)
                    new_count += 1
            print(f"  {test_id}: {len(questions)} questions, {new_count} new")
            time.sleep(0.3)
        except Exception as e:
            print(f"  {test_id}: ERROR - {e}")

    # Save results
    output_file = output_dir / "all_sat_questions.json"
    with open(output_file, "w") as f:
        json.dump(all_questions, f, indent=2)

    print(f"\n=== DONE ===")
    print(f"Total unique questions: {len(all_questions)}")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    main()
