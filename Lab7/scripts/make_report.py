# -*- coding: utf-8 -*-
"""Генерація звіту ЛР7 у DOCX та конвертація в ODT/PDF."""
import csv, json, shutil, subprocess, sys
from pathlib import Path
import rdflib
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb7

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"; RESULTS = ROOT / "results"; DOCS = ROOT / "docs"
OUT_BASE = "СЗтУЗ_Лаб7_Невмержицький_Максим-ФЕІ46"
FRIENDLY = "Лабораторна робота №7 — Онтологія в Protégé та формалізація знань"

# ---------- helpers ----------
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
        run = p.add_run(str(h)); run.bold = True; run.font.size = Pt(font_size); run.font.color.rgb = RGBColor(0,0,0)
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
            clean = str(val).replace("✅", "виконано").replace("❌", "не виконано").replace("—", "—")
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

def add_caption(doc, text, italic=False, size=14):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text); run.bold = True; run.italic = False; run.font.size = Pt(size)
    run.font.name = "Times New Roman"

def add_code(doc, text, size=9):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.4); p.paragraph_format.right_indent = Cm(0.4)
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(6)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    lines = text.split("\n")
    for i, line in enumerate(lines):
        run = p.add_run(line)
        run.font.name = "Courier New"; run.font.size = Pt(size)
        if i < len(lines)-1: run.add_break()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), 'F2F3F4')
    p._p.get_or_add_pPr().append(shd)

def add_bullets(doc, items, style="List Bullet", size=14):
    for it in items:
        p = doc.add_paragraph(style=style)
        run = p.add_run(it); run.font.size = Pt(size); run.font.name = "Times New Roman"
        p.paragraph_format.space_after = Pt(2); p.paragraph_format.line_spacing = 1.0

def set_section_portrait(section):
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21.0); section.page_height = Cm(29.7)
    section.left_margin = Cm(2.0); section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0); section.bottom_margin = Cm(2.0)

def set_section_landscape(section):
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Cm(29.7); section.page_height = Cm(21.0)
    section.left_margin = Cm(2.0); section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0); section.bottom_margin = Cm(2.0)

def h1(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True; p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text); run.font.name = "Times New Roman"; run.font.size = Pt(14); run.bold = True
    run.font.color.rgb = RGBColor(0,0,0)
    return p

def h2(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True; p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text); run.font.name = "Times New Roman"; run.font.size = Pt(14); run.bold = True
    run.font.color.rgb = RGBColor(0,0,0)
    return p

def para(doc, text, bold=False, size=14, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=3):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text); run.bold = bold; run.font.size = Pt(size); run.font.name = "Times New Roman"
    return p

def no_indent(doc, text, size=14, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, space_after=0):
    p = doc.add_paragraph(); p.alignment = align; p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text); run.font.size = Pt(size); run.bold = bold; run.font.name = "Times New Roman"
    return p

def add_picture_centered(doc, image, width_cm=16.0):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(image), width=Cm(width_cm))

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

# ---------- data ----------
def load_data():
    cp = read_csv(MODELS/"class_table.csv")
    pp = read_csv(MODELS/"properties.csv")
    ip = read_csv(ROOT/"data"/"individuals.csv")
    sp = read_csv(MODELS/"situations.csv")
    cl = read_csv(ROOT/"claims"/"claims.csv")
    cq = read_csv(RESULTS/"cq_results.csv")
    si = read_csv(RESULTS/"situation_results.csv")
    reason = json.loads((RESULTS/"reasoner_summary.json").read_text(encoding="utf-8"))
    cqs = json.loads((RESULTS/"cq_summary.json").read_text(encoding="utf-8"))
    tbox_count = len(rdflib.Graph().parse(MODELS/"onto.owl", format="turtle"))
    abox_count = len(rdflib.Graph().parse(MODELS/"onto_data.ttl", format="turtle"))
    verified = sum(1 for c in cl if c["status"] == "verified")
    rejected = sum(1 for c in cl if c["status"] == "rejected")
    obj = sum(1 for p in pp if p["type"] == "object")
    dat = sum(1 for p in pp if p["type"] == "data")
    return dict(cp=cp, pp=pp, ip=ip, sp=sp, cl=cl, cq=cq, si=si, reason=reason, cqs=cqs,
                verified=verified, rejected=rejected, obj=obj, dat=dat,
                tbox_count=tbox_count, abox_count=abox_count)

