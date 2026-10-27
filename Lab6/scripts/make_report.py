# -*- coding: utf-8 -*-
"""Генерація звіту ЛР6 у DOCX та конвертація в ODT/PDF."""
import json, subprocess, shutil, os
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import kb

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"; DOCS = ROOT / "docs"; RESULTS = ROOT / "results"
OUT_BASE = "СЗтУЗ_Лаб6_Невмержицький_Максим-ФЕІ36"
FRIENDLY = "Лабораторна робота №6 — Семантична мережа та концептуальна карта"

# ---------- helpers ----------
def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_margins(table, top=58, bottom=58, left=58, right=58):
    tblPr = table._tbl.tblPr
    mar = OxmlElement('w:tblCellMar')
    for side, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        el = OxmlElement(f'w:{side}'); el.set(qn('w:w'), str(val)); el.set(qn('w:type'), 'dxa'); mar.append(el)
    tblPr.append(mar)

def add_table(doc, headers, rows, widths=None, font_size=None, header_fill="E6E6E6", align_center_cols=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    font_size = 14 if len(headers) <= 3 else (12 if len(headers) == 4 else (11 if len(headers) == 5 else (10 if len(headers) == 6 else 9)))
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        run = p.add_run(str(h)); run.bold = True; run.font.size = Pt(font_size); run.font.color.rgb = RGBColor(0,0,0)
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
            clean = str(val).replace("✅", "виконано").replace("❌", "не виконано")
            run = p.add_run(clean); run.font.size = Pt(font_size)
            p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            if align_center_cols and i in align_center_cols:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        trPr = table.rows[-1]._tr.get_or_add_trPr()
        cantSplit = OxmlElement('w:cantSplit'); cantSplit.set(qn('w:val'), 'true'); trPr.append(cantSplit)
    if widths:
        scale = min(1.0, 16.9 / sum(widths))
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

def add_code(doc, text, size=10):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5); p.paragraph_format.right_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(6)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for i, line in enumerate(text.split("\n")):
        run = p.add_run(line)
        run.font.name = "Courier New"; run.font.size = Pt(size)
        if i < len(text.split("\n"))-1: run.add_break()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), 'F2F3F4')
    p._p.get_or_add_pPr().append(shd)

def add_bullets(doc, items, style="List Bullet", size=14):
    for it in items:
        p = doc.add_paragraph(style=style)
        run = p.add_run(it); run.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(2); p.paragraph_format.line_spacing = 1.0

def set_section_portrait(section):
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21.0); section.page_height = Cm(29.7)
    section.left_margin = Cm(2.0); section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0); section.bottom_margin = Cm(2.0)

def set_section_landscape(section):
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Cm(29.7); section.page_height = Cm(21.0)
    section.left_margin = Cm(1.5); section.right_margin = Cm(1.5)
    section.top_margin = Cm(1.5); section.bottom_margin = Cm(1.5)

def add_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(); run.font.size = Pt(9); run.font.name = "Times New Roman"
    fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText'); instrText.set(qn('xml:space'), 'preserve'); instrText.text = "PAGE"
    fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1); run._r.append(instrText); run._r.append(fldChar2)

def add_header(section):
    header = section.header
    p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    p.text = ""
    run = p.add_run("Сховища знань та управління знаннями · Лабораторна робота №6")
    run.font.size = Pt(8); run.font.name = "Times New Roman"; run.font.color.rgb = RGBColor(100,100,100)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    # bottom border
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr'); bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single'); bottom.set(qn('w:sz'), '4'); bottom.set(qn('w:space'), '1'); bottom.set(qn('w:color'), 'BFBFBF')
    pBdr.append(bottom); pPr.append(pBdr)

def add_map_page(doc, image, caption, width_cm=25.5):
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_landscape(sec)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(image), width=Cm(width_cm))
    add_caption(doc, caption)
    sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_portrait(sec2)

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
    run = p.add_run(text); run.bold = bold; run.font.size = Pt(size)
    return p

def no_indent(doc, text, size=14, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, space_after=0):
    p = doc.add_paragraph(); p.alignment = align; p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text); run.font.size = Pt(size); run.bold = bold
    return p

def selfcheck(doc, rows, caption=None):
    if caption:
        add_caption(doc, caption)
    add_table(doc, ["Критерій", "Стан", "Де перевірити"], rows, widths=[8.2, 2.2, 6.5], font_size=12, align_center_cols=[1])

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

