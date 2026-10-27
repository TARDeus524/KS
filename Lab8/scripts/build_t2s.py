# -*- coding: utf-8 -*-
"""Формує tests/t2s.jsonl з еталонними відповідями, отриманими з Fuseki."""
import json
import re
import requests
from kb8 import T2S, PREFIXES, TESTS, RESULTS, FUSEKI_URL, DATASET, MM_NS

ENDPOINT = f"{FUSEKI_URL}/{DATASET}/query"

def add_prefixes(q):
    return PREFIXES + "\n" + q.strip()

def add_limit(q):
    return q if re.search(r"\bLIMIT\s+\d+", q, re.I) else q.rstrip() + "\nLIMIT 100"

def norm(v):
    if v.get("type") == "uri" and v["value"].startswith(MM_NS):
        return "mm:" + v["value"][len(MM_NS):]
    return v["value"]

def run_reference(q):
    r = requests.get(ENDPOINT, params={"query": add_limit(add_prefixes(q))},
                     headers={"Accept": "application/sparql-results+json"}, timeout=120)
    r.raise_for_status()
    rows = []
    for b in r.json()["results"]["bindings"]:
        rows.append({k: norm(v) for k, v in b.items()})
    return rows

def main():
    records = []
    for item in T2S:
        expected = run_reference(item["reference"])
        rec = {
            "id": item["id"], "difficulty": item["difficulty"],
            "question": item["question"], "reference_query": item["reference"],
            "before_query": item["before"], "after_query": item["after"],
            "expected": expected,
        }
        records.append(rec)
    (TESTS / "t2s.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8")
    print(f"t2s.jsonl: {len(records)} questions")
    for r in records:
        print(r["id"], r["difficulty"], len(r["expected"]), r["expected"][:2])

if __name__ == "__main__":
    main()
