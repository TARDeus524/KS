# Формалізація предметної області

## Простір назв

- `mm:` — `https://knowledge.uni.lviv.ua/mobility#`
- онтологія: `https://knowledge.uni.lviv.ua/mobility`
- ABox: `https://knowledge.uni.lviv.ua/mobility/data`
- зовнішній словник: `schema:` — `https://schema.org/`

## Принципи

1. Класи означено через genus + differentia; батьківський клас задає рід, `rdfs:comment` — ознаку.
2. Object properties мають domain/range; для більшості пар задано `owl:inverseOf`.
3. Data properties типізовано; для GTFS-полів дат/часу використано `xsd:string` через обмеження HermiT.
4. Визначені класи задано через `owl:equivalentClass` та `owl:intersectionOf`.
5. Диз’юнктність — 8 груп `owl:AllDisjointClasses`.

## Ключові аксіоми

- `Trip ⊑ ∃hasStopTime.StopTime`
- `TransportRoute ⊑ ∃servesStop.Stop`
- `NetworkSegment ⊑ ∀hasEvent.Event`
- `Recommendation ⊑ ∃recommends.TransportRoute`
- `Trip ⊑ =1 usesVehicle.Vehicle`
- `Trip ⊑ =1 operatedBy.TransportAgency`
- `StopTime ⊑ =1 atStop.Stop`
- `InterchangeStop ≡ Stop ⊓ ≥2 servedByRoute.TransportRoute`
- `AccessibleStop ≡ Stop ⊓ wheelchairAccessible = true`
- `CongestedSegment ≡ NetworkSegment ⊓ ∃hasEvent.Congestion`
- `DelayedTrip ≡ Trip ⊓ ∃hasState.DelayedState`

## Повторне використання

`schema:BusStop`, `schema:Route`, `schema:Trip`, `schema:Person`, `schema:Organization`,
`schema:Event`, `schema:Dataset`, `schema:Place` використано через `skos:closeMatch` і
`rdfs:seeAlso`. Повний `owl:imports` не застосовано, щоб не завантажувати зайві аксіоми
schema.org і зберегти локальну відтворюваність.
