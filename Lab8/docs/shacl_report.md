# SHACL-валідація

## Форми та обмеження

| Форма | Цільовий клас | Призначення |
|---|---|---|
| StopShape | mm:Stop | stopId, stopName, координати, доступність, маршрут |
| TripShape | mm:Trip | tripId, маршрут, стан, ТЗ, початкова/кінцева зупинка |
| RouteShape | mm:TransportRoute | routeId, routeType, servesStop, hasTrip |
| DelayShape | mm:Delay | delayMinutes, measurementOf, measuredBy |
| EventShape | mm:Event | eventTime, affectsSegment |
| RecommendationShape | mm:Recommendation | recommends, forPassenger, recommendationOfDecision |
| AgencyShape | mm:TransportAgency | agencyName, operatesTrip |

Разом: **7 NodeShape**, **26 property shapes**, **158 трійок SHACL-обмежень**. Використано `minCount`, `maxCount`, `datatype`, `class`, `pattern`, `minInclusive`, `maxInclusive`, `nodeKind`, `in`.

## Валідний набір

`data/kb.ttl`: **Conforms = true**, порушень: 0.

Звіти: `results/shacl_valid_report.ttl`, `results/shacl_valid_report.txt`.

## Дефектний набір

`data/kb_invalid.ttl` містить три навмисні дефекти:

1. `Stop_Vokzal.stopId` = `VOKZAL` замість `S001` (pattern).
2. У `Trip_9_0800` видалено `hasState` (minCount).
3. `Congestion_Horodotska.eventTime` = `not-a-date` без `xsd:dateTime` (datatype).

Результат: **Conforms = false**, виявлено **3** порушення.

| Фокус | Шлях | Повідомлення |
|---|---|---|
| `Stop_Vokzal` | `stopId` | stopId має бути один рядок формату S### |
| `Congestion_Horodotska` | `eventTime` | Подія повинна мати eventTime типу xsd:dateTime |
| `Trip_9_0800` | `hasState` | Рейс повинен мати рівно один стан |

Звіти: `results/shacl_invalid_report.ttl`, `results/shacl_invalid_report.txt`.

## Чому SHACL, а не OWL

OWL 2 працює у відкритому світі: відсутність трійки не означає порушення, а висновки можуть бути додані reasoner-ом. SHACL — окремий механізм валідації RDF-графа, який перевіряє наявність обов’язкових значень, типи, регулярні вирази, діапазони та класи саме в поданому графі. Тому `minCount` для `hasState`, `pattern` для `stopId` і `minInclusive` для `delayMinutes` природно описуються SHACL-формами; OWL-обмеження на кшталт `someValuesFrom` чи `qualifiedCardinality` залишаються для логічних висновків і класифікації. У роботі SHACL використано як контракт якості даних, а OWL/HermiT — як джерело семантичних висновків у ЛР7.
