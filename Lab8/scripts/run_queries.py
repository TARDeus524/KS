# -*- coding: utf-8 -*-
"""Виконує SPARQL-запити через Fuseki, зберігає результати й тайминги."""
import csv, json, statistics, time
from pathlib import Path
import requests
from rdflib import Graph
from kb8 import QUERIES, RESULTS, MM_NS, DATASET, FUSEKI_URL

ENDPOINT = f"{FUSEKI_URL}/{DATASET}/query"

META = {
    "q01_interchange_stops": ("Q01", "CQ1", "Які зупинки є пересадочними?", "SELECT", "Перелік пересадочних зупинок; перевірка класу InterchangeStop."),
    "q02_routes_at_vokzal": ("Q02", "CQ2", "Які маршрути обслуговують зупинку «Вокзал»?", "SELECT", "Маршрути, що мають пряме відношення servesStop до Stop_Vokzal."),
    "q03_accessible_stops": ("Q03", "CQ5", "Які зупинки доступні для маломобільних пасажирів?", "SELECT", "Фільтр за булевим значенням wheelchairAccessible."),
    "q04_delayed_trips": ("Q04", "CQ3", "Які рейси мають стан затримки?", "SELECT", "Рейс із станом DelayedState через hasState."),
    "q05_delay_over_10": ("Q05", "CQ9", "Які рейси мають затримку понад 10 хвилин?", "SELECT", "Агрегат Delay + FILTER(?minutes > 10)."),
    "q06_trip_counts_by_route": ("Q06", "CQ11", "Скільки рейсів має кожен маршрут?", "SELECT", "Агрегація COUNT із GROUP BY; базовий варіант для оптимізації."),
    "q06_trip_counts_by_route_opt": ("Q06-OPT", "CQ11", "Скільки рейсів має кожен маршрут? (оптимізовано)", "SELECT", "Те саме без зайвого класу та з прямим hasTrip."),
    "q07_stops_with_optional_access": ("Q07", "CQ12", "Які зупинки мають маршрути та ознаку доступності?", "SELECT", "OPTIONAL для доступності й маршрутів; рядки без значень не губляться."),
    "q08_route_stop_path": ("Q08", "CQ13", "Які зупинки входять до маршруту через рейс і stop time?", "SELECT", "Property path hasTrip/hasStopTime/atStop."),
    "q09_ask_accessible": ("Q09", "CQ14", "Чи доступний «Вокзал» для маломобільних пасажирів?", "ASK", "ASK-перевірка одного факту без побудови таблиці."),
    "q10_construct_route_trip": ("Q10", "CQ15", "Побудувати підграф маршрут → рейс → початкова/кінцева зупинка.", "CONSTRUCT", "CONSTRUCT повертає RDF-граф для повторного використання."),
    "q11_federated_wikidata": ("Q11", "CQ16", "Які локальні поняття мають підтверджені відповідники у Wikidata?", "SELECT", "Federated SERVICE до Wikidata через проксі з User-Agent."),
}

MANUAL = {
    "Q01": (2, ["Stop_Rynok", "Stop_Vokzal"]),
    "Q02": (3, ["Route_25", "Route_31", "Route_9"]),
    "Q04": (1, ["Trip_9_0800"]),
    "Q06": (3, ["Route_9:2", "Route_25:1", "Route_31:1"]),
    "Q08": (3, ["Route_9:Stop_Politekhnika", "Route_9:Stop_Rynok", "Route_9:Stop_Vokzal"]),
    "Q09": (1, ["true"]),
    "Q10": (12, []),
    "Q11": (7, []),
}

def shorten(value, typ=None):
    if typ == "uri" and value.startswith(MM_NS):
        return "mm:" + value[len(MM_NS):]
    if typ == "uri" and value.startswith("http://www.wikidata.org/entity/"):
        return "wd:" + value.rsplit("/", 1)[-1]
    return value

def binding_rows(bindings):
    out = []
    for b in bindings:
        out.append({k: shorten(v["value"], v.get("type")) for k, v in b.items()})
    return out

def execute(query, accept="application/sparql-results+json", timeout=150):
    t0 = time.perf_counter()
    r = requests.get(ENDPOINT, params={"query": query}, headers={"Accept": accept}, timeout=timeout)
    elapsed = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    return r, elapsed

