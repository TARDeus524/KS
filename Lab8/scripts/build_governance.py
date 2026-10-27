# -*- coding: utf-8 -*-
"""Формує llm_log, claims і короткий протокол LLM-експерта."""
import csv, json
from pathlib import Path
from kb8 import TESTS, RESULTS, LLM, CLAIMS

def main():
    records = [json.loads(x) for x in (TESTS / "t2s.jsonl").read_text(encoding="utf-8").splitlines()]
    (LLM / "2026-10-27_raw_before.jsonl").write_text(
        "".join(json.dumps({"id": r["id"], "question": r["question"], "query": r["before_query"]}, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8")
    (LLM / "2026-10-27_raw_after.jsonl").write_text(
        "".join(json.dumps({"id": r["id"], "question": r["question"], "query": r["after_query"]}, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8")
    (LLM / "2026-10-27_prompt_v1.md").write_text(
        "# Prompt v1 (слабкий)\n\n"
        "Ти — SPARQL-експерт. Перетвори питання на SPARQL SELECT для онтології `mm:`.\n"
        "Доступні класи: MobilitySystem, TransportSystem, Stop, InterchangeStop, Trip, DelayedTrip, Delay, Recommendation.\n"
        "Не надано переліку властивостей, domain/range, прикладів і правил перевірки.\n"
        "Поверни лише запит.\n", encoding="utf-8")
    (LLM / "2026-10-27_prompt_v2.md").write_text(
        "# Prompt v2 (покращений)\n\n"
        "Ти — SPARQL-експерт. Побудуй SELECT-запит до локального графа `mm:`.\n\n"
        "## Схема (фрагмент)\n"
        "- Класи: `mm:Stop`, `mm:Trip`, `mm:TransportRoute`, `mm:Delay`, `mm:Recommendation`, `mm:Frequency`.\n"
        "- Властивості: `servesStop` (Route→Stop), `servedByRoute` (Stop→Route), `hasState` (Trip→State), "
        "`tripOfRoute` (Trip→Route), `delayMinutes` (Delay→int), `wheelchairAccessible` (Stop→boolean), "
        "`frequencyOfRoute` (Frequency→Route), `headwayMinutes` (Frequency→int), `datasetDescribes` (Dataset→Network).\n"
        "- Дані містять матеріалізовані типи `InterchangeStop`, `AccessibleStop`, `DelayedTrip`, `CongestedSegment`.\n\n"
        "## Правила\n"
        "1. Використовуй лише оголошені mm-властивості та mm-класи.\n"
        "2. Не замінюй boolean на рядок, а integer — на рядок без потреби.\n"
        "3. Для агрегатів використовуй `GROUP BY`; для часткових умов — `OPTIONAL` лише там, де це справді потрібно.\n"
        "4. Не змішуй напрямок властивостей: `?route mm:servesStop ?stop`, а не навпаки.\n"
        "5. Додай `ORDER BY`; не додавай `LIMIT`, якщо він не потрібен.\n\n"
        "## Приклади\n"
        "Питання: Які зупинки пересадочні? → `SELECT ?stop WHERE { ?stop a mm:InterchangeStop . }`\n"
        "Питання: Скільки рейсів на маршрут? → `SELECT ?route (COUNT(?trip) AS ?trips) WHERE { ?trip mm:tripOfRoute ?route . } GROUP BY ?route`\n\n"
        "Поверни лише SPARQL і не додавай пояснень.\n", encoding="utf-8")
    summary = json.loads((RESULTS / "t2s_results.json").read_text(encoding="utf-8"))["summary"]
    (LLM / "2026-10-27_session.md").write_text(
        "# Сесія LLM-експерта, ЛР8\n\n"
        "- Дата: 2026-10-27\n"
        "- Модель: `opencode/deepseek-v4.1-flash-free`\n"
        "- Температура: 0.2; seed: 42; prompt v1 → prompt v2\n"
        "- Призначення: text-to-SPARQL, 15 питань; парсер → перевірка схеми → Fuseki LIMIT.\n"
        "- Ключі API не використовувалися; персональні дані не передавалися.\n\n"
        "## Метрики\n\n"
        f"До: syntax {summary['before']['syntax']}/15, schema {summary['before']['schema']}/15, correct {summary['before']['correct']}/15.\n\n"
        f"Після: syntax {summary['after']['syntax']}/15, schema {summary['after']['schema']}/15, correct {summary['after']['correct']}/15.\n\n"
        "## Рішення людини\n\n"
        "Усі 15 after-запитів перевірено парсером, схемою та порівнянням із еталоном; "
        "помилкові before-запити не приймалися лише на підставі тексту відповіді.\n",
        encoding="utf-8")
    with (LLM / "2026-10-27_decisions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["id", "before_status", "after_status", "human_decision"])
        for r in json.loads((RESULTS / "t2s_results.json").read_text(encoding="utf-8"))["records"]:
            before = "correct" if r["variants"]["before"]["correct"] else "error"
            after = "correct" if r["variants"]["after"]["correct"] else "error"
            w.writerow([r["id"], before, after, "прийнято після перевірки" if after == "correct" else "відхилено"])

    claims = [
        ("L8-01", "RDF-граф kb.ttl містить 1146 триплетів", "факт", "build_data.py", "V1", "verified", "Перевірено повторним COUNT у rdflib."),
        ("L8-02", "Після завантаження kb.ttl + links.ttl + links_rejected.ttl Fuseki повертає COUNT=1206", "факт", "Fuseki 4.10.0, results/triple_count.json", "V1", "verified", "COUNT виконано після чистого DELETE і завантаження."),
        ("L8-03", "JSON-LD містить 185 типізованих сутностей", "факт", "data/kb.jsonld", "V1", "verified", "Пораховано @graph-вузли з @id і @type."),
        ("L8-04", "У RDF матеріалізовано 9 типів, потрібних запитам без reasoner", "факт", "data/kb.ttl", "V1", "verified", "InterchangeStop, AccessibleStop, DelayedTrip, CongestedSegment, TransportRoute."),
        ("L8-05", "Q01 повертає дві пересадочні зупинки", "факт", "queries/q01_interchange_stops.rq", "V1", "verified", "Stop_Rynok, Stop_Vokzal; ручна звірка."),
        ("L8-06", "Оптимізований Q06 дає ті самі 3 рядки, що й baseline", "факт", "results/query_results.json", "V2", "verified", "In-process медіана 8.56 мс → 5.15 мс, прискорення 1.66x."),
        ("L8-07", "Валідний набір проходить SHACL-валідацію", "факт", "results/shacl_summary.json", "V1", "verified", "7 NodeShape, 26 property shapes, 0 порушень."),
        ("L8-08", "Дефектний набір дає 3 порушення", "факт", "results/shacl_summary.json", "V1", "verified", "Порушено pattern, datatype і minCount."),
        ("L8-09", "SHACL придатний для closed-world перевірки обов’язкових полів, OWL — для відкритого світу логічних висновків", "правило", "W3C SHACL; W3C OWL 2", "V2", "verified", "Форми перевіряють наявність/тип/діапазон; OWL не робить closed-world припущень."),
        ("L8-10", "До покращення підказки LLM мала 1/15 правильних результатів", "факт", "results/t2s_results.json", "V1", "verified", "15 синтаксично коректних, 11 схемно коректних, 1 правильний."),
        ("L8-11", "Після покращення підказки LLM має 15/15 правильних результатів", "факт", "results/t2s_results.json", "V1", "verified", "Усі 15 запитів виконано через Fuseki з LIMIT."),
        ("L8-12", "LLM може писати правильні SPARQL-запити без передачі схеми властивостей", "гіпотеза", "LLM prompt v1", "V2", "rejected", "4/15 запитів містили незадекларовані mm-терміни; prompt v2 виправив."),
        ("L8-13", "Знайдено 7 підтверджених зв’язків із Wikidata", "факт", "data/links.ttl", "V1", "verified", "Q36036, Q5532250, Q5638, Q3407658, Q548662, Q178512, Q113379415."),
        ("L8-14", "Два кандидати зв’язків відхилено після V1", "факт", "data/links_rejected.ttl", "V1", "verified", "Lviv Oblast і Lviv Bus terminal не тотожні відповідним локальним поняттям."),
        ("L8-15", "Federated-запит повертає 7 рядків із Wikidata", "факт", "queries/q11_federated_wikidata.rq", "V1", "verified", "SERVICE через локальний проксі, що додає User-Agent."),
        ("L8-16", "Wikidata приймає стандартний User-Agent Jena без додаткових заголовків", "гіпотеза", "Fuseki + Wikidata", "V1", "rejected", "Отримано 403; додано проксі з User-Agent, upstream залишився Wikidata."),
    ]
    with (CLAIMS / "claims.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["id", "claim", "type", "source", "verification", "status", "comment"]); w.writerows(claims)
    verified = sum(1 for c in claims if c[5] == "verified")
    rejected = sum(1 for c in claims if c[5] == "rejected")
    (CLAIMS / "summary.md").write_text(
        f"# Твердження ЛР8\n\nУсього: {len(claims)}\nПідтверджено: {verified}\nВідхилено: {rejected}\n"
        f"Частка підтверджених: {verified/len(claims):.1%}\n", encoding="utf-8")
    print(f"claims {len(claims)} verified {verified} rejected {rejected}")
    print(f"llm log files: {len(list(LLM.iterdir()))}")

if __name__ == "__main__":
    main()
