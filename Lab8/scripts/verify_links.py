# -*- coding: utf-8 -*-
"""V1-перевірка зовнішніх QID через Wikidata API."""
import json
import requests
from rdflib import Graph
from kb8 import DATA, RESULTS, MM
from rdflib.namespace import SKOS

WD = "http://www.wikidata.org/entity/"
UA = "KnowledgeStorageLab/1.0 (educational; Lviv University)"

def main():
    rows = []
    for filename in ("links.ttl", "links_rejected.ttl"):
        g = Graph().parse(DATA / filename, format="turtle")
        for s, p, o in g.triples((None, None, None)):
            if p not in (SKOS.exactMatch, SKOS.closeMatch):
                continue
            qid = str(o).replace(WD, "")
            status = g.value(s, MM.linkStatus)
            conf = g.value(s, MM.linkConfidence)
            rows.append({"local": str(s).split("#")[-1], "qid": qid,
                         "relation": "exactMatch" if p == SKOS.exactMatch else "closeMatch",
                         "status": str(status), "confidence": str(conf),
                         "external": str(o), "source": "https://www.wikidata.org/wiki/" + qid})
    ids = "|".join(sorted({r["qid"] for r in rows}))
    r = requests.get("https://www.wikidata.org/w/api.php", params={
        "action": "wbgetentities", "ids": ids, "props": "labels|descriptions",
        "languages": "en|uk", "format": "json"}, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    entities = r.json().get("entities", {})
    for row in rows:
        ent = entities.get(row["qid"], {})
        labels = ent.get("labels", {})
        descs = ent.get("descriptions", {})
        row["label_en"] = labels.get("en", {}).get("value", "")
        row["label_uk"] = labels.get("uk", {}).get("value", "")
        row["description_en"] = descs.get("en", {}).get("value", "")
        row["api_ok"] = bool(row["label_en"])
        if row["status"] == "verdict":
            pass
    out = {"checked_at": "2026-10-27", "source": "Wikidata API wbgetentities",
           "items": rows,
           "verified": sum(1 for x in rows if x["status"] == "verified"),
           "rejected": sum(1 for x in rows if x["status"] == "rejected")}
    (RESULTS / "wikidata_verification.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
