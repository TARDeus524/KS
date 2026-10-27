# -*- coding: utf-8 -*-
"""Precision/recall LLM-карти відносно експертного еталону (45 тверджень)."""
import csv, json
from pathlib import Path
import kb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"; MODELS = ROOT / "models"; RESULTS = ROOT / "results"

def main():
    gold = set()
    with open(DATA / "expert_gold.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gold.add((row["subject_id"], row["predicate_id"], row["object_id"]))
    llm = []
    for line in (MODELS / "triples_llm.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        llm.append((r["subject_id"], r["predicate_id"], r["object_id"]))
    llm_set = set(llm)
    tp = len(gold & llm_set)
    fp = len(llm_set - gold)
    fn = len(gold - llm_set)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    payload = {"gold": len(gold), "llm_unique": len(llm_set), "tp": tp, "fp": fp, "fn": fn,
               "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
               "false_positives": sorted(llm_set - gold), "false_negatives": sorted(gold - llm_set)}
    (RESULTS / "precision_recall.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# Precision / recall LLM-карти\n",
          "| Показник | Значення |", "|---|---:|",
          f"| Еталон (gold) | {len(gold)} тверджень |",
          f"| Унікальних триплетів LLM | {len(llm_set)} |",
          f"| TP | {tp} |", f"| FP | {fp} |", f"| FN | {fn} |",
          f"| Precision | {precision:.3f} |", f"| Recall | {recall:.3f} |", f"| F1 | {f1:.3f} |\n",
          "## FP (помилкові твердження LLM)\n"]
    for s, p, o in sorted(llm_set - gold):
        plabel = kb.RELATIONS[p][0] if p in kb.RELATIONS else "пов'язаний з"
        md.append(f"- {kb.CONCEPTS[s][0]} — {plabel} → {kb.CONCEPTS[o][0]}")
    md += ["\n## FN (пропущені твердження еталону)\n"]
    for s, p, o in sorted(gold - llm_set):
        md.append(f"- {kb.CONCEPTS[s][0]} — {kb.RELATIONS[p][0]} → {kb.CONCEPTS[o][0]}")
    (RESULTS / "precision_recall.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ["gold","llm_unique","tp","fp","fn","precision","recall","f1"]}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
