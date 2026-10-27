# Лабораторна робота №7 — онтологія в Protégé

Предметна область: «Інтелектуальне управління міською мобільністю».
Виконавець: Невмержицький Максим Миколайович, група ФЕІ-46с.

## Що є в роботі

- `models/onto.owl` — OWL 2 TBox у Turtle; `models/onto.rdf` — та сама онтологія в RDF/XML для Protégé.
- `models/onto_data.ttl` / `.rdf` — ABox на 52 індивіди.
- `models/class_table.csv` — 58 класів із genus + differentia.
- `models/properties.csv` — 48 object properties і 25 data properties.
- `models/situations.csv` — 5 шаблонів ситуацій із прив’язкою елементів до класів.
- `models/llm_draft.ttl` — чернетка онтології від LLM.
- `tests/cq_sparql/` — 10 CQ-запитів; `tests/situation_queries/` — 2 перевірки ситуацій.
- `build/` — merged RDF, inferred RDF, навмисно суперечливий RDF.
- `results/` — машинні результати CQ, ситуацій, HermiT.
- `docs/` — журнал HermiT, оцінювання, протокол LLM, перевірка Protégé.
- `claims/` — 18 тверджень (12 verified, 6 rejected).
- `scripts/` — відтворювані скрипти генерації, перевірки, візуалізації та звіту.

## Відтворення

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

python scripts/build_ontology.py
python scripts/run_reasoner.py
python scripts/evaluate_ontology.py
python scripts/visualize.py
python scripts/make_report.py
```

Потрібні Java 11+ (HermiT), Graphviz (`dot`) і LibreOffice (`soffice`).
Мережа під час відтворення не потрібна.

## Ключові результати

- 58 класів, 48 object properties, 25 data properties, 52 індивіди.
- HermiT: онтологія консистентна; 165 виведених type-тверджень, 21 property-твердження.
- 6 змістовних членств у визначених класах: InterchangeStop ×2, AccessibleStop ×2, CongestedSegment, DelayedTrip.
- Навмисна суперечність Bus/Tram виявлена `InconsistentOntologyException` і локалізована.
- CQ: експертна онтологія 10/10, LLM-чернетка 2/10.
- 5/5 ситуацій валідовано; S1 і S3 перевірено SPARQL-запитами.
- 7 OntoClean-перевірок; 18 тверджень, з них 12 підтверджено.

## Технічне зауваження

HermiT підтримує лише типи з OWL 2 datatype map. Поля GTFS із датами та часом збережено як `xsd:string`
(`YYYYMMDD` і `HH:MM:SS`), щоб уникнути `UnsupportedDatatypeException`; для повних дат використано `xsd:dateTime`.

## Звіт

`СЗтУЗ_Лаб7_Невмержицький_Максим-ФЕІ46.docx`, `.odt`, `.pdf`.
