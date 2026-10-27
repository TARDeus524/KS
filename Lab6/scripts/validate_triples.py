# -*- coding: utf-8 -*-
"""Перевірка JSONL-триплетів LLM: схема, цитата, каталог, domain/range."""
import csv, json, re, sys
from pathlib import Path
import kb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"
RESULTS = ROOT / "results"

SOURCE_FILES = {
    "GTFS Reference 2026": "gtfs_reference.txt",
    "Transmodel (Wikipedia, rev. 1277981919)": "transmodel.txt",
    "Intelligent transportation system (Wikipedia)": "its_wiki.txt",
}
REQUIRED = {"id", "subject", "subject_id", "subject_type", "predicate", "predicate_id",
            "object", "object_id", "object_type", "source", "evidence", "status", "error_type"}

def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()

def load_texts():
    return {k: norm((DATA / "texts" / v).read_text(encoding="utf-8")) for k, v in SOURCE_FILES.items()}

def check_type(cid, typ, is_obj=False):
    if cid not in kb.CONCEPTS:
        return "unknown_concept"
    actual = kb.CONCEPTS[cid][3]
    if typ != actual:
        return "declared_type_mismatch"
    return None

def validate_record(r, texts):
    errors = []
    missing = REQUIRED - set(r)
    if missing:
        errors.append("schema_missing:" + ",".join(sorted(missing)))
    quote = "missing_evidence"
    if not norm(r.get("evidence", "")):
        errors.append("missing_evidence")
    elif r.get("source") not in SOURCE_FILES:
        quote = "source_unknown"; errors.append("source_unknown")
    else:
        if norm(r["evidence"]) in texts[r["source"]]:
            quote = "confirmed"
        else:
            quote = "not_found"; errors.append("quote_not_found")

    pid = r.get("predicate_id")
    if pid not in kb.RELATIONS:
        errors.append("unknown_relation")
    else:
        dom, ran = kb.RELATIONS[pid][2], kb.RELATIONS[pid][3]
        sid, oid = r.get("subject_id"), r.get("object_id")
        te = check_type(sid, r.get("subject_type"))
        if te: errors.append("subject_" + te)
        te = check_type(oid, r.get("object_type"))
        if te: errors.append("object_" + te)
        if dom and kb.CONCEPTS.get(sid, ("",0,"","",False,""))[3] not in dom:
            errors.append("domain_violation")
        if ran == {"__instance__"}:
            if not kb.CONCEPTS.get(oid, ("",0,"","",False,""))[4]:
                errors.append("range_violation")
        elif ran and kb.CONCEPTS.get(oid, ("",0,"","",False,""))[3] not in ran:
            errors.append("range_violation")

    manual = r.get("error_type")
    if manual == "direction_error":
        errors.append("direction_error")

    # пріоритет класифікації для звіту
    if "missing_evidence" in errors: final = "missing_evidence"
    elif "quote_not_found" in errors: final = "quote_not_found"
    elif "unknown_relation" in errors: final = "unknown_relation"
    elif any(e.startswith(("domain_", "range_", "subject_", "object_")) for e in errors): final = "type_violation"
    elif "direction_error" in errors: final = "direction_error"
    elif "source_unknown" in errors: final = "source_unknown"
    elif any(e.startswith("schema_") for e in errors): final = "schema_error"
    else: final = None
    return {"id": r.get("id"), "errors": errors, "quote": quote, "final_error": final,
            "valid": final is None and r.get("status") == "accepted"}

def main():
    texts = load_texts()
    records = [json.loads(line) for line in (MODELS / "triples_llm.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    results = [validate_record(r, texts) for r in records]
    total = len(results)
    quote_confirmed = sum(1 for x in results if x["quote"] == "confirmed")
    relation_valid = sum(1 for x in results if "unknown_relation" not in x["errors"])
    type_valid = sum(1 for x in results if not any(e.startswith(("domain_", "range_", "subject_", "object_")) for e in x["errors"]))
    fully_valid = sum(1 for x in results if x["valid"])
    rejected = total - fully_valid
    by_type = {}
    for x in results:
        if x["final_error"]:
            by_type[x["final_error"]] = by_type.get(x["final_error"], 0) + 1
    payload = {
        "total": total, "schema_valid": sum(1 for r in records if REQUIRED <= set(r)),
        "quote_confirmed": quote_confirmed, "quote_share": round(quote_confirmed/total, 4),
        "relation_valid": relation_valid, "type_valid": type_valid,
        "fully_valid": fully_valid, "rejected": rejected,
        "errors_by_type": by_type, "details": results,
    }
    (RESULTS / "validation_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md = ["# Результат перевірки триплетів LLM\n",
          "| Показник | Значення |", "|---|---|",
          f"| Усього триплетів | {total} |",
          f"| Валідних за схемою | {payload['schema_valid']} |",
          f"| Підтверджених цитат | {quote_confirmed}/{total} ({payload['quote_share']:.1%}) |",
          f"| Відношень з каталогу | {relation_valid}/{total} |",
          f"| Типів domain/range без порушень | {type_valid}/{total} |",
          f"| Повністю валідних (прийнято людиною) | {fully_valid}/{total} |",
          f"| Відхилено | {rejected}/{total} |\n",
          "## Помилки за типами\n", "| Тип | Кількість |", "|---|---:|"]
    for k, v in sorted(by_type.items()): md.append(f"| `{k}` | {v} |")
    md += ["\n## Перелік відхилених триплетів\n",
           "| ID | Помилка | Деталі |", "|---|---|---|"]
    for x in results:
        if x["final_error"]:
            md.append(f"| {x['id']} | `{x['final_error']}` | {', '.join(x['errors'])} |")
    md += ["\nСкрипт: `scripts/validate_triples.py`. Повний машинний звіт: `results/validation_report.json`."]
    (RESULTS / "validation_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ["total","quote_confirmed","quote_share","relation_valid","type_valid","fully_valid","errors_by_type"]}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