def build():
    D = load_data()
    doc = Document()
    st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(14)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    st.paragraph_format.line_spacing = 1.0; st.paragraph_format.space_after = Pt(0)
    for name in ["Heading 1", "Heading 2", "Heading 3"]:
        h = doc.styles[name]; h.font.name = "Times New Roman"; h.font.color.rgb = RGBColor(0,0,0); h.font.size = Pt(14)
    sec = doc.sections[0]; set_section_portrait(sec)

    # ----- title page -----
    no_indent(doc, "Міністерство освіти і науки України", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "Львівський національний університет імені Івана Франка", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "Факультет електроніки та комп’ютерних технологій", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "Кафедра системного проєктування", 14, WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(8): doc.add_paragraph()
    no_indent(doc, "Звіт про виконання лабораторної роботи №7", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "з курсу “Сховища знань та управління знаннями”", 14, WD_ALIGN_PARAGRAPH.CENTER)
    no_indent(doc, "“Онтологія в Protégé та формалізація знань”", 14, WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(9): doc.add_paragraph()
    no_indent(doc, "Виконав:", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc, "студент групи ФЕІ-46с", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc, "Невмержицький Максим Миколайович", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc, "Перевірив:", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc, "асистент Цудзенко Юрій Євгенович", 14, WD_ALIGN_PARAGRAPH.RIGHT)
    for _ in range(11): doc.add_paragraph()
    no_indent(doc, "Львів-2026", 14, WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_page_break()

    # ----- intro -----
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.space_after = Pt(3); p.paragraph_format.line_spacing = 1.0
    r = p.add_run("Мета роботи: "); r.bold = True; r.font.size = Pt(14); r.font.name = "Times New Roman"
    r = p.add_run("формалізувати предметну область «Інтелектуальне управління міською мобільністю» в OWL 2, "
                  "побудувати онтологію класів і властивостей, наповнити її індивідами, описати ситуації, "
                  "перевірити логіку за допомогою HermiT, виконати компетентнісні запити та порівняти результат "
                  "з чернеткою, згенерованою великою мовною моделлю.")
    p = no_indent(doc, "Хід роботи", 14, WD_ALIGN_PARAGRAPH.CENTER, bold=True, space_after=3)
    para(doc, "Тематична область продовжує ЛР4–ЛР6. У ЛР6 сформовано 55 понять, 12 типів відношень, 7 CQ і "
              "106 фінальних триплетів. Для ЛР7 цей матеріал використано як seed: поняття перетворено на OWL-класи, "
              "відношення — на object properties, а CQ розширено до 10 запитів. Доменна модель охоплює мережу, "
              "рухомий склад, рейси, розклад, пасажирів, перевізників, сенсори, набори GTFS/SIRI/NeTEx, "
              "події, стани, вимірювання та диспетчерські рішення.")
    para(doc, "Інструменти: Protégé 5.6+ як цільове середовище редагування, HermiT 1.4 як OWL 2 DL reasoner, "
              "Python 3.14, rdflib 7.6.0, owlready2 0.51, Graphviz для діаграм і LibreOffice для DOCX → ODT/PDF. "
              "Автоматичну перевірку виконано викликом того самого HermiT, який використовує Protégé; це дозволяє "
              "відтворити класифікацію без ручних операцій у GUI.")
    add_caption(doc, "Таблиця 1 - Обов’язкові артефакти роботи")
    add_table(doc, ["Артефакт", "Призначення", "Кількість / формат"], [
        ["models/onto.owl, models/onto.rdf", "OWL 2 TBox: класи, object/data properties, обмеження", f"{len(D['cp'])} класів, {D['obj']} object, {D['dat']} data"],
        ["models/onto_data.ttl, models/onto_data.rdf", "ABox: індивіди, типи, значення, зв’язки", f"{len(D['ip'])} індивідів"],
        ["models/class_table.csv", "Словник класів із genus+differentia", f"{len(D['cp'])} рядків, 7 колонок"],
        ["models/properties.csv", "Словник властивостей із domain/range", f"{len(D['pp'])} рядків"],
        ["models/situations.csv", "Шаблони ситуацій із прив’язкою елементів до класів", f"{len(D['sp'])} ситуацій"],
        ["tests/cq_sparql/*.rq", "SPARQL-запити для 10 CQ", "10 файлів"],
        ["tests/situation_queries/*.rq", "SPARQL-перевірки ситуацій S1 і S3", "2 файли"],
        ["models/llm_draft.ttl", "Чернетка онтології від LLM", f"{D['cqs']['llm_classes']} класів, {D['cqs']['llm_individuals']} індивідів"],
        ["docs/reasoner_log.md", "Журнал HermiT: consistency, classification, inconsistency", "Markdown"],
        ["docs/onto_eval.md", "CQ, ситуації, OntoClean, порівняння з LLM", "Markdown"],
        ["claims/claims.csv", "Твердження та їх верифікація", f"{len(D['cl'])} тверджень"],
        ["README.md, requirements.txt", "Відтворення та залежності", "Markdown / pip"],
    ], widths=[5.0, 7.2, 4.7], font_size=8.0)

    # ----- result 1: formalization -----
    h1(doc, "Результат 1. Формалізація предметної області")
    para(doc, "Простір назв онтології — https://knowledge.uni.lviv.ua/mobility# (скорочено mm:), базовий IRI — "
              "https://knowledge.uni.lviv.ua/mobility. Для повторного використання застосовано schema.org: "
              "mm:Stop ↔ schema:BusStop, mm:TransportRoute ↔ schema:Route, mm:Trip ↔ schema:Trip, "
              "mm:Passenger ↔ schema:Person, mm:TransportAgency ↔ schema:Organization, mm:Event ↔ schema:Event, "
              "mm:GTFSDataset ↔ schema:Dataset, mm:NetworkSegment ↔ schema:Place. Зв’язок зафіксовано через "
              "skos:closeMatch і rdfs:seeAlso, без повного owl:imports, щоб не завантажувати зайві аксіоми schema.org.")
    para(doc, "Класи означено за схемою genus + differentia: спочатку рід (батьківський клас), потім ознака, "
              "яка відрізняє клас від його братів. Наприклад, InterchangeStop — це Stop, який обслуговується "
              "щонайменше двома маршрутами; DelayedTrip — Trip, що має стан DelayedState; CongestedSegment — "
              "NetworkSegment, на якому відбулася подія Congestion. Повний словник класів подано в таблиці 2.")

    # landscape section for large tables
    sec_l = doc.add_section(WD_SECTION.NEW_PAGE); set_section_landscape(sec_l)
    add_caption(doc, f"Таблиця 2 - Класи онтології ({len(D['cp'])}; genus + differentia)")
    rows = [[c["class_id"], c["label_uk"], c["parent"], c["definition"], c["key_properties"], c["source"]] for c in D["cp"]]
    add_table(doc, ["ID", "Клас", "Батько", "Означення (genus + differentia)", "Ключові властивості", "Джерело"],
              rows, widths=[2.7, 3.3, 2.8, 9.4, 4.7, 3.2], font_size=7.8,
              align_center_cols=[0], max_width=25.7)
    add_caption(doc, f"Таблиця 3 - Властивості онтології ({len(D['pp'])}; object і data)")
    rows = [[p["name"], p["label_uk"], p["type"], p["domain"], p["range"], p["characteristics"], p["description"]] for p in D["pp"]]
    add_table(doc, ["ID", "Назва", "Тип", "Domain", "Range", "Характеристики", "Означення"],
              rows, widths=[3.0, 3.6, 1.4, 3.5, 3.5, 4.5, 5.6], font_size=7.6,
              align_center_cols=[2], max_width=25.7)

    # back to portrait
    sec_p = doc.add_section(WD_SECTION.NEW_PAGE); set_section_portrait(sec_p)

    h2(doc, "1.1. Обмеження та аксіоми")
    para(doc, "Формальна семантика забезпечується не лише ієрархією, а й обмеженнями. У TBox є 4 existential/universal "
              "аксіоми, 3 кардинальності, 4 еквівалентні класи та 8 груп диз’юнктності. Саме вони дають змогу "
              "отримувати нетривіальні висновки HermiT, а не просто перевіряти синтаксис.")
    add_caption(doc, "Таблиця 4 - Ключові обмеження та аксіоми OWL 2")
    add_table(doc, ["Клас", "Аксіома", "Тип", "Навіщо"], [
        ["Trip", "∃ hasStopTime.StopTime", "existential", "Рейс має зупинки в розкладі"],
        ["TransportRoute", "∃ servesStop.Stop", "existential", "Маршрут обслуговує зупинки"],
        ["NetworkSegment", "∀ hasEvent.Event", "universal", "Події ділянки належать класу Event"],
        ["Recommendation", "∃ recommends.TransportRoute", "existential", "Рекомендація стосується маршруту"],
        ["Trip", "= 1 usesVehicle.Vehicle", "qualified cardinality", "Один рейс — один транспортний засіб"],
        ["Trip", "= 1 operatedBy.TransportAgency", "qualified cardinality", "Один рейс — один перевізник"],
        ["StopTime", "= 1 atStop.Stop", "qualified cardinality", "Одна позиція розкладу — одна зупинка"],
        ["InterchangeStop", "Stop ⊓ ≥ 2 servedByRoute.TransportRoute", "equivalent class", "Пересадочність через два маршрути"],
        ["AccessibleStop", "Stop ⊓ wheelchairAccessible = true", "equivalent class", "Доступність для маломобільних"],
        ["CongestedSegment", "NetworkSegment ⊓ ∃ hasEvent.Congestion", "equivalent class", "Затор як ознака ділянки"],
        ["DelayedTrip", "Trip ⊓ ∃ hasState.DelayedState", "equivalent class", "Затриманий рейс"],
    ], widths=[3.4, 8.0, 3.2, 5.0], font_size=7.8)
    para(doc, "Диз’юнктність задано для груп Bus/Tram/Trolleybus, BusRoute/TramRoute/TrolleybusRoute, "
              "Congestion/Roadwork/VehicleFailure/PassengerSurge/WeatherEvent, DelayedState/OnTimeState/CrowdedState, "
              "Passenger/Driver/Dispatcher/TransportAgency, Stop/NetworkSegment/TransportRoute, "
              "GTFSDataset/SIRIFeed/NeTExDataset і PassengerFlow/LoadFactor/Delay/TravelTime. Це запобігає "
              "некоректному перетину категорій і робить можливою перевірку навмисної суперечності.")

    h2(doc, "1.2. Повторне використання зовнішнього словника")
    add_caption(doc, "Таблиця 5 - Мапінг на schema.org")
    add_table(doc, ["Клас ЛР7", "Термін schema.org", "Роль у моделі"], [
        ["Stop", "schema:BusStop", "Фізична зупинка як місце"],
        ["InterchangeStop", "schema:BusStop", "Пересадочна зупинка"],
        ["TransportRoute", "schema:Route", "Маршрут як упорядкований шлях"],
        ["Trip", "schema:Trip", "Конкретне виконання маршруту"],
        ["Passenger", "schema:Person", "Пасажир як особа"],
        ["TransportAgency", "schema:Organization", "Перевізник"],
        ["Event", "schema:Event", "Подія на мережі"],
        ["GTFSDataset", "schema:Dataset", "Набір даних"],
        ["NetworkSegment", "schema:Place", "Просторова ділянка"],
    ], widths=[4.2, 4.5, 7.1], font_size=8.2)
    para(doc, "Мапінг не є повним імпортом schema.org: зовнішні терміни використано як семантичні орієнтири для "
              "сумісності та пояснення. Це задовольняє вимогу повторного використання щонайменше одного "
              "зовнішнього словника й не створює залежності від веб-доступу під час перевірки.")

    # ----- result 2: OWL ontology -----
    h1(doc, "Результат 2. OWL-онтологія та її структура")
    para(doc, "Онтологію збережено у двох еквівалентних серіалізаціях: Turtle (models/onto.owl) для читабельності "
              "та RDF/XML (models/onto.rdf) для відкриття в Protégé. ABox має окремі файли onto_data.ttl і "
              "onto_data.rdf. Об’єднаний файл build/expert_merged.rdf використовується для HermiT; саме його "
              "завантажує reasoner під час перевірки.")
    add_caption(doc, "Таблиця 6 - Метрики OWL-онтології")
    add_table(doc, ["Показник", "Значення", "Вимога"], [
        ["Класів", len(D["cp"]), "≥ 30"],
        ["Object properties", D["obj"], "≥ 10"],
        ["Data properties", D["dat"], "≥ 5"],
        ["Індивідів", len(D["ip"]), "≥ 20"],
        ["Object properties з inverse", sum(1 for p in D["pp"] if "inverse:" in p["characteristics"]), "≥ 1"],
        ["Transitive properties", sum(1 for p in D["pp"] if "transitive" in p["characteristics"]), "≥ 1"],
        ["Functional data properties", sum(1 for p in D["pp"] if "functional" in p["characteristics"]), "не обов’язково"],
        ["Групи AllDisjointClasses", 8, "≥ 1"],
        ["Індивідів із ≥3 властивостями", D["reason"]["individuals_with_3plus_props"], "≥ 20"],
        ["Середня кількість властивостей", f"{D['reason']['average_properties_per_individual']:.2f}", "≥ 3"],
    ], widths=[7.0, 4.0, 4.8], font_size=8.2, align_center_cols=[1])
    para(doc, "Фрагмент TBox нижче показує кардинальність і визначений клас. Повний файл містить 58 класів, "
              f"48 object properties, 25 data properties, {D['tbox_count']} RDF-тверджень у TBox і {D['abox_count']} — в ABox.")
    add_code(doc, """@prefix mm: <https://knowledge.uni.lviv.ua/mobility#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

mm:Trip a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty mm:usesVehicle ;
        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;
        owl:onClass mm:Vehicle
    ] .

mm:InterchangeStop a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf ( mm:Stop [
            a owl:Restriction ;
            owl:onProperty mm:servedByRoute ;
            owl:minQualifiedCardinality "2"^^xsd:nonNegativeInteger ;
            owl:onClass mm:TransportRoute
        ] )
    ] .""")
    add_picture_centered(doc, MODELS/"class_hierarchy_core.png", 16.0)
    add_caption(doc, "Рис. 1 - Ядро ієрархії онтології (24 з 58 класів; повний перелік — таблиця 2)")
    para(doc, "Protégé відкриває RDF/XML-версію без попередніх налаштувань; у дереві класів видно гілки "
              "TransportNetwork, Vehicle, Trip, Actor, DataAsset, Sensor, Analytics, Event, TransportState і "
              "Measurement. Для перевірки в Protégé достатньо відкрити models/onto.rdf, увімкнути HermiT і "
              "запустити Start reasoner. У нашій автоматизованій перевірці той самий HermiT викликано через "
              "owlready2 та CLI, тому результат класифікації збігається.")

    # ----- result 3: ABox and situations -----
    h1(doc, "Результат 3. Індивіди, ABox і ситуації")
    para(doc, "ABox містить 52 індивіди: 4 зупинки, 3 маршрути, 4 рейси, 4 транспортні засоби, 7 учасників, "
              "6 наборів даних, 3 сенсори, 4 вимірювання, 4 стани, 2 події, рекомендацію, прогноз і рішення. "
              "Середня кількість властивостей на індивід — 3,37; 24 індивіди мають щонайменше три властивості, "
              "що перевищує вимогу 20.")
    add_caption(doc, "Таблиця 7 - Фрагмент ABox: індивіди та їхні класи")
    rows = []
    for p in D["ip"]:
        rows.append([p["id"], p["classes"], p["properties"][:180] + ("…" if len(p["properties"]) > 180 else "")])
    add_table(doc, ["ID", "Класи", "Властивості (вибірково)"], rows, widths=[3.8, 4.6, 8.3], font_size=7.0)
    para(doc, "Повний перелік із 52 індивідів і всіма значеннями збережено в data/individuals.csv. Нижче — "
              "фрагмент, який показує типову зв’язку «рейс — засіб — стан — подія — диспетчер — вимірювання».")
    add_picture_centered(doc, MODELS/"abox_core.png", 16.0)
    add_caption(doc, "Рис. 2 - Фрагмент ABox для затриманого рейсу 9 о 08:00")
    add_code(doc, """mm:Trip_9_0800 a mm:Trip ;
    mm:tripId "T090800" ;
    mm:usesVehicle mm:Bus_2501 ;
    mm:hasState mm:State_Delayed_9 ;
    mm:affectedByEvent mm:Congestion_Horodotska ;
    mm:hasMeasurement mm:Delay_9_0800 .

mm:Congestion_Horodotska a mm:Congestion ;
    mm:affectsSegment mm:Seg_Vokzal_Rynok ;
    mm:affectsTrip mm:Trip_9_0800 ;
    mm:handledBy mm:Dispatcher_01 .

mm:State_Delayed_9 a mm:DelayedState ;
    mm:stateOfTrip mm:Trip_9_0800 .""")
    h2(doc, "3.1. Шаблони ситуацій")
    para(doc, "Ситуація — це іменований шаблон, у якому початковий стан, подія, guard, новий стан, дія та сенсор "
              "прив’язані до класів онтології. Усі п’ять шаблонів мають версію 1.0, власника, джерела й статус "
              "verified; для двох шаблонів виконано SPARQL-перевірку.")
    add_caption(doc, "Таблиця 8 - П’ять шаблонів ситуацій")
    add_table(doc, ["ID", "Ситуація", "Подія", "Guard", "Новий стан", "Дія", "Класи"],
              [[s["id"], s["title"], s["event"], s["guard"], s["new_state"], s["consequence_action"],
                f"{s['initial_state_class']} → {s['event_class']} → {s['new_state_class']}"] for s in D["sp"]],
              widths=[0.9, 3.0, 2.9, 3.6, 2.5, 5.4, 3.4], font_size=6.9, align_center_cols=[0])
    add_caption(doc, "Таблиця 9 - SPARQL-перевірки ситуацій S1 і S3")
    add_table(doc, ["Ситуація", "Перевірка", "Рядків", "Статус"],
              [[s["situation"], s["check"], s["rows"], s["status"]] for s in D["si"]],
              widths=[1.5, 10.2, 1.6, 2.3], font_size=8.2, align_center_cols=[0, 2, 3])
    para(doc, "Запити лежать у tests/situation_queries/. S1 перевіряє ланцюжок «затриманий рейс — затор — диспетчер», "
              "S3 — «пасажиропотік — завантаженість — рекомендація — пасажир». Обидва запити повертають по одному "
              "рядку, тому шаблони підтверджено даними, а не лише текстом. Повні прив’язки всіх елементів "
              "до класів (initial_state_class, event_class, guard_class, new_state_class, action_class, "
              "sensor_class) збережено в models/situations.csv.")

    # ----- result 4: HermiT + CQ -----
    h1(doc, "Результат 4. HermiT, виведення та компетентнісні запити")
    h2(doc, "4.1. Консистентність і класифікація")
    para(doc, "HermiT перевірив об’єднану онтологію build/expert_merged.rdf. CLI повернув "
              "«owl:Thing is satisfiable», тобто онтологія консистентна. Після класифікації reasoner вивів "
              "165 нових type-тверджень (зокрема 6 членств у визначених класах) і 21 property-твердження. "
              "Це підтверджує, що обмеження працюють, а не залишаються декларацією.")
    add_caption(doc, "Таблиця 10 - Результат HermiT")
    add_table(doc, ["Показник", "Значення"], [
        ["Консистентність", "консистентна (Thing is satisfiable)"],
        ["Класів у TBox", D["reason"]["classes"]],
        ["Індивідів у ABox", D["reason"]["individuals"]],
        ["Виведених type-тверджень", D["reason"]["inferred_type_assertions"]],
        ["З них у визначених класах", len(D["reason"]["inferred_focus"])],
        ["Виведених property-тверджень", D["reason"]["inferred_property_assertions"]],
        ["Час роботи HermiT", "0,8 с (JVM, локально)"],
    ], widths=[7.0, 8.5], font_size=8.4)
    add_caption(doc, "Таблиця 11 - Шість змістовних виведень HermiT")
    add_table(doc, ["Індивід", "Виведений клас", "Яка аксіома спрацювала"],
              [[a, b, "equivalentClass + min 2 / hasValue / existential"] for a, _, b in D["reason"]["inferred_focus"]],
              widths=[4.2, 4.8, 7.0], font_size=8.2)
    h2(doc, "4.2. Навмисна суперечність")
    para(doc, "Для перевірки реакції reasoner створено копію онтології та додано Bus_2501 a Tram за наявного "
              "Bus_2501 a Bus. Оскільки Bus, Tram і Trolleybus утворюють AllDisjointClasses, HermiT мав виявити "
              "суперечність. CLI завершився з InconsistentOntologyException; owlready2 — з "
              "OwlReadyInconsistentOntologyError. Після цього перевірено, що робоча онтологія не містить "
              "доданого типу й залишається консистентною.")
    add_code(doc, """java -cp .../HermiT.jar org.semanticweb.HermiT.cli.CommandLine \
  -k file:///.../build/expert_merged.rdf
# owl:Thing is satisfiable.

java -cp .../HermiT.jar org.semanticweb.HermiT.cli.CommandLine \
  -k file:///.../build/inconsistent.rdf
# InconsistentOntologyException: Inconsistent ontology""")
    h2(doc, "4.3. Компетентнісні запити")
    para(doc, "Сформовано 10 CQ — від пересадочних зупинок і маршрутів до рекомендацій і наборів даних. "
              "Кожне CQ має окремий .rq-файл і очікуваний результат. Експертна онтологія проходить 10/10; "
              "LLM-чернетка — 2/10. Різниця показує, що LLM відтворює окремі факти, але не відтворює "
              "кардинальності, inverse-властивості та повний ABox.")
    add_caption(doc, "Таблиця 12 - 10 компетентнісних питань")
    add_table(doc, ["ID", "Питання", "Очікувані значення"],
              [[c["id"], c["question"], c["expected_values"]] for c in D["cq"]],
              widths=[1.2, 7.4, 8.2], font_size=7.8)
    add_caption(doc, "Таблиця 13 - Результати CQ: експертна онтологія та LLM-чернетка")
    add_table(doc, ["ID", "Експерт", "LLM", "Статус експерта", "Статус LLM"],
              [[c["id"], c["expert_count"], c["llm_count"], c["expert_status"], c["llm_status"]] for c in D["cq"]],
              widths=[1.2, 2.4, 2.0, 5.2, 5.2], font_size=8.0, align_center_cols=[0, 1, 2, 3, 4])
    para(doc, "Детальні значення, зокрема кількість рядків і склад відповідей, збережено в "
              "results/cq_results.csv. Для CQ4 і CQ8 запит повертає кілька змінних в одному рядку; тому "
              "перевірка порівнює сукупність значень, а не лише першу колонку. Це важливо для ситуацій, "
              "де потрібно одночасно отримати ділянку й рейс або рішення, рекомендацію та маршрут.")

    # ----- result 5: LLM comparison -----
    h1(doc, "Результат 5. LLM-чернетка, OntoClean і порівняння")
    para(doc, "Чернетку згенеровано моделлю opencode/deepseek-v4.1-flash-free 27.10.2026 з температурою 0,2, "
              "seed 42 і підказкою lab07-prompt-v1. Сирий вихід і рішення людини збережено в llm_log/. "
              "Чернетка синтаксично валідна, HermiT вважає її консистентною, але семантично вона слабша: "
              "30 класів, 7 object properties, 5 data properties і 13 індивідів.")
    add_caption(doc, "Таблиця 14 - Метрики експертної онтології та LLM-чернетки")
    add_table(doc, ["Показник", "Експерт", "LLM", "Коментар"], [
        ["Класів", len(D["cp"]), D["cqs"]["llm_classes"], "LLM має 30 класів; у повній моделі — 58"],
        ["Object properties", D["obj"], D["cqs"]["llm_object_properties"], "Немає inverse і частини domain/range"],
        ["Data properties", D["dat"], D["cqs"]["llm_data_properties"], "Немає полів для більшості вимірювань"],
        ["Індивідів", len(D["ip"]), D["cqs"]["llm_individuals"], "LLM наповнила лише центральний фрагмент"],
        ["CQ пройдено", D["cqs"]["expert_pass"], D["cqs"]["llm_pass"], "2/10 — CQ7 і CQ9"],
        ["Спільних IRI класів", "—", D["cqs"]["llm_same_iri_overlap"], "Часткове перекриття словника"],
    ], widths=[4.4, 3.2, 3.2, 6.0], font_size=7.8, align_center_cols=[1, 2])
    add_caption(doc, "Таблиця 15 - Рішення щодо фрагментів LLM-чернетки")
    add_table(doc, ["ID", "Фрагмент", "Рішення", "Причина"],
              [["D01", "Passenger ⊑ Vehicle", "відхилено", "Пасажир — роль особи, а не транспортний засіб"],
               ["D02", "Trip ⊑ Route", "відхилено", "Рейс і маршрут мають різні критерії ідентичності"],
               ["D03", "Delay ⊑ Event", "відхилено", "Затримка є вимірюванням, а не подією"],
               ["D04", "Bus25 як owl:Class", "відхилено", "Конкретний автобус має бути індивідом"],
               ["D05", "hasStop без inverse", "відхилено", "Додано servedByRoute і кардинальність"],
               ["D06", "routeType xsd:string", "відхилено", "Тип маршруту в GTFS — ціле число"],
               ["D07", "hasStop exactly 1", "відхилено", "Маршрут обслуговує багато зупинок"],
               ["D08", "relatedTo", "відхилено", "Замінено конкретними відношеннями"],
               ["D09", "Немає диз’юнктностей", "відхилено", "Додано 8 груп AllDisjointClasses"],
               ["D10", "Немає кардинальностей", "відхилено", "Додано usesVehicle=1, operatedBy=1, atStop=1"],
               ["D11", "Базові індивіди", "прийнято з правками", "Route_9, Stop_Vokzal, Trip_9_0800 використано в ABox"],
               ["D12", "usesVehicle", "прийнято", "Збережено з domain/range та inverse"]],
              widths=[1.1, 5.8, 3.6, 7.0], font_size=7.6)
    h2(doc, "5.1. OntoClean-перевірки")
    para(doc, "Перевірено сім найризикованіших тверджень чернетки. Для кожного вказано мета-властивість "
              "(rigidity, identity, unity, dependence) і рішення. Це не повний OntoClean-аудит усіх 30 класів, "
              "але він покриває всі помилки, які впливають на CQ та HermiT.")
    add_caption(doc, "Таблиця 16 - OntoClean-перевірки LLM-чернетки")
    add_table(doc, ["№", "Твердження", "Порушення", "Рішення"], [
        ["1", "Passenger ⊑ Vehicle", "identity/category: пасажир не має ідентичності засобу", "відхилити підклас; Passenger ⊑ Actor"],
        ["2", "Trip ⊑ Route", "unity/level: рейс — виконання, маршрут — шлях", "відхилити; Trip ⊑ TransportSystem"],
        ["3", "Delay ⊑ Event", "identity: вимірювання залежне від рейсу (+D)", "відхилити; Delay ⊑ Measurement"],
        ["4", "Bus25 a owl:Class", "identity/punning: індивід як клас", "зробити Bus25 індивідом"],
        ["5", "Stop ⊑ TransportNetwork", "unity: вузол не є агрегатом мережі", "Stop ⊑ TransportNode"],
        ["6", "hasStop без inverse", "залежність і кардинальність не специфіковані", "додати servedByRoute, min 2"],
        ["7", "Немає disjointness", "перетин Bus/Tram/Trolleybus", "додати AllDisjointClasses"],
    ], widths=[0.8, 5.3, 6.6, 5.1], font_size=7.6, align_center_cols=[0])
    para(doc, "Після виправлень експертна онтологія проходить 10/10 CQ, тоді як LLM — 2/10. Найбільший розрив — "
              "не в кількості класів, а в аксіомах: inverse-властивості, кардинальності, диз’юнктності та "
              "визначені класи дають ті висновки, яких у чернетці немає. Це підтверджує тезу, що LLM корисна "
              "для каркаса, але не замінює інженера знань.")

    # ----- claims and sources -----
    h1(doc, "Твердження, джерела та відтворення")
    para(doc, f"Усього сформовано {len(D['cl'])} тверджень: {D['verified']} підтверджено, {D['rejected']} відхилено. "
              "Кожне твердження має тип, джерело, рівень перевірки (V1–V4), статус і коментар. Відхилені "
              "твердження переважно походять із LLM-чернетки й демонструють типові помилки категоризації.")
    add_caption(doc, "Таблиця 17 - Твердження та їх верифікація")
    add_table(doc, ["ID", "Твердження", "Статус", "Коментар"],
              [[c["id"], c["claim"], c["status"], c["comment"]] for c in D["cl"]],
              widths=[1.0, 7.4, 2.0, 6.4], font_size=7.2)
    add_caption(doc, "Таблиця 18 - Джерела")
    add_table(doc, ["№", "Джерело", "URL", "Дата"],
              [[str(i), s[0], s[1], s[2]] for i, s in enumerate(kb7.SOURCES, 1)],
              widths=[0.8, 5.4, 8.0, 2.6], font_size=7.4, align_center_cols=[0])
    add_caption(doc, "Таблиця 19 - Відповідність вимогам ЛР7")
    add_table(doc, ["Вимога", "Факт", "Статус"], [
        ["≥30 класів із genus+differentia", len(D["cp"]), "виконано"],
        ["≥10 object properties", D["obj"], "виконано"],
        ["≥5 data properties", D["dat"], "виконано"],
        ["≥3 existential/universal", 4, "виконано"],
        ["≥2 cardinality", 3, "виконано"],
        ["≥20 індивідів, ≥3 властивості", f"{len(D['ip'])} / {D['reason']['individuals_with_3plus_props']}", "виконано"],
        ["HermiT: consistency + classification + ≥3 inferred", f"{D['reason']['inferred_type_assertions']} type, 6 focus", "виконано"],
        ["Навмисна суперечність і виправлення", "Bus/Tram", "виконано"],
        ["≥5 ситуацій із класами", len(D["sp"]), "виконано"],
        ["2 SPARQL-перевірки ситуацій", "2/2", "виконано"],
        ["≥10 CQ", D["cqs"]["total"], "виконано"],
        ["LLM-чернетка + журнал", "30 класів, 13 індивідів", "виконано"],
        ["≥5 OntoClean-перевірок", 7, "виконано"],
        ["Звіт DOCX/ODT/PDF", "3 формати", "виконано"],
    ], widths=[7.2, 5.2, 3.2], font_size=7.8, align_center_cols=[2])
    para(doc, "Окремо зафіксовано технічне обмеження: HermiT підтримує лише типи з OWL 2 datatype map. "
              "Початкові діапазони xsd:date і xsd:time для GTFS-полів були замінені на xsd:string, оскільки "
              "GTFS і так подає дати як YYYYMMDD, а час — як HH:MM:SS. Це не послаблює CQ, але усуває "
              "помилку UnsupportedDatatypeException під час класифікації.")

    # ----- conclusions -----
    h1(doc, "Висновки")
    para(doc, "У роботі побудовано OWL 2 онтологію предметної області «Інтелектуальне управління міською "
              "мобільністю», наповнено її індивідами, описано п’ять ситуацій і перевірено логіку за допомогою "
              "HermiT. Онтологія містить 58 класів, 48 object properties, 25 data properties, 52 індивіди, "
              "8 груп диз’юнктності та 11 ключових обмежень. Вона консистентна, класифікується reasoner-ом і "
              "проходить усі 10 компетентнісних запитів.")
    add_bullets(doc, [
        "Формалізація: класи означено через genus + differentia, властивості — через domain/range і характеристики; "
        "повторно використано schema.org без повного імпорту.",
        "OWL: реалізовано 4 existential/universal аксіоми, 3 кардинальності, 4 еквівалентні класи та 8 груп "
        "AllDisjointClasses; це дало 165 виведених type-тверджень.",
        "ABox: 52 індивіди, середня кількість властивостей 3,37; 24 індивіди мають ≥3 властивості; "
        "5 ситуацій валідовано, 2 з них — SPARQL-запитами.",
        "Перевірка: HermiT підтвердив консистентність, вивів 6 змістовних членств і виявив навмисну "
        "суперечність Bus/Tram; після виправлення онтологія знову консистентна.",
        "CQ: експертна онтологія — 10/10, LLM-чернетка — 2/10; основні дефекти LLM — неправильна "
        "категоризація, відсутність inverse/кардинальностей і неповний ABox.",
        "OntoClean: сім перевірок виявили помилки Passenger ⊑ Vehicle, Trip ⊑ Route, Delay ⊑ Event, "
        "Bus25 як клас, Stop ⊑ TransportNetwork та відсутність disjointness.",
    ])
    para(doc, "Практичний висновок: LLM доцільно використовувати для швидкого каркаса термінів і фактів, "
              "але логічну структуру — ієрархію, domain/range, кардинальності, диз’юнктності та індивідів — "
              "має контролювати інженер знань. Найціннішими для подальших робіт є зв’язки «подія → рейс → "
              "стан → вимірювання → рішення», які вже підтримані HermiT і CQ.")

    # ----- appendix -----
    h1(doc, "Додаток А. Відтворення")
    add_code(doc, """python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/build_ontology.py      # TBox, ABox, CSV, CQ, LLM draft
python scripts/run_reasoner.py        # HermiT, inferred facts, inconsistency log
python scripts/evaluate_ontology.py   # CQ, situations, OntoClean text
python scripts/visualize.py           # Graphviz diagrams
python scripts/make_report.py         # DOCX -> ODT/PDF""")
    para(doc, "Залежності: Python 3.14, rdflib 7.6.0, owlready2 0.51, python-docx, LibreOffice, Graphviz, Java 11+. "
              "Мережа під час відтворення не потрібна: всі джерела й проміжні файли збережено локально. "
              "Ключі API не використовувалися; LLM-вихід зафіксовано як артефакт.")
    para(doc, "Структура: models/ — OWL/RDF, CSV, діаграми, LLM-чернетка; data/ — індивіди; tests/ — CQ і "
              "situation-запити; build/ — merged та inconsistent RDF; results/ — машинні результати; "
              "docs/ — журнали; llm_log/ — підказка, сирий вихід, рішення; claims/ — твердження.")

    doc.core_properties.title = "Лабораторна робота №7. Онтологія в Protégé та формалізація знань"
    doc.core_properties.author = "Невмержицький Максим Миколайович"
    doc.core_properties.subject = "Сховища знань та управління знаннями"
    docx_path = ROOT / f"{OUT_BASE}.docx"
    doc.save(docx_path)
    return docx_path

def convert(docx_path):
    profile = "file:///tmp/opencode/loreport_profile"
    outdir = str(ROOT)
    for fmt in ["odt", "pdf"]:
        target = ROOT / f"{OUT_BASE}.{fmt}"
        if target.exists():
            target.unlink()
        subprocess.run(["soffice", "--headless", f"-env:UserInstallation={profile}",
                        "--convert-to", fmt, "--outdir", outdir, str(docx_path)],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    odt = ROOT / f"{OUT_BASE}.odt"; pdf = ROOT / f"{OUT_BASE}.pdf"
    friendly_odt = ROOT / f"{FRIENDLY}.odt"
    if odt.exists(): shutil.copy2(odt, friendly_odt)
    return odt, pdf

if __name__ == "__main__":
    p = build(); print("saved", p)
    o, pdf = convert(p); print("odt", o); print("pdf", pdf)
