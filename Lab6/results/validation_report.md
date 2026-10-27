# Результат перевірки триплетів LLM

| Показник | Значення |
|---|---|
| Усього триплетів | 50 |
| Валідних за схемою | 50 |
| Підтверджених цитат | 44/50 (88.0%) |
| Відношень з каталогу | 49/50 |
| Типів domain/range без порушень | 48/50 |
| Повністю валідних (прийнято людиною) | 40/50 |
| Відхилено | 10/50 |

## Помилки за типами

| Тип | Кількість |
|---|---:|
| `direction_error` | 1 |
| `missing_evidence` | 1 |
| `quote_not_found` | 5 |
| `type_violation` | 2 |
| `unknown_relation` | 1 |

## Перелік відхилених триплетів

| ID | Помилка | Деталі |
|---|---|---|
| L41 | `quote_not_found` | quote_not_found |
| L42 | `quote_not_found` | quote_not_found |
| L43 | `quote_not_found` | quote_not_found |
| L44 | `quote_not_found` | quote_not_found |
| L45 | `quote_not_found` | quote_not_found |
| L46 | `missing_evidence` | missing_evidence |
| L47 | `type_violation` | domain_violation |
| L48 | `type_violation` | domain_violation, range_violation |
| L49 | `unknown_relation` | unknown_relation |
| L50 | `direction_error` | direction_error |

Скрипт: `scripts/validate_triples.py`. Повний машинний звіт: `results/validation_report.json`.