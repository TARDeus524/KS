# -*- coding: utf-8 -*-
"""Формує data/links.ttl — зв’язки з Wikidata з рівнем впевненості."""
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, SKOS, DCTERMS, OWL
from kb8 import DATA, MM, LOAD_DATE

WD = "http://www.wikidata.org/entity/"

LINKS = [
    # local, external, predicate, confidence, status, rationale, external label
    ("Network_Lviv", "Q36036", "exactMatch", "0.97", "verified",
     "Місто Львів: збіг назви, адміністративного центру та предметної області; перевірено опис Wikidata.",
     "Lviv"),
    ("GTFSDataset", "Q5532250", "exactMatch", "0.98", "verified",
     "General Transit Feed Specification: точний збіг стандарту GTFS, на який посилається онтологія.",
     "General Transit Feed Specification"),
    ("Bus", "Q5638", "closeMatch", "0.95", "verified",
     "Клас Bus відповідає загальному поняттю bus; у Wikidata це транспортний засіб, у нас — клас рухомого складу.",
     "bus"),
    ("Tram", "Q3407658", "closeMatch", "0.90", "verified",
     "Клас Tram відповідає поняттю tram; Wikidata описує транспортний засіб, локальний клас — тип ТЗ.",
     "tram"),
    ("Stop", "Q548662", "closeMatch", "0.88", "verified",
     "public transport stop: локальний клас Stop охоплює зупинки громадського транспорту.",
     "public transport stop"),
    ("TransportSystem", "Q178512", "closeMatch", "0.80", "verified",
     "public transport: локальний TransportSystem ширший за послугу, тому closeMatch, не exactMatch.",
     "public transport"),
    ("GTFSDataset", "Q113379415", "closeMatch", "0.72", "verified",
     "GTFS feed: локальний клас описує набір даних, а Wikidata — конкретний feed; зв’язок збережено як closeMatch.",
     "General Transit Feed Specification feed"),
    # Навмисно відхилений кандидат: адміністративна одиниця не є транспортною мережею.
    ("Network_Lviv", "Q164193", "closeMatch", "0.30", "rejected",
     "Lviv Oblast — адміністративна область, а не транспортна мережа міста; кандидат відхилено після V1.",
     "Lviv Oblast"),
    # Навмисно відхилений кандидат: автобусний термінал не тотожний зупинці «Вокзал».
    ("Stop_Vokzal", "Q4271066", "closeMatch", "0.25", "rejected",
     "Lviv Bus terminal — окремий автобусний термінал, а не залізнична/пересадочна зупинка Вокзал; sameAs був би хибним.",
     "Lviv Bus terminal"),
]

def make_graph(links):
    g = Graph()
    for prefix, ns in [("mm", MM), ("rdf", RDF), ("rdfs", RDFS), ("xsd", XSD),
                       ("skos", SKOS), ("dcterms", DCTERMS), ("owl", OWL),
                       ("wd", URIRef(WD))]:
        g.bind(prefix, ns)
    for local, ext, rel, conf, status, rationale, label in links:
        s = MM[local]
        o = URIRef(WD + ext)
        pred = SKOS.exactMatch if rel == "exactMatch" else SKOS.closeMatch
        g.add((s, pred, o))
        g.add((s, MM.linkConfidence, Literal(conf, datatype=XSD.decimal)))
        g.add((s, MM.linkStatus, Literal(status)))
        g.add((s, MM.linkExternalLabel, Literal(label)))
        g.add((s, MM.linkVerifiedAt, Literal(LOAD_DATE, datatype=XSD.date)))
        g.add((s, RDFS.comment, Literal(rationale, lang="uk")))
        g.add((s, DCTERMS.source, URIRef("https://www.wikidata.org/wiki/" + ext)))
    return g

def main():
    verified = [x for x in LINKS if x[4] == "verified"]
    rejected = [x for x in LINKS if x[4] == "rejected"]
    gv = make_graph(verified)
    gr = make_graph(rejected)
    gv.serialize(destination=DATA / "links.ttl", format="turtle")
    gr.serialize(destination=DATA / "links_rejected.ttl", format="turtle")
    print(f"links.ttl: {len(gv)} triples, {len(verified)} verified links")
    print(f"links_rejected.ttl: {len(gr)} triples, {len(rejected)} rejected links")

if __name__ == "__main__":
    main()
