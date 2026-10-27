# Перевірка в Protégé / HermiT

## Відкриття

1. Protégé 5.6+ → File → Open → `models/onto.rdf`.
2. Переконатися, що в дереві класів є 58 класів і гілки `TransportNetwork`, `Vehicle`, `Trip`, `Actor`,
   `DataAsset`, `Sensor`, `Analytics`, `Event`, `TransportState`, `Measurement`.
3. Reasoner → HermiT → Start reasoner.

## Автоматична перевірка

```bash
/tmp/opencode/lab6venv/bin/python scripts/run_reasoner.py
```

Скрипт об’єднує `models/onto.owl` і `models/onto_data.ttl` у `build/expert_merged.rdf`,
запускає HermiT, матеріалізує висновки в `build/expert_inferred.ttl` і перевіряє
навмисну суперечність у `build/inconsistent.rdf`.

## Очікуваний результат

- `build/expert_merged.rdf` → `owl:Thing is satisfiable.`
- `build/expert_inferred.ttl` → 165 виведених type-тверджень, 21 property-твердження.
- `build/inconsistent.rdf` → `InconsistentOntologyException: Inconsistent ontology`.
- `docs/reasoner_log.md` містить повний журнал.

## Обмеження

HermiT не підтримує `xsd:date` і `xsd:time` з OWL 2 datatype map. GTFS-значення дат/часу
збережено як `xsd:string`; для повних моментів часу використано `xsd:dateTime`.
