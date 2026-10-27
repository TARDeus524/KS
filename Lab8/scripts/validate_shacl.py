# -*- coding: utf-8 -*-
"""Запускає pySHACL для валідного й дефектного наборів."""
import json
from pathlib import Path
from rdflib import Graph
from rdflib.namespace import RDF
from pyshacl import validate
from kb8 import DATA, SHAPES, RESULTS
from rdflib.namespace import SH

def run(data_path, prefix):
    data = Graph().parse(data_path, format="turtle")
    shapes = Graph().parse(SHAPES / "shapes.ttl", format="turtle")
    conforms, report, text = validate(
        data, shacl_graph=shapes, inference="none",
        abort_on_first=False, allow_infos=False, allow_warnings=False,
    )
    (RESULTS / f"{prefix}_report.ttl").write_text(report.serialize(format="turtle"), encoding="utf-8")
    (RESULTS / f"{prefix}_report.txt").write_text(text, encoding="utf-8")
    violations = []
    for result in report.objects(None, SH.result):
        def one(pred):
            v = report.value(result, pred)
            return str(v) if v is not None else ""
        violations.append({
            "focus": one(SH.focusNode),
            "path": one(SH.resultPath),
            "message": one(SH.resultMessage),
            "severity": one(SH.resultSeverity),
        })
    return {"conforms": conforms, "violations": violations, "report_text": text}

def main():
    valid = run(DATA / "kb.ttl", "shacl_valid")
    invalid = run(DATA / "kb_invalid.ttl", "shacl_invalid")
    shapes = Graph().parse(SHAPES / "shapes.ttl", format="turtle")
    summary = {
        "shapes": len(set(shapes.subjects(RDF.type, SH.NodeShape))),
        "property_shapes": len(set(shapes.objects(None, SH.property))),
        "constraint_triples": len([p for p in shapes.predicates() if str(p).startswith(str(SH))]),
        "valid": {"conforms": valid["conforms"], "violations": len(valid["violations"])},
        "invalid": {"conforms": invalid["conforms"], "violations": len(invalid["violations"]),
                    "items": invalid["violations"]},
    }
    (RESULTS / "shacl_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "invalid"}, ensure_ascii=False, indent=2))
    print(json.dumps(summary["invalid"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