def main():
    records = []
    timings = []
    for path in sorted(QUERIES.glob("q*.rq")):
        key = path.stem
        if key not in META:
            continue
        qid, cq, question, qtype, purpose = META[key]
        query = path.read_text(encoding="utf-8")
        if qtype == "CONSTRUCT":
            r, ms = execute(query, accept="text/turtle")
            g = Graph().parse(data=r.text, format="turtle")
            (RESULTS / "construct_route_trip.ttl").write_text(r.text, encoding="utf-8")
            record = {"id": qid, "file": path.name, "cq": cq, "question": question,
                      "purpose": purpose, "type": qtype, "elapsed_ms": round(ms, 2),
                      "count": len(g), "rows": [], "status": "PASS" if len(g) >= 3 else "FAIL"}
        elif qtype == "ASK":
            r, ms = execute(query)
            val = r.json()["boolean"]
            record = {"id": qid, "file": path.name, "cq": cq, "question": question,
                      "purpose": purpose, "type": qtype, "elapsed_ms": round(ms, 2),
                      "count": 1 if val else 0, "boolean": val, "rows": [{"ask": str(val).lower()}],
                      "status": "PASS" if val else "FAIL"}
        else:
            r, ms = execute(query)
            rows = binding_rows(r.json()["results"]["bindings"])
            record = {"id": qid, "file": path.name, "cq": cq, "question": question,
                      "purpose": purpose, "type": qtype, "elapsed_ms": round(ms, 2),
                      "count": len(rows), "rows": rows, "status": "PASS" if rows else "FAIL"}
        if qid in MANUAL:
            expected_count, expected_values = MANUAL[qid]
            if qid == "Q09":
                ok = record.get("boolean") is True
            elif qid == "Q10":
                ok = record["count"] == expected_count
            elif qid == "Q06":
                got = {r["route"]: r.get("trips") for r in record["rows"]}
                ok = got == {"mm:Route_9": "2", "mm:Route_25": "1", "mm:Route_31": "1"}
            elif qid == "Q11":
                ok = record["count"] == expected_count
            elif qid == "Q08":
                got = sorted(f"{r['route'].replace('mm:', '')}:{r['stop'].replace('mm:', '')}" for r in record["rows"])
                ok = record["count"] == expected_count and got == sorted(expected_values)
            else:
                got = sorted(v.replace("mm:", "") for row in record["rows"] for v in row.values())
                ok = record["count"] == expected_count and got == sorted(expected_values)
            record["manual"] = {"expected_count": expected_count,
                                "expected_values": expected_values,
                                "status": "PASS" if ok else "FAIL"}
        else:
            record["manual"] = {"status": "not_checked"}
        record["query"] = query.strip()
        records.append(record)
        timings.append({"id": qid, "type": qtype, "elapsed_ms": round(ms, 2), "rows": record["count"]})

    base = next(r for r in records if r["id"] == "Q06")
    opt = next(r for r in records if r["id"] == "Q06-OPT")
    base_times, opt_times = [], []
    for _ in range(10):
        q = (QUERIES / base["file"]).read_text(encoding="utf-8")
        _, ms = execute(q); base_times.append(ms)
        q = (QUERIES / opt["file"]).read_text(encoding="utf-8")
        _, ms = execute(q); opt_times.append(ms)
    local = Graph().parse(str(QUERIES.parent / "data" / "kb.ttl"), format="turtle")
    local.parse(str(QUERIES.parent / "data" / "links.ttl"), format="turtle")
    local_base, local_opt = [], []
    for _ in range(30):
        t0 = time.perf_counter(); list(local.query((QUERIES / base["file"]).read_text(encoding="utf-8"))); local_base.append((time.perf_counter()-t0)*1000)
        t0 = time.perf_counter(); list(local.query((QUERIES / opt["file"]).read_text(encoding="utf-8"))); local_opt.append((time.perf_counter()-t0)*1000)
    timing_summary = {
        "baseline_file": base["file"], "optimized_file": opt["file"],
        "baseline_median_ms": round(statistics.median(base_times), 2),
        "optimized_median_ms": round(statistics.median(opt_times), 2),
        "http_runs": 10,
        "http_speedup": round(statistics.median(base_times) / max(statistics.median(opt_times), 0.001), 2),
        "inprocess_baseline_median_ms": round(statistics.median(local_base), 3),
        "inprocess_optimized_median_ms": round(statistics.median(local_opt), 3),
        "inprocess_runs": 30,
        "inprocess_speedup": round(statistics.median(local_base) / max(statistics.median(local_opt), 0.001), 2),
    }
    out = {"endpoint": ENDPOINT, "dataset": DATASET, "query_count": len(records),
           "timing": timing_summary, "queries": records}
    (RESULTS / "query_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RESULTS / "query_timings.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id", "type", "elapsed_ms", "rows"])
        w.writeheader(); w.writerows(timings)
    print(json.dumps({"queries": len(records), "timing": timing_summary,
                      "statuses": {r["id"]: r["status"] for r in records}}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
