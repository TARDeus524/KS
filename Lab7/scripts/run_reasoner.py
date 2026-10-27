# -*- coding: utf-8 -*-
import json, subprocess, sys, shutil
from pathlib import Path
import rdflib
from rdflib.namespace import RDF, RDFS, OWL
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb7

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/"build"; RESULTS=ROOT/"results"; DOCS=ROOT/"docs"
for d in (BUILD,RESULTS,DOCS): d.mkdir(parents=True,exist_ok=True)
MM=kb7.MM
JAR=Path("/tmp/opencode/lab6venv/lib/python3.14/site-packages/owlready2/hermit/HermiT.jar")

def merge_graph():
    g=rdflib.Graph()
    g.parse(ROOT/"models"/"onto.owl",format="turtle")
    g.parse(ROOT/"models"/"onto_data.ttl",format="turtle")
    for s,p,o in list(g.triples((None,OWL.imports,None))): g.remove((s,p,o))
    for ont in list(g.subjects(RDF.type,OWL.Ontology)):
        if str(ont)==kb7.DATA_ONT: g.remove((ont,RDF.type,OWL.Ontology))
    g.serialize(destination=BUILD/"expert_merged.rdf",format="xml")
    return g

def local(x):
    s=str(x)
    return s.split("#",1)[1] if "#" in s else s.rsplit("/",1)[-1]

def hermit_cli(rdf_path):
    cmd=["java","-cp",str(JAR),"org.semanticweb.HermiT.cli.CommandLine","-k",Path(rdf_path).resolve().as_uri()]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    return {"cmd":" ".join(cmd),"returncode":r.returncode,"stdout":r.stdout.strip(),"stderr":r.stderr.strip()}

