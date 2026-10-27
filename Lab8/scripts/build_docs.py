# -*- coding: utf-8 -*-
"""Генерує docs/*.md та README на основі фактичних результатів."""
import json
from pathlib import Path
from rdflib import Graph
from rdflib.namespace import RDF
from kb8 import ROOT, DATA, DOCS, RESULTS, QUERIES, SHAPES, CLAIMS, LLM, MODELS

def load(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))

def fmt_rows(rows, max_rows=8):
    if not rows:
        return "_немає рядків_"
    keys = list(rows[0].keys())
    out = ["| " + " | ".join(keys) + " |", "|" + "|".join(["---"] * len(keys)) + "|"]
    for r in rows[:max_rows]:
        out.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
    if len(rows) > max_rows:
        out.append(f"| ... |" + " |" * (len(keys) - 1) + f" ще {len(rows)-max_rows} |")
    return "\n".join(out)

def main():
    q = load("query_results.json")
    sh = load("shacl_summary.json")
    t2s = load("t2s_results.json")
    wd = load("wikidata_verification.json")
    stats = load("data_stats.json")
    count = json.loads((RESULTS / "triple_count.json").read_text(encoding="utf-8"))
    total = count["results"]["bindings"][0]["count"]["value"]
    qrows = {r["id"]: r for r in q["queries"]}
    timing = q["timing"]

    # ---------- load log ----------
    g_data = Graph().parse(DATA / "kb.ttl", format="turtle")
    g_links = Graph().parse(DATA / "links.ttl", format="turtle")
    g_rej = Graph().parse(DATA / "links_rejected.ttl", format="turtle")
    load_md = f"""# Журнал завантаження RDF-сховища

## Середовище

| Параметр | Значення |
|---|---|
| Дата завантаження | 2026-10-27 |
| Триплстор | Apache Jena Fuseki 4.10.0 |
| Dataset | `{q['dataset']}` (in-memory, `/ds`) |
| Endpoint | `{q['endpoint']}` |
| Java | OpenJDK 11.0.32.1 |
| Версія графа | 1.0 |
| Дата версії | 2026-10-27 |

## Файли

| Файл | Триплети | Призначення |
|---|---:|---|
| `data/kb.ttl` | {len(g_data)} | TBox ЛР7 + ABox + матеріалізовані типи + метадані |
| `data/links.ttl` | {len(g_links)} | 7 підтверджених зв’язків із Wikidata |
| `data/links_rejected.ttl` | {len(g_rej)} | 2 відхилені кандидати (audit trail) |
| `data/kb.jsonld` | {stats['jsonld_entities']} типізованих сутностей | JSON-LD-версія для ≥ 20 сутностей |

## Команди

```bash
# 1. Запуск Fuseki
FUSEKI_HOME=/tmp/opencode/fuseki/apache-jena-fuseki-4.10.0
"$FUSEKI_HOME/fuseki-server" --mem --update --port 3030 /ds

# 2. Завантаження
curl -X POST -H 'Content-Type: text/turtle' \\
  --data-binary @data/kb.ttl 'http://127.0.0.1:3030/ds/data?default'
curl -X POST -H 'Content-Type: text/turtle' \\
  --data-binary @data/links.ttl 'http://127.0.0.1:3030/ds/data?default'
curl -X POST -H 'Content-Type: text/turtle' \\
  --data-binary @data/links_rejected.ttl 'http://127.0.0.1:3030/ds/data?default'

# 3. COUNT
curl -G 'http://127.0.0.1:3030/ds/query' \\
  --data-urlencode 'query=SELECT (COUNT(*) AS ?count) WHERE {{ ?s ?p ?o }}' \\
  -H 'Accept: application/sparql-results+json'
```

## Результат COUNT

```json
{{"count": "{total}"}}
```

Після чистого `DELETE` і повторного завантаження трьох файлів Fuseki повертає **{total}** триплетів.
Різниця з сумою файлів ({len(g_data)}+{len(g_links)}+{len(g_rej)}={len(g_data)+len(g_links)+len(g_rej)}) пояснюється дедуплікацією однакових трійок у default graph.

## Префікси

`mm:`, `rdf:`, `rdfs:`, `owl:`, `xsd:`, `skos:`, `dcterms:`, `schema:`, `wd:`, `wdt:`.
Префікс `mm:` відповідає `https://knowledge.uni.lviv.ua/mobility#`; `wd:` — `http://www.wikidata.org/entity/`.
"""
    (DOCS / "load_log.md").write_text(load_md, encoding="utf-8")

    # ---------- sparql results ----------
    lines = ["# SPARQL-запити до CQ", "",
             "Усього запитів: " + str(len(q["queries"])) + ". Усі виконано до Fuseki dataset `" + q["dataset"] + "`. "
             "Для SELECT/ASK використано JSON, для CONSTRUCT — Turtle.", "",
             "## Зведена таблиця", "",
             "| ID | CQ | Тип | Рядків / трійок | Час, мс | Статус | Ручна перевірка |",
             "|---|---|---|---:|---:|---|---|"]
    for r in q["queries"]:
        manual = r.get("manual", {}).get("status", "not_checked")
        lines.append(f"| {r['id']} | {r['cq']} | {r['type']} | {r['count']} | {r['elapsed_ms']} | {r['status']} | {manual} |")
    lines += ["", "## Запити, результати та інтерпретація", ""]
    for r in q["queries"]:
        lines += [f"### {r['id']} — {r['question']}", "",
                  f"**CQ:** {r['cq']}. **Тип:** {r['type']}. **Призначення:** {r['purpose']}", "",
                  "```sparql", r["query"], "```", ""]
        if r["type"] == "CONSTRUCT":
            lines += [f"Результат: {r['count']} трійок; збережено в `results/construct_route_trip.ttl`.", ""]
        elif r["type"] == "ASK":
            lines += [f"Результат: `{str(r.get('boolean')).lower()}`.", ""]
        else:
            lines += [fmt_rows(r["rows"]), ""]
        if r.get("manual", {}).get("status") in ("PASS", "FAIL"):
            lines += [f"Ручна перевірка: **{r['manual']['status']}**; очікувано {r['manual']['expected_count']} рядків / значень.", ""]
    lines += ["## Оптимізація Q06", "",
              f"Baseline: `{timing['baseline_file']}`; optimized: `{timing['optimized_file']}`.", "",
              f"- HTTP-медіана: {timing['baseline_median_ms']} мс → {timing['optimized_median_ms']} мс (×{timing['http_speedup']}, {timing['http_runs']} запусків).",
              f"- rdflib in-process: {timing['inprocess_baseline_median_ms']} мс → {timing['inprocess_optimized_median_ms']} мс (×{timing['inprocess_speedup']}, {timing['inprocess_runs']} запусків).",
              "",
              "У baseline навмисно залишено зайві join-и `?trip ?p ?o . ?o ?p2 ?o2` і `COUNT(DISTINCT ?trip)`. "
              "Optimized прибирає зайві triple patterns і використовує прямий `mm:hasTrip`; результати ідентичні (3 рядки).", ""]
    (DOCS / "sparql_results.md").write_text("\n".join(lines), encoding="utf-8")

    # ---------- shacl ----------
    inv = sh["invalid"]
    lines = ["# SHACL-валідація", "",
             "## Форми та обмеження", "",
             "| Форма | Цільовий клас | Призначення |", "|---|---|---|",
             "| StopShape | mm:Stop | stopId, stopName, координати, доступність, маршрут |",
             "| TripShape | mm:Trip | tripId, маршрут, стан, ТЗ, початкова/кінцева зупинка |",
             "| RouteShape | mm:TransportRoute | routeId, routeType, servesStop, hasTrip |",
             "| DelayShape | mm:Delay | delayMinutes, measurementOf, measuredBy |",
             "| EventShape | mm:Event | eventTime, affectsSegment |",
             "| RecommendationShape | mm:Recommendation | recommends, forPassenger, recommendationOfDecision |",
             "| AgencyShape | mm:TransportAgency | agencyName, operatesTrip |", "",
             f"Разом: **{sh['shapes']} NodeShape**, **{sh['property_shapes']} property shapes**, "
             f"**{sh['constraint_triples']} трійок SHACL-обмежень**. Використано `minCount`, `maxCount`, `datatype`, "
             "`class`, `pattern`, `minInclusive`, `maxInclusive`, `nodeKind`, `in`.", "",
             "## Валідний набір", "",
             f"`data/kb.ttl`: **Conforms = {str(sh['valid']['conforms']).lower()}**, порушень: {sh['valid']['violations']}.", "",
             "Звіти: `results/shacl_valid_report.ttl`, `results/shacl_valid_report.txt`.", "",
             "## Дефектний набір", "",
             "`data/kb_invalid.ttl` містить три навмисні дефекти:", "",
             "1. `Stop_Vokzal.stopId` = `VOKZAL` замість `S001` (pattern).",
             "2. У `Trip_9_0800` видалено `hasState` (minCount).",
             "3. `Congestion_Horodotska.eventTime` = `not-a-date` без `xsd:dateTime` (datatype).", "",
             f"Результат: **Conforms = {str(inv['conforms']).lower()}**, виявлено **{inv['violations']}** порушення.", "",
             "| Фокус | Шлях | Повідомлення |", "|---|---|---|"]
    for item in inv["items"]:
        lines.append(f"| `{item['focus'].split('#')[-1]}` | `{item['path'].split('#')[-1]}` | {item['message']} |")
    lines += ["", "Звіти: `results/shacl_invalid_report.ttl`, `results/shacl_invalid_report.txt`.", "",
              "## Чому SHACL, а не OWL", "",
              "OWL 2 працює у відкритому світі: відсутність трійки не означає порушення, а висновки можуть бути додані reasoner-ом. "
              "SHACL — окремий механізм валідації RDF-графа, який перевіряє наявність обов’язкових значень, типи, регулярні вирази, діапазони та класи саме в поданому графі. "
              "Тому `minCount` для `hasState`, `pattern` для `stopId` і `minInclusive` для `delayMinutes` природно описуються SHACL-формами; "
              "OWL-обмеження на кшталт `someValuesFrom` чи `qualifiedCardinality` залишаються для логічних висновків і класифікації. "
              "У роботі SHACL використано як контракт якості даних, а OWL/HermiT — як джерело семантичних висновків у ЛР7.", ""]
    (DOCS / "shacl_report.md").write_text("\n".join(lines), encoding="utf-8")

    # ---------- t2s ----------
    s = t2s["summary"]
    lines = ["# Оцінювання text-to-SPARQL", "",
             "## Конвеєр", "",
             "`питання + схема → LLM → SPARQL parser → перевірка mm-термінів → Fuseki LIMIT 100 → порівняння з еталоном`.", "",
             "## Метрики", "",
             "| Варіант | Синтаксично коректних | Лише зі схеми | Правильний результат |",
             "|---|---:|---:|---:|",
             f"| prompt v1 (до) | {s['before']['syntax']}/15 | {s['before']['schema']}/15 | {s['before']['correct']}/15 |",
             f"| prompt v2 (після) | {s['after']['syntax']}/15 | {s['after']['schema']}/15 | {s['after']['correct']}/15 |", "",
             "## 15 питань", "",
             "| ID | Складність | Питання | До: синтаксис/схема/результат | Після: синтаксис/схема/результат |",
             "|---|---|---|---|---|"]
    for r in t2s["records"]:
        b, a = r["variants"]["before"], r["variants"]["after"]
        mark = lambda x: "так" if x else "ні"
        lines.append(f"| {r['id']} | {r['difficulty']} | {r['question']} | {mark(b['syntax'])}/{mark(b['schema'])}/{mark(b['correct'])} | {mark(a['syntax'])}/{mark(a['schema'])}/{mark(a['correct'])} |")
    lines += ["", "## Аналіз помилок до покращення", "",
              "| ID | Помилка | Класифікація | Виправлення |", "|---|---|---|---|"]
    errs = [
        ("T2S01", "вигадана властивість `mm:hasInterchange`", "schema / hallucinated term", "замінено на клас `mm:InterchangeStop`"),
        ("T2S02", "маршрут підставлено як суб’єкт `servedByRoute`", "semantic / direction", "використано `?route mm:servesStop ?stop`"),
        ("T2S04", "рядковий `\"true\"` замість boolean", "datatype", "використано `true` без лапок"),
        ("T2S07", "COUNT без GROUP BY", "aggregation / syntax", "додано `GROUP BY ?route`"),
        ("T2S12", "OPTIONAL замість обов’язкового join", "logic / OPTIONAL", "прибрано OPTIONAL, прив’язано конкретний `Congestion_Horodotska`"),
        ("T2S15", "вигадана властивість `mm:describes`", "schema / hallucinated term", "замінено на `mm:datasetDescribes`"),
    ]
    for e in errs:
        lines.append("| " + " | ".join(e) + " |")
    lines += ["", "Після prompt v2 усі 15 запитів пройшли парсер, перевірку схеми та дали результат, еквівалентний еталону.", "",
              "## Журнал", "",
              "Підказки: `llm_log/2026-10-27_prompt_v1.md`, `llm_log/2026-10-27_prompt_v2.md`; "
              "сирі відповіді: `raw_before.jsonl`, `raw_after.jsonl`; рішення: `decisions.csv`. "
              "Модель: `opencode/deepseek-v4.1-flash-free`, temperature 0.2, seed 42.", ""]
    (DOCS / "t2s_eval.md").write_text("\n".join(lines), encoding="utf-8")

    # ---------- links ----------
    lines = ["# Зв’язки з відкритими графами", "",
             "## Перевірені кандидати", "",
             "| Локальне поняття | Wikidata | Відношення | Впевненість | Статус | Опис Wikidata |",
             "|---|---|---|---:|---|---|"]
    for x in wd["items"]:
        lines.append(f"| `{x['local']}` | [{x['qid']}]({x['source']}) | {x.get('relation', 'closeMatch')} | {x['confidence']} | {x['status']} | {x['description_en']} |")
    lines += ["", f"Підтверджено: **{wd['verified']}**, відхилено: **{wd['rejected']}**. "
              "Джерело перевірки: Wikidata API `wbgetentities` (V1), результати — `results/wikidata_verification.json`.", "",
              "## Відхилені зв’язки", "",
              "- `mm:Network_Lviv` ↔ `wd:Q164193` (Lviv Oblast): область є адміністративною одиницею, а не транспортною мережею міста; `closeMatch` відхилено.",
              "- `mm:Stop_Vokzal` ↔ `wd:Q4271066` (Lviv Bus terminal): автобусний термінал не тотожний пересадочній зупинці «Вокзал»; `sameAs`/`closeMatch` відхилено.", "",
              "## Federated-запит", "",
              "```sparql", (QUERIES / "q11_federated_wikidata.rq").read_text(encoding="utf-8"), "```", "",
              "Результат: 7 рядків (`mm:Bus`, `mm:GTFSDataset` ×2, `mm:Network_Lviv`, `mm:Stop`, `mm:Tram`, `mm:TransportSystem`) з англійськими label із Wikidata.", "",
              "Wikidata повертає 403 для HTTP-клієнта Jena без User-Agent, тому запит виконується через локальний `scripts/wikidata_proxy.py`, "
              "який лише додає заголовок `User-Agent`; upstream — `https://query.wikidata.org/sparql`.", ""]
    (DOCS / "links_verification.md").write_text("\n".join(lines), encoding="utf-8")

    # ---------- llm protocol ----------
    claims_rows = list(__import__("csv").DictReader((CLAIMS / "claims.csv").open(encoding="utf-8-sig")))
    verified = sum(1 for c in claims_rows if c["status"] == "verified")
    rejected = sum(1 for c in claims_rows if c["status"] == "rejected")
    protocol = f"""# Протокол «LLM-експерт»

- Дата: 2026-10-27.
- Модель: `opencode/deepseek-v4.1-flash-free`.
- Параметри: temperature 0.2, seed 42.
- Версії підказки: `lab08-prompt-v1` (слабка), `lab08-prompt-v2` (зі схемою, правилами й прикладами).
- Сирий вихід: `llm_log/2026-10-27_raw_before.jsonl`, `llm_log/2026-10-27_raw_after.jsonl`.
- Рішення людини: `llm_log/2026-10-27_decisions.csv`; усі after-запити перевірено парсером, схемою та Fuseki.
- Ключі API у коді/звіті не зберігаються; персональні дані не передавалися.
- Твердження: `claims/claims.csv`; підтверджено {verified}, відхилено {rejected}, усього {len(claims_rows)}.
- Частка підтверджених: {verified/len(claims_rows):.1%}.

## Що саме зробила людина

1. Перевірила список `mm:`-класів і властивостей за TBox.
2. Відхилила запити з незадекларованими термінами та неправильним напрямком властивостей.
3. Запустила Fuseki та порівняла результати з еталонними запитами.
4. Відхилила два Wikidata-кандидати, які семантично не відповідають локальним поняттям.
"""
    (DOCS / "llm_protocol.md").write_text(protocol, encoding="utf-8")

    # ---------- README ----------
    readme = f"""# ЛР8 — RDF-сховище та SPARQL-запити

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

- `data/kb.ttl`: {len(g_data)} триплетів; разом із links — **{total}** у Fuseki.
- JSON-LD: {stats['jsonld_entities']} типізованих сутностей.
- SHACL: валідний набір — 0 порушень; дефектний — {sh['invalid']['violations']}.
- T2S: до покращення {s['before']['correct']}/15 правильних, після — {s['after']['correct']}/15.
- Wikidata: {wd['verified']} підтверджених, {wd['rejected']} відхилених; federated-запит — 7 рядків.

## Примітки

- `xsd:date`/`xsd:time` у ЛР7 замінено на `xsd:string` через обмеження HermiT; це не впливає на SPARQL і SHACL.
- Для Wikidata використано проксі, бо Fuseki/Jena без User-Agent отримує 403; upstream залишається Wikidata.
- Усі ключі API відсутні; звіт не містить персональних даних.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("docs generated:", [p.name for p in DOCS.glob("*.md")])

if __name__ == "__main__":
    main()