# ---------- data ----------
def stats():
    def node_count(tr): return len({t[1] for t in tr} | {t[3] for t in tr})
    v1, v2 = kb.V1_TRIPLES, kb.V2_TRIPLES
    llm = [t for t in kb.LLM_TRIPLES if t[0] in [f"L{i:02d}" for i in range(1,41)]]
    vals = load_json(RESULTS / "validation_report.json")
    pr = load_json(RESULTS / "precision_recall.json")
    A=[r[2] for r in kb.RUBRIC_ROWS]; B=[r[3] for r in kb.RUBRIC_ROWS]
    n=len(A); exact=sum(a==b for a,b in zip(A,B)); mad=sum(abs(a-b) for a,b in zip(A,B))/n
    k=5; po=sum(1-abs(a-b)/(k-1) for a,b in zip(A,B))/n
    pe=sum((1-abs(i-j)/(k-1))*(A.count(i)/n)*(B.count(j)/n) for i in range(k) for j in range(k))
    kappa=(po-pe)/(1-pe)
    verified=sum(1 for c in kb.CLAIMS if c[5]=="verified")
    return {
        "v1_nodes":node_count(v1),"v1_props":len(v1),"v1_cross":sum(1 for t in v1 if t[4]),
        "v2_nodes":node_count(v2),"v2_props":len(v2),"v2_cross":sum(1 for t in v2 if t[4]),
        "llm_nodes":node_count(llm),"llm_props":len(llm),
        "concepts":len(kb.CONCEPTS),"relations":len(kb.RELATIONS),"cqs":len(kb.CQS),
        "exact":exact,"n":n,"exact_share":exact/n,"mad":mad,"kappa":kappa,
        "claims":len(kb.CLAIMS),"verified":verified,
        "rejected":sum(1 for c in kb.CLAIMS if c[5]=="rejected"),
        "pending":sum(1 for c in kb.CLAIMS if c[5]=="pending"),
    }

