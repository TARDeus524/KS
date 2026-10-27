# ЛР8 — RDF-сховище та SPARQL-запити

Проєкт продовжує ЛР7: онтологія та індивіди експортовані в `data/kb.ttl`, завантажені в Apache Jena Fuseki, перевірені SHACL і використані для text-to-SPARQL.

## Структура

```
data/        kb.ttl, kb.jsonld, links.ttl, links_rejected.ttl, kb_invalid.ttl
queries/     11 SPARQL-запитів (SELECT, ASK, CONSTRUCT, aggregation, OPTIONAL, FILTER, path, federated)
shapes/      shapes.ttl (7 NodeShape, 26 property shapes)
scripts/     build_data.py, build_links.py, build_invalid.py, run_queries.py, validate_shacl.py, run_t2s.py, make_report.py
tests/       t2s.jsonl (15 питань)
docs/        load_log, sparql_results, shacl_report, t2s_eval, links_verification, llm_protocol
results/     фактичні результати, звіти SHACL, метрики
claims/      claims.csv, summary.md
llm_log/     підказки, сирий вихід, рішення
```

## Залежності

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Потрібні Java 11+ для Fuseki/HermiT, Apache Jena Fuseki 4.10.0, Graphviz і LibreOffice для звіту.

## Відтворення

```bash
# 1. Дані
python scripts/build_data.py
python scripts/build_links.py
python scripts/build_invalid.py

# 2. Fuseki
FUSEKI_HOME=/tmp/opencode/fuseki/apache-jena-fuseki-4.10.0
"$FUSEKI_HOME/fuseki-server" --mem --update --port 3030 /ds
curl -X POST -H 'Content-Type: text/turtle' --data-binary @data/kb.ttl 'http://127.0.0.1:3030/ds/data?default'
curl -X POST -H 'Content-Type: text/turtle' --data-binary @data/links.ttl 'http://127.0.0.1:3030/ds/data?default'
curl -X POST -H 'Content-Type: text/turtle' --data-binary @data/links_rejected.ttl 'http://127.0.0.1:3030/ds/data?default'

# 3. Проксі Wikidata (лише додає User-Agent)
python scripts/wikidata_proxy.py 3031 &

# 4. Запити, SHACL, T2S
python scripts/run_queries.py
python scripts/validate_shacl.py
python scripts/build_t2s.py
python scripts/run_t2s.py

# 5. Звіт
python scripts/visualize.py
python scripts/build_docs.py
python scripts/make_report.py
```

## Фактичні результати

- `data/kb.ttl`: 1146 триплетів; разом із links — **1206** у Fuseki.
- JSON-LD: 185 типізованих сутностей.
- SHACL: валідний набір — 0 порушень; дефектний — 3.
- T2S: до покращення 1/15 правильних, після — 15/15.
- Wikidata: 7 підтверджених, 2 відхилених; federated-запит — 7 рядків.

## Примітки

- `xsd:date`/`xsd:time` у ЛР7 замінено на `xsd:string` через обмеження HermiT; це не впливає на SPARQL і SHACL.
- Для Wikidata використано проксі, бо Fuseki/Jena без User-Agent отримує 403; upstream залишається Wikidata.
- Усі ключі API відсутні; звіт не містить персональних даних.
