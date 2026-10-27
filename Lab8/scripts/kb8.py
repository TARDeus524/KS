# -*- coding: utf-8 -*-
"""Спільні константи та допоміжні функції ЛР8."""
from pathlib import Path
from rdflib import Namespace, URIRef

ROOT = Path(__file__).resolve().parents[1]
LAB7 = ROOT.parent / "Lab7"
DATA = ROOT / "data"
DOCS = ROOT / "docs"
QUERIES = ROOT / "queries"
SHAPES = ROOT / "shapes"
SCRIPTS = ROOT / "scripts"
RESULTS = ROOT / "results"
TESTS = ROOT / "tests"
LLM = ROOT / "llm_log"
CLAIMS = ROOT / "claims"
MODELS = ROOT / "models"

MM_NS = "https://knowledge.uni.lviv.ua/mobility#"
ONT = "https://knowledge.uni.lviv.ua/mobility"
DATA_ONT = "https://knowledge.uni.lviv.ua/mobility/data"
MM = Namespace(MM_NS)

FUSEKI_VERSION = "4.10.0"
FUSEKI_URL = "http://127.0.0.1:3030"
DATASET = "ds"
LOAD_DATE = "2026-10-27"
VERSION = "1.0"

PREFIXES = """PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX schema: <https://schema.org/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
"""