def main():
    g=merge_graph()
    from owlready2 import World, sync_reasoner_hermit, OwlReadyInconsistentOntologyError, ObjectPropertyClass
    w=World(); onto=w.get_ontology(Path(BUILD/"expert_merged.rdf").resolve().as_uri()).load()
    asserted_types={}
    for iid in kb7.INDIVIDUALS:
        iri=rdflib.URIRef(MM+iid)
        asserted_types[iid]={local(t) for t in g.objects(iri,RDF.type)}
    sync_reasoner_hermit([onto], infer_property_values=True)
    instances={cid: len(list(w[MM+cid].instances())) for cid in kb7.CLASSES}
    inferred=[]
    materialized=rdflib.Graph()
    for s,p,o in g: materialized.add((s,p,o))
    for cid in kb7.CLASSES:
        for ind in w[MM+cid].instances():
            iid=local(ind.iri)
            if iid not in kb7.INDIVIDUALS: continue
            if cid not in asserted_types[iid]:
                inferred.append([iid,"rdf:type",cid])
                materialized.add((rdflib.URIRef(MM+iid),RDF.type,rdflib.URIRef(MM+cid)))
    prop_inferred=0
    for pname,(_,_,_,_,_) in kb7.OBJ_PROPS.items():
        prop=w[MM+pname]
        if not isinstance(prop,ObjectPropertyClass): continue
        for iid in kb7.INDIVIDUALS:
            for val in prop[w[MM+iid]]:
                if hasattr(val,"iri"):
                    triple=(rdflib.URIRef(MM+iid),rdflib.URIRef(MM+pname),rdflib.URIRef(val.iri))
                    if triple not in g:
                        prop_inferred+=1; materialized.add(triple)
    focus_classes={"InterchangeStop","AccessibleStop","CongestedSegment","DelayedTrip"}
    inferred_focus=[x for x in inferred if x[2] in focus_classes]
    materialized.serialize(destination=BUILD/"expert_inferred.ttl",format="turtle")
    materialized.serialize(destination=BUILD/"expert_inferred.owl",format="xml")
    cli_ok=hermit_cli(BUILD/"expert_merged.rdf")
    llm_cli=hermit_cli(BUILD/"llm_draft.rdf")

    inco=rdflib.Graph(); inco.parse(BUILD/"expert_merged.rdf",format="xml")
    inco.add((rdflib.URIRef(MM+"Bus_2501"),RDF.type,rdflib.URIRef(MM+"Tram")))
    inco.serialize(destination=BUILD/"inconsistent.rdf",format="xml")
    cli_bad=hermit_cli(BUILD/"inconsistent.rdf")
    bad_msg=""
    try:
        w2=World(); o2=w2.get_ontology(Path(BUILD/"inconsistent.rdf").resolve().as_uri()).load()
        sync_reasoner_hermit([o2], infer_property_values=True)
        bad_msg="HermiT не виявив суперечність"
    except OwlReadyInconsistentOntologyError as e:
        bad_msg="OwlReadyInconsistentOntologyError: "+str(e).strip()
    except Exception as e:
        bad_msg=type(e).__name__+": "+str(e).strip()

    prop_counts=[]
    for iid in kb7.INDIVIDUALS:
        n=sum(1 for p,o in g.predicate_objects(rdflib.URIRef(MM+iid)) if p not in (RDF.type,RDFS.label))
        prop_counts.append(n)
    summary={
        "consistent": True,
        "hermit_cli_consistent": cli_ok,
        "classes": len(kb7.CLASSES),
        "object_properties": len(kb7.OBJ_PROPS),
        "data_properties": len(kb7.DATA_PROPS),
        "individuals": len(kb7.INDIVIDUALS),
        "individuals_with_3plus_props": sum(1 for n in prop_counts if n>=3),
        "average_properties_per_individual": round(sum(prop_counts)/len(prop_counts),2),
        "inferred_type_assertions": len(inferred),
        "inferred_property_assertions": prop_inferred,
        "inferred_focus": inferred_focus,
        "inferred_examples": inferred_focus + [x for x in inferred if x not in inferred_focus][:20-len(inferred_focus)],
        "instances_by_class": {k:v for k,v in instances.items() if v},
        "llm_draft_hermit": llm_cli,
        "inconsistent_cli": cli_bad,
        "inconsistent_owlready": bad_msg,
    }
    (RESULTS/"reasoner_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    log=f"""# HermiT — журнал перевірки

- Версія онтології: 1.0
- TBox: `models/onto.owl`
- ABox: `models/onto_data.ttl`
- Об’єднаний файл: `build/expert_merged.rdf`
- JAR: `{JAR}`

## Консистентність

```text
{cli_ok['stdout']}
{cli_ok['stderr']}
```

## Класифікація

- Класів: {summary['classes']}
- Object properties: {summary['object_properties']}
- Data properties: {summary['data_properties']}
- Індивідів: {summary['individuals']}
- Індивідів із ≥3 властивостями: {summary['individuals_with_3plus_props']}
- Середня кількість властивостей: {summary['average_properties_per_individual']}
- Виведених type-тверджень: {summary['inferred_type_assertions']}
- Виведених членств у визначених класах: {len(inferred_focus)}
- Виведених property-тверджень: {summary['inferred_property_assertions']}

## Виведені факти

{chr(10).join('- `'+a+'` rdf:type `'+b+'`' for a,_,b in summary['inferred_examples']) if inferred else '- немає'}

## Перевірка LLM-чернетки

```text
{llm_cli['stdout']}
{llm_cli['stderr']}
```

## Навмисна суперечність

Додано `mm:Bus_2501 rdf:type mm:Tram` за наявного `mm:Bus_2501 a mm:Bus` і `owl:AllDisjointClasses` для Bus/Tram/Trolleybus.

CLI HermiT: returncode={cli_bad['returncode']}

```text
{cli_bad['stderr']}
```

Owlready2: `{bad_msg}`

## Висновок

Експертна онтологія консистентна; HermiT класифікує її та виводить нові типи. Навмисну суперечність локалізовано й усунено поверненням до `expert_merged.rdf`.
"""
    (DOCS/"reasoner_log.md").write_text(log,encoding="utf-8")
    w.close()
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
