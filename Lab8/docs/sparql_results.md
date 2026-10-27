# SPARQL-запити до CQ

Усього запитів: 12. Усі виконано до Fuseki dataset `ds`. Для SELECT/ASK використано JSON, для CONSTRUCT — Turtle.

## Зведена таблиця

| ID | CQ | Тип | Рядків / трійок | Час, мс | Статус | Ручна перевірка |
|---|---|---|---:|---:|---|---|
| Q01 | CQ1 | SELECT | 2 | 6.51 | PASS | PASS |
| Q02 | CQ2 | SELECT | 3 | 7.49 | PASS | PASS |
| Q03 | CQ5 | SELECT | 2 | 5.97 | PASS | not_checked |
| Q04 | CQ3 | SELECT | 1 | 8.55 | PASS | PASS |
| Q05 | CQ9 | SELECT | 1 | 5.82 | PASS | not_checked |
| Q06 | CQ11 | SELECT | 3 | 8.49 | PASS | PASS |
| Q06-OPT | CQ11 | SELECT | 3 | 6.46 | PASS | not_checked |
| Q07 | CQ12 | SELECT | 7 | 7.75 | PASS | not_checked |
| Q08 | CQ13 | SELECT | 3 | 10.66 | PASS | PASS |
| Q09 | CQ14 | ASK | 1 | 6.22 | PASS | PASS |
| Q10 | CQ15 | CONSTRUCT | 12 | 9.23 | PASS | PASS |
| Q11 | CQ16 | SELECT | 7 | 2201.13 | PASS | PASS |

## Запити, результати та інтерпретація

### Q01 — Які зупинки є пересадочними?

**CQ:** CQ1. **Тип:** SELECT. **Призначення:** Перелік пересадочних зупинок; перевірка класу InterchangeStop.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT DISTINCT ?stop
WHERE {
  ?stop a mm:InterchangeStop .
}
ORDER BY ?stop
```

| stop |
|---|
| mm:Stop_Rynok |
| mm:Stop_Vokzal |

Ручна перевірка: **PASS**; очікувано 2 рядків / значень.

### Q02 — Які маршрути обслуговують зупинку «Вокзал»?

**CQ:** CQ2. **Тип:** SELECT. **Призначення:** Маршрути, що мають пряме відношення servesStop до Stop_Vokzal.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT DISTINCT ?route
WHERE {
  ?route mm:servesStop mm:Stop_Vokzal .
}
ORDER BY ?route
```

| route |
|---|
| mm:Route_25 |
| mm:Route_31 |
| mm:Route_9 |

Ручна перевірка: **PASS**; очікувано 3 рядків / значень.

### Q03 — Які зупинки доступні для маломобільних пасажирів?

**CQ:** CQ5. **Тип:** SELECT. **Призначення:** Фільтр за булевим значенням wheelchairAccessible.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT DISTINCT ?stop
WHERE {
  ?stop mm:wheelchairAccessible true .
}
ORDER BY ?stop
```

| stop |
|---|
| mm:Stop_Politekhnika |
| mm:Stop_Vokzal |

### Q04 — Які рейси мають стан затримки?

**CQ:** CQ3. **Тип:** SELECT. **Призначення:** Рейс із станом DelayedState через hasState.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT DISTINCT ?trip
WHERE {
  ?trip mm:hasState ?state .
  ?state a mm:DelayedState .
}
ORDER BY ?trip
```

| trip |
|---|
| mm:Trip_9_0800 |

Ручна перевірка: **PASS**; очікувано 1 рядків / значень.

### Q05 — Які рейси мають затримку понад 10 хвилин?

**CQ:** CQ9. **Тип:** SELECT. **Призначення:** Агрегат Delay + FILTER(?minutes > 10).

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT DISTINCT ?trip ?minutes
WHERE {
  ?delay a mm:Delay ;
         mm:measurementOf ?trip ;
         mm:delayMinutes ?minutes .
  FILTER(?minutes > 10)
}
ORDER BY DESC(?minutes) ?trip
```

| trip | minutes |
|---|---|
| mm:Trip_9_0800 | 12 |

### Q06 — Скільки рейсів має кожен маршрут?

**CQ:** CQ11. **Тип:** SELECT. **Призначення:** Агрегація COUNT із GROUP BY; базовий варіант для оптимізації.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT ?route (COUNT(DISTINCT ?trip) AS ?trips)
WHERE {
  ?route a mm:TransportRoute ;
         mm:hasTrip ?trip .
  ?trip ?p ?o .
  ?o ?p2 ?o2 .
}
GROUP BY ?route
ORDER BY DESC(?trips) ?route
```

| route | trips |
|---|---|
| mm:Route_9 | 2 |
| mm:Route_25 | 1 |
| mm:Route_31 | 1 |

Ручна перевірка: **PASS**; очікувано 3 рядків / значень.

### Q06-OPT — Скільки рейсів має кожен маршрут? (оптимізовано)

