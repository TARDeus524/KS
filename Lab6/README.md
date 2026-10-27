# ЛР6. Семантична мережа та концептуальна карта

Тематична область: **Інтелектуальне управління міською мобільністю**.
Робота продовжує ЛР4 (таксономія) і ЛР5 (семантична мережа).

## Структура артефактів

| Шлях | Призначення |
|---|---|
| `docs/cmap_focus.md` | фокусне питання, parking lot (55 понять), каталог 12 відношень, 7 CQ |
| `models/cmap_expert.drawio`, `.png`, `.dot` | експертна карта v1: 48 понять, 85 пропозицій, 5 крос-зв'язків |
| `models/triples_llm.jsonl` | 50 триплетів LLM із цитатами та статусом перевірки |
| `models/cmap_llm.png` | граф 40 прийнятих триплетів LLM |
| `docs/cmap_rubric.xlsx` | рубрика Новака для 3 карт, 2 оцінювачі, узгодженість, precision/recall |
| `models/cmap_v2.drawio`, `.png`, `.dot` | об'єднана карта v2: 55 понять, 106 пропозицій |
| `models/triples_final.csv` | 106 триплетів для ЛР7–ЛР9 (`s,p,o,source,status`) |
| `claims/claims.csv` | таблиця тверджень (18 записів, V1–V3) |
| `llm_log/` | підказка, сирий вихід, рішення людини, журнал |
| `data/texts/` | 3 тексти та `SOURCES.md` |
| `scripts/` | відтворювані скрипти побудови й перевірки |
| `results/` | машинні звіти перевірки цитат/типів і precision/recall |

## Відтворення з нуля

Потрібні Python 3.14+, Graphviz `dot`, пакет `openpyxl`.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/build_artifacts.py
python scripts/validate_triples.py
python scripts/evaluate_triples.py
python scripts/make_report.py
```

`build_artifacts.py` використовує фіксований seed у журналі LLM (`seed=42`) і не звертається до мережі.
Тексти вже збережено в `data/texts/`.

## Перевірка

- 50 триплетів LLM; 44/50 (88 %) цитат підтверджено дослівно.
- 40/50 триплетів прийнято після перевірки domain/range і цитат.
- 10 відхилено: 5 — цитата не знайдена, 1 — немає цитати, 2 — порушення domain/range, 1 — відношення поза каталогом, 1 — неправильний напрямок.
- Precision 0.800, recall 0.889, F1 0.842 на 45 твердженнях еталону.
