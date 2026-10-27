# -*- coding: utf-8 -*-
"""Конвеєр text-to-SPARQL: парсер → перевірка схеми → Fuseki LIMIT → метрики."""
import json, re, time
from pathlib import Path
import requests
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, OWL
from rdflib.plugins.sparql import prepareQuery
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

def schema_terms():
    g = Graph().parse(TESTS.parent / "data" / "kb.ttl", format="turtle")
    classes = {str(s).split("#")[-1] for s in g.subjects(RDF.type, OWL.Class) if str(s).startswith(MM_NS)}
    props = set()
    for typ in (OWL.ObjectProperty, OWL.DatatypeProperty):
        props |= {str(s).split("#")[-1] for s in g.subjects(RDF.type, typ) if str(s).startswith(MM_NS)}
    individuals = {str(s).split("#")[-1] for s in g.subjects() if str(s).startswith(MM_NS)}
    return classes | props, props, individuals

def check(q, classes_props, props, individuals):
    try:
        prepareQuery(add_prefixes(q))
        syntax = True
    except Exception:
        syntax = False
    used = set(re.findall(r"mm:([A-Za-z_][A-Za-z0-9_]*)", q))
    schema = syntax and used <= (classes_props | individuals)
    return syntax, schema, sorted(used - (classes_props | individuals))

def execute(q):
    r = requests.get(ENDPOINT, params={"query": add_limit(add_prefixes(q))},
                     headers={"Accept": "application/sparql-results+json"}, timeout=120)
    r.raise_for_status()
    return [{k: norm(v) for k, v in b.items()} for b in r.json()["results"]["bindings"]]

def canonical(rows):
    return sorted(tuple(sorted(r.items())) for r in rows)

def main():
    cp, props, inds = schema_terms()
    records = []
    for line in (TESTS / "t2s.jsonl").read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        result = {"id": item["id"], "difficulty": item["difficulty"],
                  "question": item["question"], "reference_query": item["reference_query"],
                  "expected": item["expected"], "variants": {}}
        for variant in ("before", "after"):
            q = item[f"{variant}_query"]
            syntax, schema, bad = check(q, cp, props, inds)
            rows, err = [], ""
            if syntax and schema:
                try:
                    rows = execute(q)
                except Exception as e:
                    err = str(e)[:240]
            correct = (not err) and canonical(rows) == canonical(item["expected"])
            result["variants"][variant] = {
                "query": q, "syntax": syntax, "schema": schema,
                "bad_terms": bad, "correct": correct, "error": err,
                "rows": rows,
            }
        records.append(result)

    def metric(variant, key):
        return sum(1 for r in records if r["variants"][variant][key])

    summary = {}
    for variant in ("before", "after"):
        summary[variant] = {
            "syntax": metric(variant, "syntax"),
            "schema": metric(variant, "schema"),
            "correct": metric(variant, "correct"),
            "total": len(records),
        }
    out = {"pipeline": ["prompt+schema", "LLM", "SPARQL parser", "schema check", "Fuseki LIMIT 100", "result comparison"],
           "total": len(records), "summary": summary, "records": records}
    (RESULTS / "t2s_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for r in records:
        b = r["variants"]["before"]; a = r["variants"]["after"]
        print(r["id"], "before", b["syntax"], b["schema"], b["correct"], "| after", a["syntax"], a["schema"], a["correct"])

if __name__ == "__main__":
    main()
