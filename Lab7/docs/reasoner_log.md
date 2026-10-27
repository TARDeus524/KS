# HermiT — журнал перевірки

- Версія онтології: 1.0
- TBox: `models/onto.owl`
- ABox: `models/onto_data.ttl`
- Об’єднаний файл: `build/expert_merged.rdf`
- JAR: `/tmp/opencode/lab6venv/lib/python3.14/site-packages/owlready2/hermit/HermiT.jar`

## Консистентність

```text
http://www.w3.org/2002/07/owl#Thing is satisfiable.

```

## Класифікація

- Класів: 58
- Object properties: 48
- Data properties: 25
- Індивідів: 52
- Індивідів із ≥3 властивостями: 24
- Середня кількість властивостей: 3.37
- Виведених type-тверджень: 165
- Виведених членств у визначених класах: 6
- Виведених property-тверджень: 21

## Виведені факти

- `Stop_Rynok` rdf:type `InterchangeStop`
- `Stop_Vokzal` rdf:type `InterchangeStop`
- `Stop_Politekhnika` rdf:type `AccessibleStop`
- `Stop_Vokzal` rdf:type `AccessibleStop`
- `Seg_Vokzal_Rynok` rdf:type `CongestedSegment`
- `Trip_9_0800` rdf:type `DelayedTrip`
- `Forecast_9_Peak` rdf:type `MobilitySystem`
- `System_Lviv` rdf:type `MobilitySystem`
- `Trip_9_0830` rdf:type `MobilitySystem`
- `Trip_9_0800` rdf:type `MobilitySystem`
- `Trip_31_0700` rdf:type `MobilitySystem`
- `Trip_25_0815` rdf:type `MobilitySystem`
- `Network_Lviv` rdf:type `MobilitySystem`
- `GPS_2501` rdf:type `MobilitySystem`
- `State_OnTime_9_0830` rdf:type `MobilitySystem`
- `State_OnTime_31` rdf:type `MobilitySystem`
- `State_OnTime_25` rdf:type `MobilitySystem`
- `Stop_Rynok` rdf:type `MobilitySystem`
- `Stop_Vokzal` rdf:type `MobilitySystem`
- `Stop_Politekhnika` rdf:type `MobilitySystem`

## Перевірка LLM-чернетки

```text
http://www.w3.org/2002/07/owl#Thing is satisfiable.

```

## Навмисна суперечність

Додано `mm:Bus_2501 rdf:type mm:Tram` за наявного `mm:Bus_2501 a mm:Bus` і `owl:AllDisjointClasses` для Bus/Tram/Trolleybus.

CLI HermiT: returncode=1

```text
Exception in thread "main" org.semanticweb.owlapi.reasoner.InconsistentOntologyException: Inconsistent ontology
	at org.semanticweb.HermiT.Reasoner.throwInconsistentOntologyExceptionIfNecessary(Unknown Source)
	at org.semanticweb.HermiT.Reasoner.checkPreConditions(Unknown Source)
	at org.semanticweb.HermiT.Reasoner.isSatisfiable(Unknown Source)
	at org.semanticweb.HermiT.cli.CommandLine$SatisfiabilityAction.run(Unknown Source)
	at org.semanticweb.HermiT.cli.CommandLine.main(Unknown Source)
```

Owlready2: `OwlReadyInconsistentOntologyError: `

## Висновок

Експертна онтологія консистентна; HermiT класифікує її та виводить нові типи. Навмисну суперечність локалізовано й усунено поверненням до `expert_merged.rdf`.
