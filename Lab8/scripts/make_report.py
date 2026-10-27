# -*- coding: utf-8 -*-
"""Генерує звіт ЛР8 у DOCX та конвертує його в ODT/PDF."""
import csv, json, shutil, subprocess, sys
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from rdflib import Graph
from kb8 import ROOT, DATA, RESULTS, MODELS, QUERIES, SHAPES, CLAIMS, LLM, DOCS

OUT_BASE = "СЗтУЗ_Лаб8_Невмержицький_Максим-ФЕІ46"
FRIENDLY = "Лабораторна робота №8 — RDF-сховище та SPARQL-запити"

def clean_text(value):
    return str(value).replace("`", "")

def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_margins(table, top=48, bottom=48, left=48, right=48):
    tblPr = table._tbl.tblPr
    mar = OxmlElement('w:tblCellMar')
    for side, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        el = OxmlElement(f'w:{side}'); el.set(qn('w:w'), str(val)); el.set(qn('w:type'), 'dxa'); mar.append(el)
    tblPr.append(mar)

def add_table(doc, headers, rows, widths=None, font_size=None, header_fill="E6E6E6", align_center_cols=None, max_width=16.9):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    if font_size is None:
        font_size = 14 if len(headers) <= 3 else (12 if len(headers) == 4 else (11 if len(headers) == 5 else (10 if len(headers) == 6 else 9)))
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        run = p.add_run(clean_text(h)); run.bold = True; run.font.size = Pt(font_size); run.font.color.rgb = RGBColor(0,0,0)
        run.font.name = "Times New Roman"
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
        set_cell_bg(hdr[i], header_fill)
    trPr = table.rows[0]._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader'); tblHeader.set(qn('w:val'), 'true'); trPr.append(tblHeader)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            clean = clean_text(val).replace("✅", "виконано").replace("❌", "не виконано")
            run = p.add_run(clean); run.font.size = Pt(font_size); run.font.name = "Times New Roman"
            p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            if align_center_cols and i in align_center_cols:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        trPr = table.rows[-1]._tr.get_or_add_trPr()
        cantSplit = OxmlElement('w:cantSplit'); cantSplit.set(qn('w:val'), 'true'); trPr.append(cantSplit)
    if widths:
        scale = min(1.0, max_width / sum(widths))
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w * scale)
    set_cell_margins(table)
    return table

def add_caption(doc, text, size=14):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(clean_text(text)); run.bold = True; run.font.size = Pt(size); run.font.name = "Times New Roman"

def add_code(doc, text, size=8.5):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.3); p.paragraph_format.right_indent = Cm(0.3)
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(5)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    lines = str(text).split("\n")
    for i, line in enumerate(lines):
        run = p.add_run(line)
        run.font.name = "Courier New"; run.font.size = Pt(size)
        if i < len(lines)-1: run.add_break()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), 'F2F3F4')
    p._p.get_or_add_pPr().append(shd)

def h1(doc, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True; p.paragraph_format.line_spacing = 1.0
    run = p.add_run(clean_text(text)); run.font.name = "Times New Roman"; run.font.size = Pt(14); run.bold = True
    run.font.color.rgb = RGBColor(0,0,0)

def h2(doc, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True; p.paragraph_format.line_spacing = 1.0
    run = p.add_run(clean_text(text)); run.font.name = "Times New Roman"; run.font.size = Pt(14); run.bold = True
    run.font.color.rgb = RGBColor(0,0,0)

def para(doc, text, bold=False, size=14, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=3):
    p = doc.add_paragraph(); p.alignment = align
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(space_after); p.paragraph_format.line_spacing = 1.0
    run = p.add_run(clean_text(text)); run.bold = bold; run.font.size = Pt(size); run.font.name = "Times New Roman"
    return p

def no_indent(doc, text, size=14, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, space_after=0):
    p = doc.add_paragraph(); p.alignment = align; p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(clean_text(text)); run.font.size = Pt(size); run.bold = bold; run.font.name = "Times New Roman"
    return p

def bullet(doc, text, size=14):
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(clean_text(text)); run.font.size = Pt(size); run.font.name = "Times New Roman"
    p.paragraph_format.space_after = Pt(2); p.paragraph_format.line_spacing = 1.0

def add_picture_centered(doc, image, width_cm=16.0):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(image), width=Cm(width_cm))

def set_portrait(section):
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21.0); section.page_height = Cm(29.7)
    section.left_margin = Cm(2.0); section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0); section.bottom_margin = Cm(2.0)