# 15 питань text-to-SPARQL: еталон, слабка чернетка та покращена чернетка.
T2S = [
    {
        "id": "T2S01", "difficulty": "easy",
        "question": "Які зупинки є пересадочними?",
        "reference": "SELECT DISTINCT ?stop WHERE { ?stop a mm:InterchangeStop . } ORDER BY ?stop",
        "before": "SELECT DISTINCT ?stop WHERE { ?stop mm:hasInterchange true . } ORDER BY ?stop",
        "after": "SELECT DISTINCT ?stop WHERE { ?stop a mm:InterchangeStop . } ORDER BY ?stop",
    },
    {
        "id": "T2S02", "difficulty": "easy",
        "question": "Які маршрути обслуговують зупинку «Вокзал»?",
        "reference": "SELECT DISTINCT ?route WHERE { ?route mm:servesStop mm:Stop_Vokzal . } ORDER BY ?route",
        "before": "SELECT DISTINCT ?route WHERE { ?route mm:servedByRoute mm:Stop_Vokzal . } ORDER BY ?route",
        "after": "SELECT DISTINCT ?route WHERE { ?route mm:servesStop mm:Stop_Vokzal . } ORDER BY ?route",
    },
    {
        "id": "T2S03", "difficulty": "medium",
        "question": "Які рейси мають стан затримки?",
        "reference": "SELECT DISTINCT ?trip WHERE { ?trip mm:hasState ?state . ?state a mm:DelayedState . } ORDER BY ?trip",
        "before": "SELECT DISTINCT ?trip WHERE { ?trip mm:hasState mm:OnTimeState . } ORDER BY ?trip",
        "after": "SELECT DISTINCT ?trip WHERE { ?trip mm:hasState ?state . ?state a mm:DelayedState . } ORDER BY ?trip",
    },
    {
        "id": "T2S04", "difficulty": "easy",
        "question": "Які зупинки доступні для маломобільних пасажирів?",
        "reference": "SELECT DISTINCT ?stop WHERE { ?stop mm:wheelchairAccessible true . } ORDER BY ?stop",
        "before": "SELECT DISTINCT ?stop WHERE { ?stop mm:wheelchairAccessible \"true\" . } ORDER BY ?stop",
        "after": "SELECT DISTINCT ?stop WHERE { ?stop mm:wheelchairAccessible true . } ORDER BY ?stop",
    },
    {
        "id": "T2S05", "difficulty": "medium",
        "question": "Які маршрути мають інтервал руху не більше 10 хвилин?",
        "reference": "SELECT DISTINCT ?route WHERE { ?f a mm:Frequency ; mm:frequencyOfRoute ?route ; mm:headwayMinutes ?h . FILTER(?h <= 10) } ORDER BY ?route",
        "before": "SELECT DISTINCT ?route WHERE { ?f a mm:Frequency ; mm:frequencyOfRoute ?route ; mm:headwayMinutes ?h . FILTER(?h < 10) } ORDER BY ?route",
        "after": "SELECT DISTINCT ?route WHERE { ?f a mm:Frequency ; mm:frequencyOfRoute ?route ; mm:headwayMinutes ?h . FILTER(?h <= 10) } ORDER BY ?route",
    },
    {
        "id": "T2S06", "difficulty": "easy",
        "question": "Які рейси виконуються автобусами?",
        "reference": "SELECT DISTINCT ?trip WHERE { ?trip mm:usesVehicle ?v . ?v a mm:Bus . } ORDER BY ?trip",
        "before": "SELECT DISTINCT ?trip WHERE { ?trip a mm:BusTrip . } ORDER BY ?trip",
        "after": "SELECT DISTINCT ?trip WHERE { ?trip mm:usesVehicle ?v . ?v a mm:Bus . } ORDER BY ?trip",
    },
    {
        "id": "T2S07", "difficulty": "medium",
        "question": "Скільки рейсів має кожен маршрут?",
        "reference": "SELECT ?route (COUNT(?trip) AS ?trips) WHERE { ?trip mm:tripOfRoute ?route . } GROUP BY ?route ORDER BY DESC(?trips) ?route",
        "before": "SELECT ?route (COUNT(?trip) AS ?trips) WHERE { ?trip mm:tripOfRoute ?route . } ORDER BY DESC(?trips)",
        "after": "SELECT ?route (COUNT(?trip) AS ?trips) WHERE { ?trip mm:tripOfRoute ?route . } GROUP BY ?route ORDER BY DESC(?trips) ?route",
    },
    {
        "id": "T2S08", "difficulty": "easy",
        "question": "Які зупинки не доступні для маломобільних пасажирів?",
        "reference": "SELECT DISTINCT ?stop WHERE { ?stop mm:wheelchairAccessible false . } ORDER BY ?stop",
        "before": "SELECT DISTINCT ?stop WHERE { ?stop mm:accessible false . } ORDER BY ?stop",
        "after": "SELECT DISTINCT ?stop WHERE { ?stop mm:wheelchairAccessible false . } ORDER BY ?stop",
    },
    {
        "id": "T2S09", "difficulty": "medium",
        "question": "Які рейси прямують від «Вокзалу» до «Площі Ринок»?",
        "reference": "SELECT DISTINCT ?trip WHERE { ?trip mm:startsAt mm:Stop_Vokzal ; mm:endsAt mm:Stop_Rynok . } ORDER BY ?trip",
        "before": "SELECT DISTINCT ?trip WHERE { ?trip mm:startsAt mm:Stop_Vokzal . } ORDER BY ?trip",
        "after": "SELECT DISTINCT ?trip WHERE { ?trip mm:startsAt mm:Stop_Vokzal ; mm:endsAt mm:Stop_Rynok . } ORDER BY ?trip",
    },
    {
        "id": "T2S10", "difficulty": "medium",
        "question": "Який маршрут рекомендовано пасажиру Passenger_P01?",
        "reference": "SELECT DISTINCT ?route WHERE { ?rec mm:forPassenger mm:Passenger_P01 ; mm:recommends ?route . } ORDER BY ?route",
        "before": "SELECT DISTINCT ?route WHERE { mm:Passenger_P01 mm:forPassenger ?rec . ?rec mm:recommends ?route . } ORDER BY ?route",
        "after": "SELECT DISTINCT ?route WHERE { ?rec mm:forPassenger mm:Passenger_P01 ; mm:recommends ?route . } ORDER BY ?route",
    },
    {
        "id": "T2S11", "difficulty": "medium",
        "question": "Яка затримка рейсу Trip_9_0800 у хвилинах?",
        "reference": "SELECT ?minutes WHERE { ?d a mm:Delay ; mm:measurementOf mm:Trip_9_0800 ; mm:delayMinutes ?minutes . }",
        "before": "SELECT ?minutes WHERE { mm:Trip_9_0800 mm:travelTimeMinutes ?minutes . }",
        "after": "SELECT ?minutes WHERE { ?d a mm:Delay ; mm:measurementOf mm:Trip_9_0800 ; mm:delayMinutes ?minutes . }",
    },
    {
        "id": "T2S12", "difficulty": "medium",
        "question": "Яка ділянка і який рейс зазнали впливу затору?",
        "reference": "SELECT DISTINCT ?segment ?trip WHERE { ?segment mm:hasEvent mm:Congestion_Horodotska . mm:Congestion_Horodotska mm:affectsTrip ?trip . } ORDER BY ?segment ?trip",
        "before": "SELECT DISTINCT ?segment ?trip WHERE { ?segment mm:hasEvent ?event . OPTIONAL { ?event mm:affectsTrip ?trip } } ORDER BY ?segment ?trip",
        "after": "SELECT DISTINCT ?segment ?trip WHERE { ?segment mm:hasEvent mm:Congestion_Horodotska . mm:Congestion_Horodotska mm:affectsTrip ?trip . } ORDER BY ?segment ?trip",
    },
    {
        "id": "T2S13", "difficulty": "hard",
        "question": "Який маршрут обслуговує найбільше зупинок?",
        "reference": "SELECT ?route (COUNT(DISTINCT ?stop) AS ?stops) WHERE { ?route mm:servesStop ?stop . } GROUP BY ?route ORDER BY DESC(?stops) ?route LIMIT 1",
        "before": "SELECT ?route ?stop WHERE { ?route mm:servesStop ?stop . } ORDER BY ?route",
        "after": "SELECT ?route (COUNT(DISTINCT ?stop) AS ?stops) WHERE { ?route mm:servesStop ?stop . } GROUP BY ?route ORDER BY DESC(?stops) ?route LIMIT 1",
    },
    {
        "id": "T2S14", "difficulty": "hard",
        "question": "Які зупинки обслуговують і маршрут 9, і маршрут 31?",
        "reference": "SELECT DISTINCT ?stop WHERE { mm:Route_9 mm:servesStop ?stop . mm:Route_31 mm:servesStop ?stop . } ORDER BY ?stop",
        "before": "SELECT DISTINCT ?stop WHERE { ?stop mm:servedByRoute mm:Route_9 ; mm:servedByRoute mm:Route_31 . } ORDER BY ?stop",
        "after": "SELECT DISTINCT ?stop WHERE { mm:Route_9 mm:servesStop ?stop . mm:Route_31 mm:servesStop ?stop . } ORDER BY ?stop",
    },
    {
        "id": "T2S15", "difficulty": "medium",
        "question": "Які джерела даних описують транспортну мережу Львова?",
        "reference": "SELECT DISTINCT ?ds WHERE { ?ds mm:datasetDescribes mm:Network_Lviv . } ORDER BY ?ds",
        "before": "SELECT DISTINCT ?ds WHERE { ?ds mm:describes mm:Network_Lviv . } ORDER BY ?ds",
        "after": "SELECT DISTINCT ?ds WHERE { ?ds mm:datasetDescribes mm:Network_Lviv . } ORDER BY ?ds",
    },
]
