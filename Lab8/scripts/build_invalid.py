# -*- coding: utf-8 -*-
"""Створює data/kb_invalid.ttl із трьома навмисними дефектами."""
from rdflib import Graph, Literal
from kb8 import DATA, MM

def main():
    g = Graph().parse(DATA / "kb.ttl", format="turtle")
    # 1. Неправильний формат stopId.
    for o in list(g.objects(MM.Stop_Vokzal, MM.stopId)):
        g.remove((MM.Stop_Vokzal, MM.stopId, o))
    g.add((MM.Stop_Vokzal, MM.stopId, Literal("VOKZAL")))
    # 2. Відсутній стан рейсу (порушення minCount).
    for o in list(g.objects(MM.Trip_9_0800, MM.hasState)):
        g.remove((MM.Trip_9_0800, MM.hasState, o))
    # 3. Неправильний тип eventTime.
    for o in list(g.objects(MM.Congestion_Horodotska, MM.eventTime)):
        g.remove((MM.Congestion_Horodotska, MM.eventTime, o))
    g.add((MM.Congestion_Horodotska, MM.eventTime, Literal("not-a-date")))
    g.serialize(destination=DATA / "kb_invalid.ttl", format="turtle")
    print("kb_invalid.ttl:", len(g), "triples; defects=3")

if __name__ == "__main__":
    main()