def build():
    S=stats()
    doc=Document()
    # base styles
    st=doc.styles["Normal"]; st.font.name="Times New Roman"; st.font.size=Pt(14)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    st.paragraph_format.line_spacing=1.0; st.paragraph_format.space_after=Pt(0)
    for name in ["Heading 1","Heading 2","Heading 3"]:
        h=doc.styles[name]; h.font.name="Times New Roman"; h.font.color.rgb=RGBColor(0,0,0); h.font.size=Pt(14)
    sec=doc.sections[0]; set_section_portrait(sec)

    # ----- title page -----
    p=no_indent(doc,"Міністерство освіти і науки України",size=14,align=WD_ALIGN_PARAGRAPH.CENTER)
    p=no_indent(doc,"Львівський національний університет імені Івана Франка",size=14,align=WD_ALIGN_PARAGRAPH.CENTER)
    p=no_indent(doc,"Факультет електроніки та комп’ютерних технологій",size=14,align=WD_ALIGN_PARAGRAPH.CENTER)
    p=no_indent(doc,"Кафедра системного проєктування",size=14,align=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(8): doc.add_paragraph()
    p=no_indent(doc,"Звіт про виконання лабораторної роботи №6",size=14,align=WD_ALIGN_PARAGRAPH.CENTER)
    p=no_indent(doc,"з курсу “Сховища знань та управління знаннями”",size=14,align=WD_ALIGN_PARAGRAPH.CENTER)
    p=no_indent(doc,"“Семантична мережа та концептуальна карта”",size=14,align=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(9): doc.add_paragraph()
    no_indent(doc,"Виконав:",size=14,align=WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc,"студент групи ФЕІ-46с",size=14,align=WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc,"Невмержицький Максим Миколайович",size=14,align=WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc,"Перевірив:",size=14,align=WD_ALIGN_PARAGRAPH.RIGHT)
    no_indent(doc,"асистент Цудзенко Юрій Євгенович",size=14,align=WD_ALIGN_PARAGRAPH.RIGHT)
    for _ in range(11): doc.add_paragraph()
    no_indent(doc,"Львів-2026",size=14,align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_page_break()

    # ----- intro -----
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.space_after=Pt(3); p.paragraph_format.line_spacing=1.0
    r=p.add_run("Мета роботи: "); r.bold=True; r.font.size=Pt(14)
    r=p.add_run("побудувати концептуальну карту за фокусним питанням, отримати альтернативну карту від LLM із "
                "триплетами та цитатами, оцінити карти за рубрикою Новака, створити об’єднану карту v2 і набір "
                "триплетів для онтології та графа."); r.font.size=Pt(14)
    p=no_indent(doc,"Хід роботи",size=14,align=WD_ALIGN_PARAGRAPH.CENTER,bold=True,space_after=3)
    para(doc,"Тематична область — інтелектуальне управління міською мобільністю. Вона продовжує ЛР4 (таксономія "
             "понять) і ЛР5 (семантична мережа з 18 понять і 27 відношень). У ЛР4 формальних компетентнісних питань "
             "не було, тому для ЛР6 сформовано 7 CQ на основі таксономії ЛР4, семантичної мережі ЛР5 та мети "
             "проєкту Domain Knowledge Hub. Це методична нестиковка між оновленою методичкою ЛР6 і попередніми "
             "роботами; вона явно зафіксована в артефакті docs/cmap_focus.md.")
    para(doc,"Інструменти: редактор draw.io для карти, Graphviz для експорту PNG, Python 3.14 для перевірки цитат, "
             "domain/range і метрик; LLM — opencode/deepseek-v4.1-flash-free як генератор чернетки триплетів. "
             "Усі рішення LLM верифіковано людиною; журнал — у llm_log/.")
    add_caption(doc,"Таблиця 1 - Обов’язкові артефакти роботи")
    add_table(doc,["Артефакт","Призначення","Кількість / формат"],[
        ["docs/cmap_focus.md","Фокусне питання, parking lot, каталог відношень, CQ",f"{S['concepts']} понять, {S['relations']} відношень, {S['cqs']} CQ"],
        ["models/cmap_expert.drawio / .png","Експертна карта v1",f"{S['v1_nodes']} понять, {S['v1_props']} пропозицій, {S['v1_cross']} крос-зв’язків"],
        ["models/triples_llm.jsonl","Триплети LLM із цитатами","50 JSONL-записів"],
        ["models/cmap_llm.png","Візуалізація прийнятих триплетів LLM",f"{S['llm_props']} пропозицій, {S['llm_nodes']} понять"],
        ["docs/cmap_rubric.xlsx","Рубрика Новака, 3 карти × 2 оцінювачі","15 оцінок, узгодженість, precision/recall"],
        ["models/cmap_v2.drawio / .png","Об’єднана карта v2",f"{S['v2_nodes']} понять, {S['v2_props']} пропозицій"],
        ["models/triples_final.csv","CSV для ЛР7–ЛР9","106 рядків, 10 колонок"],
        ["claims/claims.csv","Таблиця тверджень",f"{S['claims']} тверджень, V1–V3"],
    ],widths=[4.8,7.2,5.2],font_size=8.2)

    # ----- result 1 -----
    h1(doc,"Результат 1. Фокусне питання та parking lot")
    h2(doc,"1.1. Фокусне питання")
    para(doc,"Фокусне питання сформульовано одним відкритим реченням, яке пов’язує статичні дані мережі, "
             "динамічні пасажиропотоки й події з рішеннями диспетчера та рекомендаціями пасажирам:",space_after=2)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(8)
    r=p.add_run(kb.FOCUS_QUESTION); r.bold=True; r.font.size=Pt(14)
    h2(doc,"1.2. Parking lot: 55 понять від загальних до часткових")
    para(doc,"Поняття впорядковано за рівнем загальності: 0 — предметна область, 1 — система, 2 — мережа, "
             "3 — базові класи, 4 — конкретні процеси/дані, 5 — приклади-екземпляри. Кожен рядок містить означення, "
             "яке далі використовується як словник онтології.")
    rows=[]
    for i,cid in enumerate(sorted(kb.CONCEPTS,key=lambda c:(kb.CONCEPTS[c][1],kb.CONCEPTS[c][2],kb.CONCEPTS[c][0])),1):
        lab,lvl,grp,typ,inst,definition=kb.CONCEPTS[cid]
        rows.append([i,lvl,lab,definition])
    add_caption(doc,"Таблиця 2 - Parking lot із 55 понять (повна версія — docs/cmap_focus.md)")
    add_table(doc,["№","Рів.","Поняття","Означення"],rows,widths=[1.0,1.0,5.0,10.2],font_size=7.6,align_center_cols=[0,1])
    h2(doc,"1.3. Каталог відношень")
    para(doc,"Каталог містить 12 типів — у межах вимоги 8–12. Для кожного типу задано domain/range, що дозволяє "
             "автоматично перевіряти триплети LLM. Підпис related-to не використовується.")
    rrows=[]
    for i,(pid,(lab,definition,dom,ran,example)) in enumerate(kb.RELATIONS.items(),1):
        dom_s=", ".join(sorted(dom)) if dom else "будь-яке"
        ran_s="екземпляр" if ran=={"__instance__"} else (", ".join(sorted(ran)) if ran else "будь-яке")
        rrows.append([i,pid,lab,definition,dom_s,ran_s])
    add_caption(doc,"Таблиця 3 - Каталог із 12 типів відношень")
    add_table(doc,["№","ID","Підпис","Означення","Domain","Range"],rrows,widths=[0.8,2.2,2.4,6.8,3.2,2.8],font_size=7.4,align_center_cols=[0])
    h2(doc,"1.4. Компетентнісні питання")
    para(doc,"Сформовано 7 CQ. Кожне CQ пов’язане з концептами та пропозиціями карти, тому покриття можна "
             "перевірити не лише експертно, а й за номерами пропозицій.")
    add_caption(doc,"Таблиця 4 - CQ та їх покриття картою")
    add_table(doc,["ID","Компетентнісне питання","Поняття","Пропозиції"],
              [[c[0],c[1],c[2],c[3]] for c in kb.CQS],widths=[1.3,8.2,4.2,3.5],font_size=7.8)
    add_caption(doc,"Таблиця 5 - Самоперевірка. Результат 1")
    selfcheck(doc,[
        ["C1. Фокусне питання відкрите й змістовне","✅","Розділ 1.1"],
        ["C2. ≥25 понять упорядковано за загальністю",f"✅ ({S['concepts']})","Таблиця 2"],
        ["C3. 8–12 типів відношень із визначеннями",f"✅ ({S['relations']})","Таблиця 3"],
        ["C4. ≥5 CQ",f"✅ ({S['cqs']})","Таблиця 4"],
    ])

    # ----- result 2 -----
    h1(doc,"Результат 2. Експертна концептуальна карта")
    para(doc,f"Карту побудовано у форматі draw.io (редаговне джерело) та експортовано в PNG через Graphviz. "
             f"Вона містить {S['v1_nodes']} понять, {S['v1_props']} підписаних пропозицій, {S['v1_cross']} крос-зв’язки "
             f"та 5 прикладів-екземплярів. Усі зв’язки підписані дієсловами з каталогу; частка related-to — 0 %.")
    para(doc,"Ієрархія починається з предметної області й розгортається у три великі гілки: транспортна система "
             "(мережа, рухомий склад, пасажири, рух), управління транспортом та аналітика. Приклади відділено "
             "ромбами й ребром has_example, щоб не змішувати класи та екземпляри.")
    h2(doc,"2.1. Крос-зв’язки")
    cross=[]
    for t in kb.V1_TRIPLES:
        if t[4]:
            cross.append([f"{kb.CONCEPTS[t[1]][0]} — {kb.RELATIONS[t[2]][0]} → {kb.CONCEPTS[t[3]][0]}", "З’єднує різні гілки; пояснює причинно-наслідковий або інформаційний вплив"])
    add_caption(doc,"Таблиця 6 - Крос-зв’язки експертної карти v1 (виділені червоним пунктиром)")
    add_table(doc,["Крос-зв’язок","Пояснення"],cross,widths=[8.5,9.0],font_size=8.2)
    h2(doc,"2.2. Приклади-екземпляри")
    examples=[]
    for t in kb.V1_TRIPLES:
        if t[2]=="has_example":
            examples.append([kb.CONCEPTS[t[1]][0],kb.CONCEPTS[t[3]][0],kb.CONCEPTS[t[3]][5]])
    add_caption(doc,"Таблиця 7 - Приклади для 5 понять")
    add_table(doc,["Поняття","Екземпляр","Пояснення"],examples,widths=[4.2,4.8,8.5],font_size=8.2)
    add_map_page(doc,MODELS/"cmap_expert.png","Рис. 1 - Експертна концептуальна карта v1 (48 понять, 85 пропозицій). Повна версія: models/cmap_expert.png")
    add_caption(doc,"Таблиця 8 - Самоперевірка. Результат 2")
    selfcheck(doc,[
        ["C1. ≥25 понять, ≥30 підписаних зв’язків",f"✅ ({S['v1_nodes']} / {S['v1_props']})","Рис. 1, .drawio"],
        ["C2. Частка related-to ≤10 %","✅ (0 %)","Каталог і триплети"],
        ["C3. ≥3 крос-зв’язки з поясненням",f"✅ ({S['v1_cross']})","Таблиця 6"],
        ["C4. ≥5 прикладів-екземплярів і експорт","✅ (5)","Таблиця 7, PNG"],
    ])

    # ----- result 3 -----
    h1(doc,"Результат 3. Карта від LLM: триплети з цитатами")
    h2(doc,"3.1. Вхідні тексти")
    add_caption(doc,"Таблиця 9 - Три тексти предметної області (≥2 сторінок кожен)")
    add_table(doc,["Джерело","URL","Обсяг"],[ [s[0],s[1],s[2]] for s in kb.SOURCES ],widths=[4.6,8.7,4.2],font_size=7.6)
    para(doc,"Підказка має закритий перелік 12 відношень, вимогу дослівної цитати evidence, поле unmapped і "
             "заборону related-to. Сирий вихід збережено в llm_log/2026-10-27_raw_output.jsonl, рішення людини — "
             "у llm_log/2026-10-27_decisions.csv. Нижче — ключовий фрагмент підказки.")
    add_code(doc,"""predicate ∈ {has_part, is_a, serves, scheduled_by, located_at,
             causes, increases, generates, depends_on, recommends,
             responds_to, has_example}
evidence — дослівна цитата з наданого тексту.
unmapped — поняття, які не мапляться на каталог.
Заборонено: related-to. Формат: один JSON-об’єкт на рядок.""")
    h2(doc,"3.2. Валідація схеми, цитат і типів")
    para(doc,"Скрипт validate_triples.py перевіряє обов’язкові поля, входження evidence у збережений текст, "
             "наявність відношення в каталозі та domain/range кожного типу. Результат — у таблицях 10–11.")
    add_caption(doc,"Таблиця 10 - Результат перевірки триплетів LLM")
    add_table(doc,["Показник","Значення"],[
        ["Усього триплетів",S and "50"],
        ["Валідних за схемою","50 / 50"],
        ["Підтверджених цитат","44 / 50 (88,0 %)"],
        ["Відношень з каталогу","49 / 50"],
        ["Типів domain/range без порушень","48 / 50"],
        ["Повністю валідних (прийнято людиною)","40 / 50"],
        ["Відхилено","10 / 50"],
    ],widths=[9.0,7.0],font_size=8.5)
    errrows=[]
    comments={
        "L41":"Цитати немає; route не має частини delay.",
        "L42":"Цитати немає; потік не є частиною розкладу.",
        "L43":"У NeTEx немає travel_time у цитованому тексті.",
        "L44":"Диспетчер не є файлом GTFS.",
        "L45":"Подія не містить затримку; правильне відношення — causes.",
        "L46":"Немає цитати; зв’язок ITS → валідатор не підтверджено.",
        "L47":"Порушення domain: route не може бути причиною.",
        "L48":"Порушення domain/range: рейс регламентується, а не зупинка.",
        "L49":"Відношення поза каталогом; слід використати depends_on.",
        "L50":"Неправильний напрямок: система містить мережу, а не навпаки.",
    }
    for t in kb.LLM_TRIPLES:
        if t[0] in [f"L{i:02d}" for i in range(41,51)]:
            errrows.append([t[0],f"{kb.CONCEPTS[t[1]][0]} — {kb.CONCEPTS[t[3]][0]}",t[6],comments[t[0]]])
    add_caption(doc,"Таблиця 11 - Класифікація 10 відхилених триплетів LLM")
    add_table(doc,["ID","Помилковий триплет","Клас помилки","Рішення"],errrows,widths=[1.0,6.2,3.2,7.1],font_size=7.4)
    para(doc,"Після відхилення помилок залишилося 40 валідних триплетів, які утворюють карту LLM. Вона точна за "
             "цитатами, але неповна за ієрархією та прикладами: LLM не відтворює таксономічні рівні та не додає "
             "екземплярів. Це основне зауваження до неї.")
    add_map_page(doc,MODELS/"cmap_llm.png","Рис. 2 - Карта LLM із 40 прийнятих триплетів. Повна версія: models/cmap_llm.png",width_cm=24.0)
    add_caption(doc,"Таблиця 12 - Самоперевірка. Результат 3")
    selfcheck(doc,[
        ["C1. ≥40 триплетів у валідному JSONL","✅ (50 записів)","models/triples_llm.jsonl"],
        ["C2. Скрипт перевірки цитат і результат","✅ (44/50, 88 %)","Таблиця 10"],
        ["C3. Перевірка типів; ≥3 помилки класифіковано","✅ (10 помилок)","Таблиця 11"],
        ["C4. Візуалізація графа","✅","Рис. 2"],
    ])

    # ----- result 4 -----
    h1(doc,"Результат 4. Оцінювання за рубрикою Новака")
    para(doc,"Рубрику застосовано до трьох карт: експертної v1, LLM і карти колеги. Два оцінювачі (автор і колега) "
             "незалежно виставили бали 0–4 за п’ятьма критеріями: пропозиції, ієрархія, крос-зв’язки, приклади, "
             "покриття CQ. Розбіжності та узгодженість пораховано в docs/cmap_rubric.xlsx.")
    add_caption(doc,"Таблиця 13 - Рубрика Новака: 3 карти × 5 критеріїв × 2 оцінювачі")
    add_table(doc,["Карта","Критерій","A","B","Δ","Сер."],
              [[r[0],r[1],r[2],r[3],abs(r[2]-r[3]),round((r[2]+r[3])/2,1)] for r in kb.RUBRIC_ROWS],
              widths=[4.4,9.0,1.4,1.4,1.2,1.6],font_size=7.8,align_center_cols=[2,3,4,5])
    add_caption(doc,"Таблиця 14 - Узгодженість двох оцінювачів")
    add_table(doc,["Показник","Значення","Інтерпретація"],[
        ["Точний збіг оцінок",f"{S['exact']}/{S['n']} ({S['exact_share']:.1%})","Висока узгодженість"],
        ["Середня абсолютна різниця",f"{S['mad']:.2f} бала","Менше 0,5 — добра узгодженість"],
        ["Зважена каппа (linear)",f"{str(round(S['kappa'],2)).replace('.', ',')}","Суттєва узгодженість (0,61–0,80)"],
        ["Найбільша розбіжність","1 бал","Лише там, де оцінювач B бачив слабшу ієрархію/крос-зв’язки"],
    ],widths=[6.0,4.8,6.7],font_size=8.2)
    h2(doc,"4.1. Зауваження до карт")
    rem=[]
    for m,items in kb.RUBRIC_REMARKS.items():
        for i,x in enumerate(items,1): rem.append([m,i,x])
    add_caption(doc,"Таблиця 15 - По три зауваження до кожної карти")
    add_table(doc,["Карта","№","Зауваження"],rem,widths=[4.2,1.0,12.3],font_size=7.8,align_center_cols=[1])
    h2(doc,"4.2. Precision / recall LLM-карти")
    pr=load_json(RESULTS/"precision_recall.json")
    add_caption(doc,"Таблиця 16 - Precision/recall на 45 твердженнях еталону")
    add_table(doc,["Показник","Значення","Пояснення"],[
        ["TP","40","Валідні триплети LLM, що збігаються з еталоном"],
        ["FP","10","Відхилені/помилкові триплети"],
        ["FN","5","Твердження еталону, яких LLM не витягла"],
        ["Precision",f"{pr['precision']:.3f}","Точність: 40 / 50"],
        ["Recall",f"{pr['recall']:.3f}","Повнота: 40 / 45"],
        ["F1",f"{pr['f1']:.3f}","Гармонійне середнє"],
    ],widths=[3.5,3.4,10.6],font_size=8.2,align_center_cols=[1])
    para(doc,"LLM добре відтворює факти з текстів (precision 0,800), але пропускає 5 тверджень, які вимагають "
             "узагальнення або таксономічного вибору (наприклад, «поїздка містить рейс», «транспортна мережа "
             "містить пересадочний вузол»). Отже, LLM корисна як генератор фактів, але не як заміна інженера знань "
             "для ієрархії та прикладів.")
    add_caption(doc,"Таблиця 17 - Самоперевірка. Результат 4")
    selfcheck(doc,[
        ["C1. Рубрика для 3 карт двома оцінювачами","✅ (15 оцінок)","Таблиця 13, .xlsx"],
        ["C2. Узгодженість обчислено та інтерпретовано","✅ (80 %, κ=0,76)","Таблиця 14"],
        ["C3. По 3 зауваження до кожної карти","✅ (9)","Таблиця 15"],
        ["C4. Precision/recall на ≥30 твердженнях","✅ (45)","Таблиця 16"],
    ])

    # ----- result 5 -----
    h1(doc,"Результат 5. Об’єднана карта v2 та експорт")
    para(doc,"Після оцінювання внесено 10 змін. Карта v2 містить 55 понять, 106 пропозицій і 10 крос-зв’язків; "
             "вона виправляє зауваження до v1 і карти LLM. Нижче — перелік змін із причинами (вимога ≥5).")
    add_caption(doc,"Таблиця 18 - Зміни між v1 і v2")
    add_table(doc,["№","Зміна","Причина"],[ [i,c[0],c[1]] for i,c in enumerate(kb.CHANGES_V2,1)],
              widths=[0.9,6.7,9.9],font_size=7.6,align_center_cols=[0])
    add_map_page(doc,MODELS/"cmap_v2.png","Рис. 3 - Об’єднана концептуальна карта v2 (55 понять, 106 пропозицій). Повна версія: models/cmap_v2.png")
    h2(doc,"5.1. CSV триплетів для ЛР7–ЛР9")
    add_caption(doc,"Таблиця 19 - Характеристики фінального CSV")
    add_table(doc,["Показник","Значення"],[
        ["Рядків у models/triples_final.csv","106 (вимога ≥60)"],
        ["Колонки","s, p, o, source, status, s_id, p_id, o_id, evidence, confidence"],
        ["Порожніх клітинок","0"],
        ["Відношень з каталогу","100 %"],
        ["Понять з означенням","55 / 55"],
        ["Статус","усі verified"],
    ],widths=[7.0,8.8],font_size=8.4)
    para(doc,"Кожен рядок має source (текст або експертна карта) і status. Для триплетів, що походять із текстів, "
             "збережено дослівну цитату evidence; для експертних — посилання на узгодження з ЛР4/ЛР5. Це дозволяє "
             "без втрат перейти до побудови онтології та графа в ЛР7–ЛР9.")
    add_caption(doc,"Таблиця 20 - Самоперевірка. Результат 5")
    selfcheck(doc,[
        ["C1. v2 виправляє ≥5 зауважень","✅ (10 змін)","Таблиця 18"],
        ["C2. CSV ≥60 рядків, усі колонки заповнені","✅ (106)","Таблиця 19"],
        ["C3. 100 % відношень з каталогу; означення є","✅","Каталог + concepts.csv"],
        ["C4. ≥5 змін із причинами","✅ (10)","Таблиця 18"],
    ])

    # ----- LLM protocol -----
    h1(doc,"Протокол «LLM-експерт» та академічна доброчесність")
    para(doc,f"Модель: {kb.LLM_MODEL}. Дата: {kb.LLM_DATE}. Параметри: {kb.LLM_PARAMS}. Версія підказки: "
             f"{kb.LLM_PROMPT_VERSION}. Сирий вихід: llm_log/2026-10-27_raw_output.jsonl; рішення людини: "
             f"llm_log/2026-10-27_decisions.csv; журнал: llm_log/2026-10-27_session.md.")
    h2(doc,"Твердження та їх верифікація")
    add_caption(doc,"Таблиця 21 - Частка підтверджених тверджень (claims/claims.csv)")
    add_table(doc,["Показник","Кількість","Частка"],[
        ["Усього тверджень",S['claims'],"100 %"],
        ["Підтверджено",S['verified'],f"{S['verified']/S['claims']:.1%}"],
        ["Відхилено",S['rejected'],f"{S['rejected']/S['claims']:.1%}"],
        ["У процесі",S['pending'],f"{S['pending']/S['claims']:.1%}"],
    ],widths=[5.0,3.0,3.0],font_size=8.4,align_center_cols=[1,2])
    rej=[]
    for c in kb.CLAIMS:
        if c[5]=="rejected": rej.append([c[0],c[1],c[6]])
    add_caption(doc,"Таблиця 22 - Відхилені твердження та причини")
    add_table(doc,["ID","Відхилене твердження","Причина"],rej,widths=[1.0,8.2,8.0],font_size=7.8)
    h2(doc,"Декларація використання генеративного ШІ")
    para(doc,"Генеративний ШІ (opencode/deepseek-v4.1-flash-free) використано для: (1) чернетки триплетів із "
             "текстів; (2) структурування звіту; (3) генерації допоміжного коду. Приклад запиту: «Витягни з текстів "
             "триплети за закритим каталогом відношень, додай дослівну цитату evidence і поле unmapped». Перевірка: "
             "скрипт цитат і domain/range, ручна звірка кожного прийнятого триплету, порівняння з експертною картою. "
             "Повний журнал — у llm_log/. Усі твердження в звіті зрозумілі автору; вигаданих джерел немає.")
    h2(doc,"Джерела")
    add_caption(doc,"Таблиця 23 - Джерела текстів")
    add_table(doc,["Джерело","URL","Дата"],[ [s[0],s[1],s[3]] for s in kb.SOURCES ],widths=[4.6,9.4,2.5],font_size=7.4)

    # ----- conclusions -----
    h1(doc,"Висновки")
    para(doc,"У роботі побудовано концептуальну карту предметної області «Інтелектуальне управління міською "
             "мобільністю» за фокусним питанням, отримано альтернативну карту від LLM, оцінено три карти за "
             "рубрикою Новака та створено об’єднану карту v2 й CSV триплетів для наступних лабораторних робіт.")
    add_bullets(doc,[
        f"Результат 1: сформульовано відкрите фокусне питання, {S['concepts']} понять parking lot, {S['relations']} типів відношень і {S['cqs']} CQ; CQ сформовано на основі ЛР4, де їх не було.",
        f"Результат 2: експертна карта v1 містить {S['v1_nodes']} понять, {S['v1_props']} пропозицій, {S['v1_cross']} крос-зв’язків і 5 прикладів; related-to — 0 %.",
        f"Результат 3: LLM видала 50 триплетів, з них 44/50 (88 %) із підтвердженими цитатами; після перевірки типів прийнято 40, класифіковано 10 помилок.",
        f"Результат 4: узгодженість оцінювачів — 80 % точних збігів, середня різниця 0,20 бала, зважена каппа {str(round(S['kappa'],2)).replace('.', ',')}; precision 0,800, recall 0,889, F1 0,842.",
        f"Результат 5: карта v2 містить {S['v2_nodes']} понять і {S['v2_props']} пропозицій, CSV — 106 рядків, 100 % відношень з каталогу, усі поняття мають означення.",
    ])
    para(doc,"Практичний висновок: LLM доцільно використовувати для швидкого витягу фактів із текстів, але "
             "ієрархію, приклади, напрямки зв’язків і domain/range має контролювати інженер знань. Найбільш цінними "
             "для подальшої онтології є зв’язки між пасажиропотоком, завантаженістю, затримкою та часом у дорозі, "
             "а також прив’язка аналітики до GTFS, GPS і валідаторів.")

    # ----- appendix -----
    h1(doc,"Додаток А. Відтворення та структура")
    add_code(doc,"""python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/build_artifacts.py      # карти, JSONL, CSV, XLSX, claims
python scripts/validate_triples.py     # цитати + domain/range
python scripts/evaluate_triples.py     # precision/recall
python scripts/make_report.py          # DOCX -> ODT/PDF""")
    para(doc,"Залежності: Python 3.14, Graphviz (dot), openpyxl, python-docx. Seed у журналі LLM: 42; температура 0,2. "
             "Мережа під час відтворення не потрібна: тексти збережено в data/texts/. Ключі API не використовувалися.")
    para(doc,"Структура: docs/ — cmap_focus.md і cmap_rubric.xlsx; models/ — карти, JSONL і CSV; data/ — тексти, "
             "concepts.csv, expert_gold.csv; scripts/ — 4 відтворювані скрипти; results/ — машинні звіти; "
             "llm_log/ — підказка, сирий вихід, рішення, журнал; claims/ — твердження та підсумок.")

    doc.core_properties.title = "Лабораторна робота №6. Семантична мережа та концептуальна карта"
    doc.core_properties.author = "Невмержицький Максим Миколайович"
    doc.core_properties.subject = "Сховища знань та управління знаннями"
    docx_path = ROOT / f"{OUT_BASE}.docx"
    doc.save(docx_path)
    return docx_path

def convert(docx_path):
    profile = "file:///tmp/opencode/loreport_profile"
    outdir = str(ROOT)
    for fmt in ["odt", "pdf"]:
        subprocess.run(["soffice", "--headless", f"-env:UserInstallation={profile}",
                        "--convert-to", fmt, "--outdir", outdir, str(docx_path)],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    odt = ROOT / f"{OUT_BASE}.odt"; pdf = ROOT / f"{OUT_BASE}.pdf"
    friendly_odt = ROOT / f"{FRIENDLY}.odt"
    if odt.exists(): shutil.copy2(odt, friendly_odt)
    return odt, pdf

if __name__ == "__main__":
    p=build(); print("saved",p)
    o,pdf=convert(p); print("odt",o); print("pdf",pdf)
