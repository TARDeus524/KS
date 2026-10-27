# Зв’язки з відкритими графами

## Перевірені кандидати

| Локальне поняття | Wikidata | Відношення | Впевненість | Статус | Опис Wikidata |
|---|---|---|---:|---|---|
| `TransportSystem` | [Q178512](https://www.wikidata.org/wiki/Q178512) | closeMatch | 0.80 | verified | shared transportation service for use by the general public |
| `Network_Lviv` | [Q36036](https://www.wikidata.org/wiki/Q36036) | exactMatch | 0.97 | verified | capital city of Lviv Oblast in western Ukraine |
| `Tram` | [Q3407658](https://www.wikidata.org/wiki/Q3407658) | closeMatch | 0.90 | verified | public transport vehicle running on rails predominantly located on streets |
| `Bus` | [Q5638](https://www.wikidata.org/wiki/Q5638) | closeMatch | 0.95 | verified | large road vehicle for transporting people |
| `GTFSDataset` | [Q5532250](https://www.wikidata.org/wiki/Q5532250) | exactMatch | 0.72 | verified | defines a common format for public transportation schedules and associated geographic information |
| `GTFSDataset` | [Q113379415](https://www.wikidata.org/wiki/Q113379415) | closeMatch | 0.72 | verified | A feed in the General Transit Feed Specification format |
| `Stop` | [Q548662](https://www.wikidata.org/wiki/Q548662) | closeMatch | 0.88 | verified | designated place of stopping a vehicle of public transportation for the purpose of allowing passengers to embark or disembark |
| `Stop_Vokzal` | [Q4271066](https://www.wikidata.org/wiki/Q4271066) | closeMatch | 0.25 | rejected | bus station in Ukraine |
| `Network_Lviv` | [Q164193](https://www.wikidata.org/wiki/Q164193) | closeMatch | 0.30 | rejected | administrative division (oblast) in western Ukraine |

Підтверджено: **7**, відхилено: **2**. Джерело перевірки: Wikidata API `wbgetentities` (V1), результати — `results/wikidata_verification.json`.

## Відхилені зв’язки

- `mm:Network_Lviv` ↔ `wd:Q164193` (Lviv Oblast): область є адміністративною одиницею, а не транспортною мережею міста; `closeMatch` відхилено.
- `mm:Stop_Vokzal` ↔ `wd:Q4271066` (Lviv Bus terminal): автобусний термінал не тотожний пересадочній зупинці «Вокзал»; `sameAs`/`closeMatch` відхилено.

## Federated-запит

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

Результат: 7 рядків (`mm:Bus`, `mm:GTFSDataset` ×2, `mm:Network_Lviv`, `mm:Stop`, `mm:Tram`, `mm:TransportSystem`) з англійськими label із Wikidata.

Wikidata повертає 403 для HTTP-клієнта Jena без User-Agent, тому запит виконується через локальний `scripts/wikidata_proxy.py`, який лише додає заголовок `User-Agent`; upstream — `https://query.wikidata.org/sparql`.
