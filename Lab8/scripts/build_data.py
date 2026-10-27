# -*- coding: utf-8 -*-
"""Збирає RDF-сховище ЛР8 з онтології та ABox ЛР7, додає метадані й JSON-LD."""
import json
from pathlib import Path
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS, DCTERMS
from kb8 import (DATA, LAB7, MODELS, RESULTS, MM_NS, ONT, DATA_ONT, MM,
                 LOAD_DATE, VERSION)

WD = "http://www.wikidata.org/entity/"

def main():
    g = Graph()
    for prefix, ns in [
        ("mm", MM), ("rdf", RDF), ("rdfs", RDFS), ("owl", OWL), ("xsd", XSD),
        ("skos", SKOS), ("dcterms", DCTERMS),
        ("schema", URIRef("https://schema.org/")),
        ("wd", URIRef(WD)),
    ]:
        g.bind(prefix, ns)
    g.parse(LAB7 / "models" / "onto.owl", format="turtle")
    g.parse(LAB7 / "models" / "onto_data.ttl", format="turtle")
    g.add((URIRef(DATA_ONT), RDF.type, OWL.Ontology))
    g.add((URIRef(DATA_ONT), OWL.imports, URIRef(ONT)))
    g.add((URIRef(DATA_ONT), OWL.versionInfo, Literal(VERSION)))
    g.add((URIRef(DATA_ONT), DCTERMS.modified, Literal(LOAD_DATE, datatype=XSD.date)))
    g.add((URIRef(DATA_ONT), DCTERMS.source, Literal("ЛР7: models/onto.owl + models/onto_data.ttl")))
    g.add((URIRef(DATA_ONT), MM.snapshotName, Literal("Domain Knowledge Hub — Lviv mobility")))
    g.add((URIRef(DATA_ONT), MM.snapshotVersion, Literal(VERSION)))
    g.add((URIRef(DATA_ONT), MM.snapshotDate, Literal(LOAD_DATE, datatype=XSD.date)))
    # Матеріалізовані висновки HermiT із ЛР7, потрібні для запитів до класів
    # без запуску reasoner під час кожного SPARQL-запиту.
    for local, cls in [
        ("Route_9", "TransportRoute"), ("Route_25", "TransportRoute"),
        ("Route_31", "TransportRoute"),
        ("Stop_Vokzal", "InterchangeStop"), ("Stop_Vokzal", "AccessibleStop"),
        ("Stop_Rynok", "InterchangeStop"), ("Stop_Politekhnika", "AccessibleStop"),
        ("Seg_Vokzal_Rynok", "CongestedSegment"), ("Trip_9_0800", "DelayedTrip"),
    ]:
        g.add((MM[local], RDF.type, MM[cls]))

    kb_ttl = DATA / "kb.ttl"
    g.serialize(destination=kb_ttl, format="turtle")
    g.serialize(destination=DATA / "kb.jsonld", format="json-ld", indent=2)

    entities = set()
    for s, p, o in g.triples((None, RDF.type, None)):
        if isinstance(s, URIRef) and not str(s).startswith("nodeID://"):
            entities.add(str(s))
    jsonld = json.loads((DATA / "kb.jsonld").read_text(encoding="utf-8"))
    if isinstance(jsonld, list):
        nodes = jsonld
    else:
        nodes = jsonld.get("@graph", [jsonld])
    jsonld_entities = {
        n.get("@id") for n in nodes
        if isinstance(n, dict) and n.get("@id") and not n["@id"].startswith("_:")
        and n.get("@type")
    }
    stats = {
        "triples": len(g),
        "subjects": len(set(g.subjects())),
        "entities_typed": len(entities),
        "jsonld_nodes": len(nodes),
        "jsonld_entities": len(jsonld_entities),
        "classes": len(set(g.subjects(RDF.type, OWL.Class))),
        "individuals": 52,
        "version": VERSION,
        "date": LOAD_DATE,
    }
    (RESULTS / "data_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"entities sample: {sorted(jsonld_entities)[:5]}")

if __name__ == "__main__":
    main()
