# Журнал завантаження RDF-сховища

## Середовище

| Параметр | Значення |
|---|---|
| Дата завантаження | 2026-10-27 |
| Триплстор | Apache Jena Fuseki 4.10.0 |
| Dataset | `ds` (in-memory, `/ds`) |
| Endpoint | `http://127.0.0.1:3030/ds/query` |
| Java | OpenJDK 11.0.32.1 |
| Версія графа | 1.0 |
| Дата версії | 2026-10-27 |

## Файли

| Файл | Триплети | Призначення |
|---|---:|---|
| `data/kb.ttl` | 1146 | TBox ЛР7 + ABox + матеріалізовані типи + метадані |
| `data/links.ttl` | 47 | 7 підтверджених зв’язків із Wikidata |
| `data/links_rejected.ttl` | 14 | 2 відхилені кандидати (audit trail) |
| `data/kb.jsonld` | 185 типізованих сутностей | JSON-LD-версія для ≥ 20 сутностей |

## Команди

```bash
# 1. Запуск Fuseki
FUSEKI_HOME=/tmp/opencode/fuseki/apache-jena-fuseki-4.10.0
"$FUSEKI_HOME/fuseki-server" --mem --update --port 3030 /ds

# 2. Завантаження
curl -X POST -H 'Content-Type: text/turtle' \
  --data-binary @data/kb.ttl 'http://127.0.0.1:3030/ds/data?default'
curl -X POST -H 'Content-Type: text/turtle' \
  --data-binary @data/links.ttl 'http://127.0.0.1:3030/ds/data?default'
curl -X POST -H 'Content-Type: text/turtle' \
  --data-binary @data/links_rejected.ttl 'http://127.0.0.1:3030/ds/data?default'

# 3. COUNT
curl -G 'http://127.0.0.1:3030/ds/query' \
  --data-urlencode 'query=SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }' \
  -H 'Accept: application/sparql-results+json'
```

## Результат COUNT

```json
{"count": "1206"}
```

Після чистого `DELETE` і повторного завантаження трьох файлів Fuseki повертає **1206** триплетів.
Різниця з сумою файлів (1146+47+14=1207) пояснюється дедуплікацією однакових трійок у default graph.

## Префікси

`mm:`, `rdf:`, `rdfs:`, `owl:`, `xsd:`, `skos:`, `dcterms:`, `schema:`, `wd:`, `wdt:`.
Префікс `mm:` відповідає `https://knowledge.uni.lviv.ua/mobility#`; `wd:` — `http://www.wikidata.org/entity/`.
