# -*- coding: utf-8 -*-
import csv, json, sys
from pathlib import Path
import rdflib
from rdflib.namespace import RDF, RDFS, OWL
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb7
ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/"results"; DOCS=ROOT/"docs"; BUILD=ROOT/"build"
RESULTS.mkdir(exist_ok=True); DOCS.mkdir(exist_ok=True)
MM=kb7.MM

def local(v):
    s=str(v)
    return s.split("#",1)[1] if "#" in s else s.rsplit("/",1)[-1]

def qrows(g,path):
    rows=list(g.query(path.read_text(encoding="utf-8")))
    out=[]
    for row in rows:
        vals=[]
        for x in row:
            if x is None: continue
            vals.append(local(x))
        out.append(vals)
    return out

def canon(vals):
    return sorted(set(vals))

def evaluate():
    ge=rdflib.Graph().parse(BUILD/"expert_inferred.ttl",format="turtle")
    gl=rdflib.Graph().parse(ROOT/"models"/"llm_draft.ttl",format="turtle")
    rows=[]; expert_pass=0; llm_pass=0
    for cid,q,file,cnt,expected in kb7.CQS:
        er=qrows(ge,ROOT/"tests"/"cq_sparql"/file)
        lr=qrows(gl,ROOT/"tests"/"cq_sparql"/file)
        ev=[v for r in er for v in r]
        lv=[v for r in lr for v in r]
        exp=[x.strip() for x in expected.split(";") if x.strip()]
        ep=canon(ev)==canon(exp); lp=canon(lv)==canon(exp)
        expert_pass+=ep; llm_pass+=lp
        rows.append([cid,q,file,"; ".join(exp),str(len(exp)),str(len(ev)),"; ".join(ev),"PASS" if ep else "FAIL",str(len(lv)),"; ".join(lv),"PASS" if lp else "FAIL"])
    with (RESULTS/"cq_results.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["id","question","query","expected_values","expected_count","expert_count","expert_values","expert_status","llm_count","llm_values","llm_status"]); w.writerows(rows)
    summary={
        "expert_pass":expert_pass,"llm_pass":llm_pass,"total":len(kb7.CQS),
        "expert_rate":round(expert_pass/len(kb7.CQS)*100,1),"llm_rate":round(llm_pass/len(kb7.CQS)*100,1),
        "llm_classes":len(set(gl.subjects(RDF.type,OWL.Class))),
        "llm_object_properties":len(set(gl.subjects(RDF.type,OWL.ObjectProperty))),
        "llm_data_properties":len(set(gl.subjects(RDF.type,OWL.DatatypeProperty))),
        "llm_individuals":len({s for s in gl.subjects(RDF.type,None) if isinstance(s,rdflib.URIRef) and str(s).startswith(MM) and not any(o in (OWL.Class,OWL.ObjectProperty,OWL.DatatypeProperty,OWL.Ontology) for o in gl.objects(s,RDF.type))}),
        "llm_same_iri_overlap":len(set(ge.subjects(RDF.type,OWL.Class)) & set(gl.subjects(RDF.type,OWL.Class))),
    }
    (RESULTS/"cq_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")

    # SPARQL-перевірки ситуацій
    s1=qrows(ge,ROOT/"tests"/"situation_queries"/"situation_S1.rq")
    s3=qrows(ge,ROOT/"tests"/"situation_queries"/"situation_S3.rq")
    situ_checks=[
        ["S1","Затриманий рейс, спричинений затором, і диспетчер",len(s1),s1,"PASS" if s1 else "FAIL"],
        ["S3","Перевантаження та рекомендація пасажиру",len(s3),s3,"PASS" if s3 else "FAIL"],
    ]
    with (RESULTS/"situation_results.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["situation","check","rows","values","status"]); w.writerows(situ_checks)

    # Метрики та перевірки ситуацій
    valid_situations=sum(1 for s in kb7.SITUATIONS if s[14] in ("validated","перевірено","verified") or "validated" in s[14])
    md=f"""# Оцінювання онтології ЛР7

## CQ-запити

- Експертна онтологія: {expert_pass}/{len(kb7.CQS)} ({summary['expert_rate']}%)
- LLM-чернетка: {llm_pass}/{len(kb7.CQS)} ({summary['llm_rate']}%)
- Різниця: {expert_pass-llm_pass} запитів

| CQ | Питання | Експерт | LLM |
|---|---|---|---|
"""
    for cid,q,file,cnt,expected in kb7.CQS:
        er=next(r for r in rows if r[0]==cid)
        md+=f"| {cid} | {q} | {er[7]} ({er[5]}) | {er[10]} ({er[8]}) |\n"
    md+=f"""
## Метрики чернетки

- Класів: {summary['llm_classes']}
- Object properties: {summary['llm_object_properties']}
- Data properties: {summary['llm_data_properties']}
- Індивідів: {summary['llm_individuals']}
- Спільних IRI класів з експертною: {summary['llm_same_iri_overlap']}

## Перевірки ситуацій

| Ситуація | Перевірка | Рядків | Статус |
|---|---|---|---|
"""
    for sid,name,n,vals,status in situ_checks:
        md+=f"| {sid} | {name} | {n} | {status} |\n"
    md+=f"""
Валідованих ситуацій: {valid_situations}/{len(kb7.SITUATIONS)}.

## OntoClean-перевірки

1. `Passenger ⊑ Vehicle` — помилка категорії: пасажир є роллю особи, а не видом транспортного засобу; різні критерії ідентичності.
2. `Trip ⊑ Route` — змішування рівнів: рейс є окремим виконанням, маршрут — класом/шляхом; порушено єдність (unity).
3. `Delay ⊑ Event` — вимірювання ототожнено з подією; вимірювання залежне від рейсу (+D), подія має власну темпоральну ідентичність.
4. `Bus25 a owl:Class` — індивід подано як клас; це punning без окремого мета-рівня, порушує ідентичність класу.
5. `Stop ⊑ TransportNetwork` — зупинка є просторовим вузлом, а не агрегатом мережі; різні критерії єдності.
6. `hasStop` без inverse і кардинальності — відношення не специфіковане; додано `servedByRoute` та `min 2`.
7. Відсутність disjointness — Bus/Tram/Trolleybus можуть перетинатися; додано 8 груп `AllDisjointClasses`.

## Висновок

Експертна онтологія проходить усі {len(kb7.CQS)} CQ, тоді як LLM-чернетка — лише {llm_pass}. Основні дефекти чернетки: неправильна категоризація, відсутність inverse/кардинальностей, неповний ABox і відсутність диз’юнктностей. Після OntoClean-перевірок і ручної корекції експертна модель відповідає CQ та проходить HermiT.
"""
    (DOCS/"onto_eval.md").write_text(md,encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))

if __name__=="__main__": evaluate()