**CQ:** CQ11. **Тип:** SELECT. **Призначення:** Те саме без зайвого класу та з прямим hasTrip.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT ?route (COUNT(?trip) AS ?trips)
WHERE {
  ?route mm:hasTrip ?trip .
}
GROUP BY ?route
ORDER BY DESC(?trips) ?route
```

| route | trips |
|---|---|
| mm:Route_9 | 2 |
| mm:Route_25 | 1 |
| mm:Route_31 | 1 |

### Q07 — Які зупинки мають маршрути та ознаку доступності?

**CQ:** CQ12. **Тип:** SELECT. **Призначення:** OPTIONAL для доступності й маршрутів; рядки без значень не губляться.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT ?stop ?name ?accessible ?route
WHERE {
  ?stop a mm:Stop ;
        mm:stopName ?name .
  OPTIONAL { ?stop mm:wheelchairAccessible ?accessible }
  OPTIONAL { ?stop mm:servedByRoute ?route }
}
ORDER BY ?stop ?route
```

| stop | name | accessible | route |
|---|---|---|---|
| mm:Stop_Politekhnika | Політехніка | true | mm:Route_9 |
| mm:Stop_Rynok | Площа Ринок | false | mm:Route_31 |
| mm:Stop_Rynok | Площа Ринок | false | mm:Route_9 |
| mm:Stop_Universytet | Університет | false | mm:Route_25 |
| mm:Stop_Vokzal | Вокзал | true | mm:Route_25 |
| mm:Stop_Vokzal | Вокзал | true | mm:Route_31 |
| mm:Stop_Vokzal | Вокзал | true | mm:Route_9 |

### Q08 — Які зупинки входять до маршруту через рейс і stop time?

**CQ:** CQ13. **Тип:** SELECT. **Призначення:** Property path hasTrip/hasStopTime/atStop.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

SELECT DISTINCT ?route ?stop
WHERE {
  ?route a mm:TransportRoute ;
         mm:hasTrip/mm:hasStopTime/mm:atStop ?stop .
}
ORDER BY ?route ?stop
```

| route | stop |
|---|---|
| mm:Route_9 | mm:Stop_Politekhnika |
| mm:Route_9 | mm:Stop_Rynok |
| mm:Route_9 | mm:Stop_Vokzal |

Ручна перевірка: **PASS**; очікувано 3 рядків / значень.

### Q09 — Чи доступний «Вокзал» для маломобільних пасажирів?

**CQ:** CQ14. **Тип:** ASK. **Призначення:** ASK-перевірка одного факту без побудови таблиці.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

ASK {
  mm:Stop_Vokzal mm:wheelchairAccessible true .
}
```

Результат: `true`.

Ручна перевірка: **PASS**; очікувано 1 рядків / значень.

### Q10 — Побудувати підграф маршрут → рейс → початкова/кінцева зупинка.

**CQ:** CQ15. **Тип:** CONSTRUCT. **Призначення:** CONSTRUCT повертає RDF-граф для повторного використання.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>

CONSTRUCT {
  ?route mm:hasTrip ?trip .
  ?trip mm:startsAt ?start ;
        mm:endsAt ?end .
}
WHERE {
  ?route a mm:TransportRoute ;
         mm:hasTrip ?trip .
  ?trip mm:startsAt ?start ;
        mm:endsAt ?end .
}
```

Результат: 12 трійок; збережено в `results/construct_route_trip.ttl`.

Ручна перевірка: **PASS**; очікувано 12 рядків / значень.

### Q11 — Які локальні поняття мають підтверджені відповідники у Wikidata?

**CQ:** CQ16. **Тип:** SELECT. **Призначення:** Federated SERVICE до Wikidata через проксі з User-Agent.

```sparql
PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>

SELECT ?local ?external ?externalLabel
WHERE {
  VALUES ?external {
    wd:Q36036 wd:Q5532250 wd:Q5638 wd:Q3407658
    wd:Q548662 wd:Q178512 wd:Q113379415
  }
  ?local mm:linkStatus "verified" .
  { ?local skos:exactMatch ?external }
  UNION
  { ?local skos:closeMatch ?external }
  SERVICE <http://127.0.0.1:3031/sparql> {
    ?external rdfs:label ?externalLabel .
    FILTER(LANG(?externalLabel) = "en")
  }
}
ORDER BY ?local
```

| local | external | externalLabel |
|---|---|---|
| mm:Bus | wd:Q5638 | bus |
| mm:GTFSDataset | wd:Q113379415 | General Transit Feed Specification feed |
| mm:GTFSDataset | wd:Q5532250 | General Transit Feed Specification |
| mm:Network_Lviv | wd:Q36036 | Lviv |
| mm:Stop | wd:Q548662 | public transport stop |
| mm:Tram | wd:Q3407658 | tram |
| mm:TransportSystem | wd:Q178512 | public transport |

Ручна перевірка: **PASS**; очікувано 7 рядків / значень.

## Оптимізація Q06

Baseline: `q06_trip_counts_by_route.rq`; optimized: `q06_trip_counts_by_route_opt.rq`.

- HTTP-медіана: 7.84 мс → 6.47 мс (×1.21, 10 запусків).
- rdflib in-process: 8.564 мс → 5.15 мс (×1.66, 30 запусків).

У baseline навмисно залишено зайві join-и `?trip ?p ?o . ?o ?p2 ?o2` і `COUNT(DISTINCT ?trip)`. Optimized прибирає зайві triple patterns і використовує прямий `mm:hasTrip`; результати ідентичні (3 рядки).