def set_landscape(section):
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Cm(29.7); section.page_height = Cm(21.0)
    section.left_margin = Cm(2.0); section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0); section.bottom_margin = Cm(2.0)

def new_section(doc, landscape=False):
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    if landscape: set_landscape(sec)
    else: set_portrait(sec)
    return sec

def load():
    q = json.loads((RESULTS / "query_results.json").read_text(encoding="utf-8"))
    sh = json.loads((RESULTS / "shacl_summary.json").read_text(encoding="utf-8"))
    t2s = json.loads((RESULTS / "t2s_results.json").read_text(encoding="utf-8"))
    wd = json.loads((RESULTS / "wikidata_verification.json").read_text(encoding="utf-8"))
    stats = json.loads((RESULTS / "data_stats.json").read_text(encoding="utf-8"))
    count = json.loads((RESULTS / "triple_count.json").read_text(encoding="utf-8"))
    total = count["results"]["bindings"][0]["count"]["value"]
    claims = list(csv.DictReader((CLAIMS / "claims.csv").open(encoding="utf-8-sig")))
    return q, sh, t2s, wd, stats, total, claims

def mark(v):
    return "так" if v else "ні"

def build():
    q, sh, t2s, wd, stats, total, claims = load()
    qr = {r["id"]: r for r in q["queries"]}
    before, after = t2s["summary"]["before"], t2s["summary"]["after"]
    g_data = Graph().parse(DATA / "kb.ttl", format="turtle")
    g_links = Graph().parse(DATA / "links.ttl", format="turtle")
    g_rej = Graph().parse(DATA / "links_rejected.ttl", format="turtle")
    verified = sum(1 for c in claims if c["status"] == "verified")
    rejected = sum(1 for c in claims if c["status"] == "rejected")

    doc = Document()
    st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(14)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    st.paragraph_format.line_spacing = 1.0; st.paragraph_format.space_after = Pt(0)
    for name in ["Heading 1", "Heading 2", "Heading 3"]:
        h = doc.styles[name]; h.font.name = "Times New Roman"; h.font.color.rgb = RGBColor(0,0,0); h.font.size = Pt(14)
    set_portrait(doc.sections[0])

    no_indent(doc, "Міністерство освіти і науки України", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "Львівський національний університет імені Івана Франка", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "Факультет електроніки та комп’ютерних технологій", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "Кафедра системного проєктування", 14, WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(8): doc.add_paragraph()
    no_indent(doc, "Звіт про виконання лабораторної роботи №8", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "з курсу “Сховища знань та управління знаннями”", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "“RDF-сховище та SPARQL-запити”", 14, WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(9): doc.add_paragraph()
    no_indent(doc, "Виконав:", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc, "студент групи ФЕІ-46с", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc, "Невмержицький Максим Миколайович", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc, "Перевірив:", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc, "асистент Цудзенко Юрій Євгенович", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    for _ in range(11): doc.add_paragraph()
    no_indent(doc, "Львів-2026", 14, WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_page_break()

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.space_after = Pt(3); p.paragraph_format.line_spacing = 1.0
    r = p.add_run("Мета роботи: "); r.bold = True; r.font.size = Pt(14); r.font.name = "Times New Roman"
    r = p.add_run("експортувати онтологію та індивідів ЛР7 у RDF, завантажити їх у триплстор, "
                  "виконати SPARQL-запити до компетентнісних питань, описати SHACL-форми з навмисними дефектами, "
                  "оцінити text-to-SPARQL і перевірити зв’язки з відкритими графами.")
    no_indent(doc, "Хід роботи", 14, WD_ALIGN_PARAGRAPH.CENTER, bold=True, space_after=3)
    para(doc, "Робота продовжує ЛР4–ЛР7. У ЛР7 створено OWL-онтологію предметної області «Інтелектуальне "
              "управління міською мобільністю»: 58 класів, 48 object properties, 25 data properties, "
              "52 індивіди та 10 CQ. У ЛР8 цей граф експортовано в Turtle, завантажено в Apache Jena Fuseki, "
              "доповнено матеріалізованими типами HermiT, зв’язками з Wikidata та перевірено запитами, "
              "SHACL-формами й конвеєром text-to-SPARQL.")
    para(doc, "Інструменти: Python 3.14, rdflib 7.6.0, pySHACL 0.40.1, requests, Apache Jena Fuseki 4.10.0, "
              "Java 11, Graphviz, matplotlib і LibreOffice. Онтологія та ABox взяті з ЛР7 без повторної "
              "ручної формалізації; усі похідні дані генеруються скриптами.")
    add_caption(doc, "Таблиця 1 - Обов’язкові артефакти ЛР8")
    add_table(doc, ["Артефакт", "Призначення", "Фактичний стан"], [
        ["data/kb.ttl; data/kb.jsonld", "RDF-сховище та JSON-LD", f"{len(g_data)} трійок; {stats['jsonld_entities']} типізованих сутностей"],
        ["queries/*.rq", "SPARQL-запити до CQ", f"{len(q['queries'])} запитів (11 змістовних + 1 оптимізований)"],
        ["shapes/shapes.ttl", "SHACL-форми", f"{sh['shapes']} NodeShape, {sh['property_shapes']} property shapes"],
        ["data/kb_invalid.ttl", "Набір із 3 дефектами", f"{sh['invalid']['violations']} порушення"],
        ["tests/t2s.jsonl", "15 питань text-to-SPARQL", "15 еталонів + before/after"],
        ["data/links.ttl; data/links_rejected.ttl", "Зв’язки з Wikidata", f"{wd['verified']} verified, {wd['rejected']} rejected"],
        ["docs/*.md", "Журнали та пояснення", "6 документів"],
        ["claims/claims.csv", "Твердження та верифікація", f"{len(claims)} тверджень"],
        ["llm_log/*", "Журнал LLM-експерта", "6 файлів"],
        ["README.md, requirements.txt", "Відтворення", "Markdown / pip"],
    ], widths=[5.4, 6.4, 5.1], font_size=8.2)

    # Result 1
    h1(doc, "Результат 1. RDF-дані у триплсторі")
    para(doc, "Онтологію та ABox ЛР7 об’єднано в один граф. До нього додано метадані версії, "
              "9 матеріалізованих type-тверджень HermiT і 7 підтверджених зв’язків із Wikidata. "
              "Матеріалізація потрібна для того, щоб CQ до `InterchangeStop`, `AccessibleStop`, `DelayedTrip` "
              "і `CongestedSegment` працювали в Fuseki без запуску reasoner на кожен запит.")
    add_caption(doc, "Таблиця 2 - Склад RDF-сховища")
    add_table(doc, ["Файл", "Трійок", "Роль"], [
        ["data/kb.ttl", len(g_data), "TBox + ABox + метадані + матеріалізовані типи"],
        ["data/links.ttl", len(g_links), "7 verified Wikidata-зв’язків"],
        ["data/links_rejected.ttl", len(g_rej), "2 rejected кандидати (audit trail)"],
        ["data/kb.jsonld", stats["jsonld_nodes"], f"JSON-LD-вузли; {stats['jsonld_entities']} типізованих сутностей"],
        ["Fuseki dataset ds", total, "Фактичний COUNT після завантаження трьох Turtle-файлів"],
    ], widths=[5.6, 2.7, 8.6], font_size=8.4, align_center_cols=[1])
    para(doc, "Завантаження виконано в Apache Jena Fuseki 4.10.0 (dataset `ds`, in-memory, порт 3030). "
              "Після чистого DELETE і повторного POST трьох файлів COUNT-запит повернув "
              f"{total} трійок. Різниця із сумою файлів ({len(g_data)}+{len(g_links)}+{len(g_rej)}) "
              "пояснюється дедуплікацією однакових трійок у default graph. Версія графа — 1.0, "
              "дата завантаження — 27.10.2026; журнал і команди збережено в docs/load_log.md.")
    add_code(doc, """PREFIX mm: <https://knowledge.uni.lviv.ua/mobility#>
SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }
# Fuseki: 1206
# data/kb.ttl: 1146; links.ttl: 47; links_rejected.ttl: 14""")
    para(doc, "JSON-LD-версія містить 185 типізованих сутностей, що перевищує вимогу ≥ 20. "
              "У ній збережено повний граф, а не лише вибірку, тому вона придатна для повторного "
              "завантаження в інші сховища. Префікси узгоджено з ЛР7: mm:, rdf:, rdfs:, owl:, xsd:, "
              "skos:, dcterms:, schema:, wd:, wdt:.")
    add_caption(doc, "Таблиця 3 - Ключові метрики RDF")
    add_table(doc, ["Показник", "Значення", "Вимога"], [
        ["Трійок у kb.ttl", len(g_data), "≥ 300"],
        ["Трійок у Fuseki", total, "≥ 300"],
        ["Типізованих сутностей JSON-LD", stats["jsonld_entities"], "≥ 20"],
        ["Підтверджених Wikidata-зв’язків", wd["verified"], "≥ 5"],
        ["Матеріалізованих типів", 9, "для CQ без reasoner"],
        ["Версія / дата", "1.0 / 2026-10-27", "є"],
    ], widths=[7.5, 4.5, 4.3], font_size=8.4, align_center_cols=[1])

    # Result 2
    h1(doc, "Результат 2. SPARQL-запити до CQ")
    para(doc, "Створено 11 змістовних запитів і один оптимізований варіант. Набір покриває SELECT, ASK, "
              "CONSTRUCT, агрегацію COUNT із GROUP BY, OPTIONAL, FILTER, property path і federated SERVICE "
              "до Wikidata. Усі запити виконано через Fuseki; результати, час і ручні перевірки збережено "
              "в results/query_results.json і results/query_timings.csv.")
    add_caption(doc, "Таблиця 4 - SPARQL-запити та результати")
    rows = []
    for r in q["queries"]:
        rows.append([r["id"], r["cq"], r["type"], r["count"], r["elapsed_ms"],
                     "так" if r["status"] == "PASS" else "ні",
                     "так" if r.get("manual", {}).get("status") == "PASS" else ("—" if r.get("manual", {}).get("status") == "not_checked" else "ні")])
    add_table(doc, ["ID", "CQ", "Тип", "Рядків / трійок", "Час, мс", "Статус", "Ручна перевірка"],
              rows, widths=[1.5, 1.6, 2.8, 2.8, 2.3, 2.0, 3.0], font_size=7.6,
              align_center_cols=[0, 1, 2, 3, 4, 5, 6])
    para(doc, "Ручно перевірено 8 запитів: Q01, Q02, Q04, Q06, Q08, Q09, Q10, Q11 (для Q10 звірено кількість "
              "трійок, для Q11 — склад Wikidata-пар). Усі перевірки збіглися з очікуваннями. "
              "Q03, Q05, Q07 залишено без ручної звірки, бо їхні результати повністю пояснюються "
              "фільтрами й OPTIONAL-семантикою.")
    h2(doc, "2.1. Ключові запити")
    para(doc, "Q01 демонструє простий SELECT за матеріалізованим класом; Q06 — агрегацію та оптимізацію; "
              "Q08 — property path; Q09 — ASK; Q10 — CONSTRUCT; Q11 — federated-запит.")
    add_code(doc, (QUERIES / "q01_interchange_stops.rq").read_text(encoding="utf-8"))
    add_code(doc, (QUERIES / "q08_route_stop_path.rq").read_text(encoding="utf-8"))
    add_code(doc, (QUERIES / "q10_construct_route_trip.rq").read_text(encoding="utf-8"))
    add_code(doc, (QUERIES / "q11_federated_wikidata.rq").read_text(encoding="utf-8"))
    h2(doc, "2.2. Оптимізація Q06")
    para(doc, "У baseline навмисно залишено два зайві join-и та COUNT(DISTINCT ?trip). "
              "Optimized прибирає ці triple patterns і рахує прямий `hasTrip`. Обидва запити повертають "
              "однакові 3 рядки: Route_9 — 2, Route_25 — 1, Route_31 — 1.")
    add_code(doc, (QUERIES / "q06_trip_counts_by_route.rq").read_text(encoding="utf-8"))
    add_code(doc, (QUERIES / "q06_trip_counts_by_route_opt.rq").read_text(encoding="utf-8"))
    add_caption(doc, "Таблиця 5 - Порівняння часу Q06")
    add_table(doc, ["Вимірювання", "Baseline, мс", "Optimized, мс", "Прискорення"], [
        ["HTTP + Fuseki, 10 запусків", q["timing"]["baseline_median_ms"], q["timing"]["optimized_median_ms"], f"×{q['timing']['http_speedup']}"],
        ["rdflib in-process, 30 запусків", q["timing"]["inprocess_baseline_median_ms"], q["timing"]["inprocess_optimized_median_ms"], f"×{q['timing']['inprocess_speedup']}"],
    ], widths=[6.4, 3.4, 3.4, 2.8], font_size=8.4, align_center_cols=[1, 2, 3])
    add_picture_centered(doc, MODELS / "query_timing.png", 15.0)
    add_caption(doc, "Рис. 1 - Час baseline та optimized Q06")
    para(doc, "На малому графі HTTP-час майже не відрізняється, бо домінує мережевий overhead; "
              "in-process вимірювання показує стабільніше прискорення. Для великого графа саме "
              "зменшення кількості join-ів і відмова від DISTINCT дають основний ефект.")
    add_caption(doc, "Таблиця 6 - Ручна перевірка запитів")
    add_table(doc, ["ID", "Що перевірено", "Очікування", "Факт", "Статус"], [
        ["Q01", "пересадочні зупинки", "2: Rynok, Vokzal", "2", "так"],
        ["Q02", "маршрути на Вокзалі", "3: 9, 25, 31", "3", "так"],
        ["Q04", "рейс зі станом затримки", "Trip_9_0800", "Trip_9_0800", "так"],
        ["Q06", "кількість рейсів", "9:2, 25:1, 31:1", "9:2, 25:1, 31:1", "так"],
        ["Q08", "property path", "3 пари Route_9–Stop", "3", "так"],
        ["Q09", "ASK доступності", "true", "true", "так"],
        ["Q10", "CONSTRUCT", "12 трійок", "12", "так"],
        ["Q11", "federated Wikidata", "7 рядків", "7", "так"],
    ], widths=[1.2, 4.6, 4.6, 4.2, 1.8], font_size=7.8, align_center_cols=[0, 4])

    # Result 3
    h1(doc, "Результат 3. SHACL-валідація")
    para(doc, "Створено 7 NodeShape із 26 property shapes та 158 трійками SHACL-обмежень. "
              "Використано `minCount`, `maxCount`, `datatype`, `class`, `pattern`, `minInclusive`, "
              "`maxInclusive`, `nodeKind` і `in`. Валідний набір `data/kb.ttl` проходить без порушень; "
              "дефектний `data/kb_invalid.ttl` містить рівно три навмисні дефекти та дає три порушення.")
    add_caption(doc, "Таблиця 7 - SHACL-форми")
    add_table(doc, ["Форма", "Цільовий клас", "Ключові обмеження"], [
        ["StopShape", "mm:Stop", "stopId pattern, stopName, координати, boolean, маршрут"],
        ["TripShape", "mm:Trip", "tripId pattern, рівно один маршрут/стан/ТЗ, start/end"],
        ["RouteShape", "mm:TransportRoute", "routeId, routeType in (0,3,11), servesStop, hasTrip"],
        ["DelayShape", "mm:Delay", "delayMinutes 0–120, measurementOf, measuredBy"],
        ["EventShape", "mm:Event", "eventTime xsd:dateTime, affectsSegment"],
        ["RecommendationShape", "mm:Recommendation", "recommends, forPassenger, decision"],
        ["AgencyShape", "mm:TransportAgency", "agencyName, operatesTrip"],
    ], widths=[4.0, 4.4, 8.5], font_size=8.0)
    add_code(doc, """mm:DelayShape a sh:NodeShape ;
  sh:targetClass mm:Delay ;
  sh:property [
    sh:path mm:delayMinutes ;
    sh:minCount 1 ; sh:maxCount 1 ;
    sh:datatype xsd:integer ;
    sh:minInclusive 0 ; sh:maxInclusive 120
  ] .""")
    add_caption(doc, "Таблиця 8 - Результати pySHACL")
    add_table(doc, ["Набір", "Conforms", "Порушень", "Коментар"], [
        ["data/kb.ttl", "true" if sh["valid"]["conforms"] else "false", sh["valid"]["violations"], "повний валідний граф"],
        ["data/kb_invalid.ttl", "false" if not sh["invalid"]["conforms"] else "true", sh["invalid"]["violations"], "3 навмисні дефекти"],
    ], widths=[4.5, 2.6, 2.6, 7.2], font_size=8.4, align_center_cols=[0, 1, 2])
    add_caption(doc, "Таблиця 9 - Виявлені порушення")
    add_table(doc, ["Фокус", "Шлях", "Повідомлення"],
              [[i["focus"].split("#")[-1], i["path"].split("#")[-1], i["message"]] for i in sh["invalid"]["items"]],
              widths=[4.0, 3.0, 9.9], font_size=7.8)
    add_picture_centered(doc, MODELS / "shacl_results.png", 10.5)
    add_caption(doc, "Рис. 2 - Кількість порушень SHACL")
    para(doc, "SHACL обрано тому, що ці обмеження є контрактом якості даних, а не логічними аксіомами. "
              "OWL 2 працює у відкритому світі: відсутність трійки не є порушенням, а reasoner може додати "
              "висновок. SHACL перевіряє саме поданий граф і повертає зрозумілий звіт із focus node, path і "
              "message. Тому `minCount` для стану рейсу, `pattern` для stopId і `minInclusive` для затримки "
              "природно виражаються формами; OWL/HermiT залишається для класифікації та виведення нових типів.")

    # Result 4
    h1(doc, "Результат 4. Text-to-SPARQL з оцінкою")
    para(doc, "Побудовано 15 питань різної складності. Конвеєр: підказка зі схемою → LLM → SPARQL-парсер "
              "rdflib → перевірка, що всі mm-терміни оголошені в TBox → виконання в Fuseki з LIMIT 100 → "
              "порівняння множини рядків з еталоном. Для кожного питання збережено еталонний запит, "
              "слабку та покращену чернетки.")
    add_picture_centered(doc, MODELS / "pipeline.png", 16.0)
    add_caption(doc, "Рис. 3 - Конвеєр text-to-SPARQL")
    add_caption(doc, "Таблиця 10 - Метрики до і після покращення підказки")
    add_table(doc, ["Варіант", "Синтаксично коректних", "Лише зі схеми", "Правильний результат"], [
        ["prompt v1 (до)", f"{before['syntax']}/15", f"{before['schema']}/15", f"{before['correct']}/15"],
        ["prompt v2 (після)", f"{after['syntax']}/15", f"{after['schema']}/15", f"{after['correct']}/15"],
    ], widths=[4.6, 4.2, 4.0, 4.1], font_size=8.6, align_center_cols=[1, 2, 3])
    add_picture_centered(doc, MODELS / "t2s_metrics.png", 15.0)
    add_caption(doc, "Рис. 4 - Метрики text-to-SPARQL до і після покращення")
    doc.add_page_break()
    add_caption(doc, "Таблиця 11 - 15 питань і результати")
    rows = []
    for r in t2s["records"]:
        b, a = r["variants"]["before"], r["variants"]["after"]
        rows.append([r["id"], r["difficulty"], r["question"], f"{mark(b['syntax'])}/{mark(b['schema'])}/{mark(b['correct'])}",
                     f"{mark(a['syntax'])}/{mark(a['schema'])}/{mark(a['correct'])}"])
    add_table(doc, ["ID", "Складність", "Питання", "До: синт./схема/результат", "Після: синт./схема/результат"],
              rows, widths=[1.4, 1.8, 8.6, 3.5, 3.5], font_size=7.1, align_center_cols=[0, 1, 3, 4])
    para(doc, "До покращення слабка підказка не містила переліку властивостей, domain/range і прикладів. "
              "Тому 4 запити містили незадекларовані mm-терміни, а частина решти була семантично хибною. "
              "Після додавання схеми, правил напрямку властивостей, типів літералів і прикладів усі 15 "
              "запитів пройшли парсер, перевірку схеми та дали еталонний результат.")
    add_caption(doc, "Таблиця 12 - Аналіз п’яти типових помилок")
    add_table(doc, ["ID", "Помилка", "Класифікація", "Виправлення"], [
        ["T2S01", "вигадана властивість mm:hasInterchange", "schema", "клас mm:InterchangeStop"],
        ["T2S02", "неправильний напрямок servedByRoute", "semantic", "mm:servesStop"],
        ["T2S04", "рядок \"true\" замість boolean", "datatype", "true без лапок"],
        ["T2S07", "COUNT без GROUP BY", "aggregation", "GROUP BY ?route"],
        ["T2S12", "OPTIONAL замість обов’язкового join", "logic", "конкретний Congestion_Horodotska"],
    ], widths=[1.4, 8.2, 3.0, 4.3], font_size=7.6)
    para(doc, "Окремо проаналізовано шосту помилку T2S15: `mm:describes` замінено на `mm:datasetDescribes`. "
              "Усі шість помилок класифіковано за рівнем: синтаксис, схема, типи, напрямок властивості, "
              "логіка агрегації та логіка OPTIONAL. Після prompt v2 метрики: 15/15 синтаксис, 15/15 схема, "
              "15/15 правильний результат.")

    # Result 5
    h1(doc, "Результат 5. Зв’язки з відкритими графами")
    para(doc, "Для 7 локальних понять знайдено відповідники у Wikidata. Кожен зв’язок має тип "
              "`skos:exactMatch` або `skos:closeMatch`, рівень впевненості, дату, джерело та пояснення. "
              "Ще 2 кандидати відхилено після V1-перевірки; вони збережені в audit trail, але не беруть "
              "участі у federated-запиті.")
    add_caption(doc, "Таблиця 13 - Зв’язки з Wikidata")
    add_table(doc, ["Локальне", "Wikidata", "Відношення", "Впевненість", "Статус"],
              [[x["local"], x["qid"], x.get("relation", "closeMatch"), x["confidence"], x["status"]] for x in wd["items"]],
              widths=[4.0, 3.0, 3.3, 2.8, 2.8], font_size=7.8, align_center_cols=[1, 2, 3, 4])
    para(doc, "Підтверджено 7 зв’язків, відхилено 2. Відхилені: `mm:Network_Lviv` ↔ `wd:Q164193` "
              "(Lviv Oblast — адміністративна одиниця, не транспортна мережа) і `mm:Stop_Vokzal` ↔ "
              "`wd:Q4271066` (Lviv Bus terminal — окремий автобусний термінал, не зупинка «Вокзал»). "
              "Перевірку виконано через Wikidata API `wbgetentities`; результати — "
              "results/wikidata_verification.json. Для `GTFSDataset` збережено два зв’язки: "
              "`exactMatch` із Q5532250 (специфікація GTFS) і `closeMatch` із Q113379415 "
              "(профіль GTFS-DCAT), тому в таблиці це поняття зустрічається двічі.")
    add_caption(doc, "Таблиця 14 - Federated-запит до Wikidata")
    add_code(doc, (QUERIES / "q11_federated_wikidata.rq").read_text(encoding="utf-8"))
    add_table(doc, ["Локальне", "Wikidata", "Label"],
              [[r["local"], r["external"], r["externalLabel"]] for r in qr["Q11"]["rows"]],
              widths=[4.8, 5.4, 6.7], font_size=7.8)
    para(doc, "Fuseki не може напряму звернутися до Wikidata: HTTP-клієнт Jena без User-Agent отримує 403. "
              "Тому використано локальний `scripts/wikidata_proxy.py`, який додає лише заголовок User-Agent "
              "і передає запит на `https://query.wikidata.org/sparql`. Це не змінює семантику federated-запиту: "
              "зовнішній граф залишається Wikidata. У запиті використано `VALUES` із 7 QID, локальні "
              "`skos:exactMatch`/`closeMatch` і `SERVICE`; результат — 7 рядків.")
    add_code(doc, "403 Please set a user-agent and respect our robot policy — Wikidata\n"
                  "SERVICE <http://127.0.0.1:3031/sparql> — локальний проксі, upstream Wikidata")

    # LLM protocol
    h1(doc, "LLM-експерт, твердження та доброчесність")
    para(doc, "Усі взаємодії з LLM задокументовано. Використано модель opencode/deepseek-v4.1-flash-free, "
              "temperature 0.2, seed 42, дві версії підказки. Сирий вихід збережено в llm_log/, рішення "
              "людини — у decisions.csv. Ключі API не зберігаються; персональні дані не передавалися.")
    add_caption(doc, "Таблиця 15 - Протокол LLM")
    add_table(doc, ["Артефакт", "Зміст"], [
        ["llm_log/2026-10-27_prompt_v1.md", "слабка підказка без схеми властивостей"],
        ["llm_log/2026-10-27_prompt_v2.md", "схема, правила, приклади"],
        ["llm_log/2026-10-27_raw_before.jsonl", "15 сирих запитів до покращення"],
        ["llm_log/2026-10-27_raw_after.jsonl", "15 сирих запитів після покращення"],
        ["llm_log/2026-10-27_decisions.csv", "рішення людини по кожному запиту"],
        ["claims/claims.csv", f"{len(claims)} тверджень; {verified} verified, {rejected} rejected"],
    ], widths=[7.4, 9.0], font_size=8.2)
    para(doc, f"Частка підтверджених тверджень — {verified}/{len(claims)} ({verified/len(claims):.1%}). "
              "Відхилено два твердження: тезу про достатність слабкої підказки та тезу про те, що "
              "Wikidata приймає стандартний User-Agent Jena. Обидва відхилення мають пояснення в claims.csv.")
    add_caption(doc, "Таблиця 16 - Ключові твердження")
    key_ids = ["L8-01", "L8-02", "L8-07", "L8-08", "L8-11", "L8-13", "L8-15"]
    key_claims = [c for c in claims if c["id"] in key_ids]
    add_table(doc, ["ID", "Твердження", "Статус", "Коментар"],
              [[c["id"], c["claim"], c["status"], c["comment"]] for c in key_claims],
              widths=[1.4, 7.6, 2.2, 5.2], font_size=7.4)

    h1(doc, "Обмеження та інтерпретація")
    for txt in [
        "Граф ЛР8 навчальний і малий (1206 трійок), тому HTTP-тайминги Q06 сильно залежать від мережевого overhead; in-process вимірювання репрезентативніше для оцінки самого запиту.",
        "Federated-запит залежить від доступності Wikidata та локального проксі; проксі не кешує відповіді й не змінює семантику SERVICE, але є інфраструктурною залежністю.",
        "SHACL перевіряє закритий зріз даних, тоді як OWL 2 працює у відкритому світі; тому SHACL-форми не замінюють OWL-аксіоми, а доповнюють їх контрактом якості.",
        "Еталони text-to-SPARQL і ручні перевірки запитів сформовані автором; вони не є незалежним бенчмарком, але повністю відтворювані за збереженими JSONL-файлами.",
    ]:
        bullet(doc, txt)

    h1(doc, "Відтворення")
    para(doc, "Порядок команд відповідає README.md. Перед запуском запитів має бути активний Fuseki на порту 3030; "
              "для Q11 — проксі на порту 3031. Усі шляхи — відносно каталогу Lab8.")
    add_caption(doc, "Таблиця 17 - Команди відтворення")
    add_table(doc, ["Крок", "Команда"], [
        ["Залежності", "pip install -r requirements.txt"],
        ["Дані", "python scripts/build_data.py"],
        ["Зв’язки", "python scripts/build_links.py"],
        ["Дефектний набір", "python scripts/build_invalid.py"],
        ["Запити", "python scripts/run_queries.py"],
        ["SHACL", "python scripts/validate_shacl.py"],
        ["T2S", "python scripts/build_t2s.py; python scripts/run_t2s.py"],
        ["Рисунки", "python scripts/visualize.py"],
        ["Документація", "python scripts/build_docs.py"],
        ["Звіт", "python scripts/make_report.py"],
    ], widths=[4.0, 12.4], font_size=8.4)

    h1(doc, "Висновки")
    for txt in [
        "Онтологію та ABox ЛР7 експортовано в RDF; Fuseki підтвердив 1206 трійок, JSON-LD містить 185 типізованих сутностей.",
        "11 змістовних SPARQL-запитів покривають SELECT, ASK, CONSTRUCT, агрегацію, OPTIONAL, FILTER, property path і federated SERVICE; 8 запитів перевірено вручну.",
        "SHACL-форми (7 NodeShape, 26 property shapes, 158 обмежень) проходять на валідному наборі та виявляють 3 порушення на дефектному.",
        "Text-to-SPARQL після покращення підказки перейшов із 1/15 до 15/15 правильних результатів; конвеєр включає парсер, перевірку схеми та LIMIT.",
        "Знайдено 7 підтверджених Wikidata-зв’язків, 2 кандидати відхилено; federated-запит повертає 7 рядків.",
        "Усі артефакти, журнали LLM, твердження та команди відтворення збережено в репозиторії; робота готова до захисту.",
    ]:
        bullet(doc, txt)

    h1(doc, "Джерела")
    for src in [
        "W3C. RDF 1.1 Concepts and Abstract Syntax. 2014.",
        "W3C. SPARQL 1.1 Query Language. 2013.",
        "W3C. Shapes Constraint Language (SHACL). 2017.",
        "W3C. OWL 2 Web Ontology Language. 2012.",
        "Apache Jena Fuseki 4.10.0; RDFLib 7.6.0; pySHACL 0.40.1 Documentation.",
        "GTFS Reference; SIRI; schema.org; Wikidata API (wbgetentities).",
        "ЛР07_завдання.pdf; матеріали курсу «Сховища знань та управління знаннями», 2026–2027.",
    ]:
        bullet(doc, src, size=11.5)

    out_docx = ROOT / f"{OUT_BASE}.docx"
    doc.save(out_docx)
    print("saved", out_docx)
    return out_docx

def convert(docx_path):
    subprocess.run(["soffice", "--headless", "--convert-to", "odt", "--outdir", str(ROOT), str(docx_path)], check=True)
    odt = ROOT / f"{OUT_BASE}.odt"
    friendly = ROOT / f"{FRIENDLY}.odt"
    if odt.exists():
        shutil.copy2(odt, friendly)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(ROOT), str(docx_path)], check=True)
    pdf = ROOT / f"{OUT_BASE}.pdf"
    print("odt", odt, "friendly", friendly, "pdf", pdf)
    return pdf

if __name__ == "__main__":
    p = build()
    convert(p)
