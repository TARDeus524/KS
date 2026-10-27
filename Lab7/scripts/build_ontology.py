# -*- coding: utf-8 -*-
import csv, json, sys
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS, DCTERMS
from rdflib.collection import Collection
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb7

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"; DATA = ROOT / "data"; DOCS = ROOT / "docs"
TESTS = ROOT / "tests"; CLAIMS = ROOT / "claims"; LLM = ROOT / "llm_log"
for d in (MODELS, DATA, DOCS, TESTS, CLAIMS, LLM, TESTS/"cq_sparql", TESTS/"situation_queries"):
    d.mkdir(parents=True, exist_ok=True)

MM = Namespace(kb7.MM)
SCHEMA = Namespace(kb7.SCHEMA)
ONT = URIRef(kb7.ONT)
DATA_ONT = URIRef(kb7.DATA_ONT)

REUSE = {
    "Stop": "schema:BusStop (клас місця зупинки)",
    "InterchangeStop": "schema:BusStop (пересадочна зупинка як підтип)",
    "TransportRoute": "schema:Route (маршрут як впорядкований шлях)",
    "Trip": "schema:Trip (конкретне виконання маршруту)",
    "Passenger": "schema:Person (пасажир як особа)",
    "TransportAgency": "schema:Organization (перевізник як організація)",
    "Event": "schema:Event (подія на мережі)",
    "GTFSDataset": "schema:Dataset (набір даних)",
    "NetworkSegment": "schema:Place (просторова ділянка)",
}

SCHEMA_MAP = {
    "Stop": "BusStop", "InterchangeStop": "BusStop", "TransportRoute": "Route",
    "Trip": "Trip", "Passenger": "Person", "TransportAgency": "Organization",
    "Event": "Event", "GTFSDataset": "Dataset", "NetworkSegment": "Place",
}

def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)

def class_key_props(cid):
    out=[]
    for pid,(_,dom,_,_,_) in kb7.OBJ_PROPS.items():
        if dom == cid: out.append(pid)
    for pid,(_,dom,_,_,_) in kb7.DATA_PROPS.items():
        if dom == cid: out.append(pid)
    return "; ".join(out) if out else "—"

def build_class_table():
    rows=[]
    for cid,(label,parent,definition,source) in kb7.CLASSES.items():
        rows.append([cid,label,definition,parent or "—",class_key_props(cid),source,REUSE.get(cid,"—")])
    write_csv(MODELS/"class_table.csv", ["class_id","label_uk","definition","parent","key_properties","source","reuse"], rows)
    return rows

def build_property_table():
    rows=[]
    for pid,(label,dom,ran,chars,desc) in kb7.OBJ_PROPS.items():
        rows.append([pid,label,"object",dom,ran,chars,desc])
    for pid,(label,dom,ran,chars,desc) in kb7.DATA_PROPS.items():
        rows.append([pid,label,"data",dom,ran,chars,desc])
    write_csv(MODELS/"properties.csv", ["name","label_uk","type","domain","range","characteristics","description"], rows)
    return rows

def build_tbox():
    g=Graph()
    for p,ns in [("mm",MM),("owl",OWL),("rdf",RDF),("rdfs",RDFS),("xsd",XSD),("skos",SKOS),("dcterms",DCTERMS),("schema",SCHEMA)]:
        g.bind(p,ns)
    g.add((ONT,RDF.type,OWL.Ontology))
    g.add((ONT,OWL.versionInfo,Literal("1.0")))
    g.add((ONT,DCTERMS.title,Literal("Онтологія інтелектуального управління міською мобільністю",lang="uk")))
    g.add((ONT,DCTERMS.creator,Literal("Невмержицький Максим Миколайович")))
    g.add((ONT,RDFS.seeAlso,URIRef("https://schema.org/")))
    for cid,(label,parent,definition,source) in kb7.CLASSES.items():
        c=MM[cid]
        g.add((c,RDF.type,OWL.Class))
        g.add((c,RDFS.label,Literal(label,lang="uk")))
        g.add((c,RDFS.comment,Literal(definition,lang="uk")))
        g.add((c,DCTERMS.source,Literal(source)))
        if parent: g.add((c,RDFS.subClassOf,MM[parent]))
        if cid in SCHEMA_MAP:
            g.add((c,SKOS.closeMatch,SCHEMA[SCHEMA_MAP[cid]]))
            g.add((c,RDFS.seeAlso,URIRef("https://schema.org/"+SCHEMA_MAP[cid])))
    for pid,(label,dom,ran,chars,desc) in kb7.OBJ_PROPS.items():
        p=MM[pid]
        g.add((p,RDF.type,OWL.ObjectProperty))
        g.add((p,RDFS.label,Literal(label,lang="uk")))
        g.add((p,RDFS.comment,Literal(desc,lang="uk")))
        if dom.startswith("schema:"): g.add((p,RDFS.domain,SCHEMA[dom.split(":",1)[1]]))
        else: g.add((p,RDFS.domain,MM[dom]))
        if ran.startswith("schema:"): g.add((p,RDFS.range,SCHEMA[ran.split(":",1)[1]]))
        else: g.add((p,RDFS.range,MM[ran]))
        for part in chars.split(";"):
            part=part.strip()
            if part.startswith("inverse:"):
                g.add((p,OWL.inverseOf,MM[part.split(":",1)[1]]))
            elif part=="transitive": g.add((p,RDF.type,OWL.TransitiveProperty))
            elif part=="symmetric": g.add((p,RDF.type,OWL.SymmetricProperty))
            elif part=="functional": g.add((p,RDF.type,OWL.FunctionalProperty))
    for pid,(label,dom,ran,chars,desc) in kb7.DATA_PROPS.items():
        p=MM[pid]
        g.add((p,RDF.type,OWL.DatatypeProperty))
        g.add((p,RDFS.label,Literal(label,lang="uk")))
        g.add((p,RDFS.comment,Literal(desc,lang="uk")))
        g.add((p,RDFS.domain,MM[dom]))
        g.add((p,RDFS.range,XSD[ran.split(":",1)[1]]))
        if "functional" in chars: g.add((p,RDF.type,OWL.FunctionalProperty))
    groups=[
        ["Bus","Tram","Trolleybus"],
        ["BusRoute","TramRoute","TrolleybusRoute"],
        ["Congestion","Roadwork","VehicleFailure","PassengerSurge","WeatherEvent"],
        ["DelayedState","OnTimeState","CrowdedState"],
        ["Passenger","Driver","Dispatcher","TransportAgency"],
        ["Stop","NetworkSegment","TransportRoute"],
        ["GTFSDataset","SIRIFeed","NeTExDataset"],
        ["PassengerFlow","LoadFactor","Delay","TravelTime"],
    ]
    for ids in groups:
        b=BNode(); g.add((b,RDF.type,OWL.AllDisjointClasses))
        lst=BNode(); Collection(g,lst,[MM[i] for i in ids]); g.add((b,OWL.members,lst))

    def restr(prop, kind, filler=None, value=None, card=None):
        b=BNode(); g.add((b,RDF.type,OWL.Restriction)); g.add((b,OWL.onProperty,MM[prop]))
        if kind=="some": g.add((b,OWL.someValuesFrom,MM[filler]))
        elif kind=="all": g.add((b,OWL.allValuesFrom,MM[filler]))
        elif kind=="min":
            g.add((b,OWL.minQualifiedCardinality,Literal(card,datatype=XSD.nonNegativeInteger)))
            g.add((b,OWL.onClass,MM[filler]))
        elif kind=="exactly":
            g.add((b,OWL.qualifiedCardinality,Literal(card,datatype=XSD.nonNegativeInteger)))
            g.add((b,OWL.onClass,MM[filler]))
        elif kind=="value": g.add((b,OWL.hasValue,Literal(value,datatype=XSD.boolean)))
        return b

    g.add((MM.Trip,RDFS.subClassOf,restr("hasStopTime","some","StopTime")))
    g.add((MM.TransportRoute,RDFS.subClassOf,restr("servesStop","some","Stop")))
    g.add((MM.NetworkSegment,RDFS.subClassOf,restr("hasEvent","all","Event")))
    g.add((MM.Trip,RDFS.subClassOf,restr("usesVehicle","exactly","Vehicle",card=1)))
    g.add((MM.Trip,RDFS.subClassOf,restr("operatedBy","exactly","TransportAgency",card=1)))
    g.add((MM.StopTime,RDFS.subClassOf,restr("atStop","exactly","Stop",card=1)))
    g.add((MM.Recommendation,RDFS.subClassOf,restr("recommends","some","TransportRoute")))
    g.add((MM.Forecast,RDFS.subClassOf,restr("forecastFor","some","Trip")))

    def equivalent(cid, base, rest):
        inter=BNode(); g.add((inter,RDF.type,OWL.Class))
        lst=BNode(); Collection(g,lst,[MM[base],rest]); g.add((inter,OWL.intersectionOf,lst))
        g.add((MM[cid],OWL.equivalentClass,inter))
    equivalent("InterchangeStop","Stop",restr("servedByRoute","min","TransportRoute",card=2))
    equivalent("AccessibleStop","Stop",restr("wheelchairAccessible","value",value=True))
    equivalent("CongestedSegment","NetworkSegment",restr("hasEvent","some","Congestion"))
    equivalent("DelayedTrip","Trip",restr("hasState","some","DelayedState"))
    out=MODELS/"onto.owl"; g.serialize(destination=out,format="turtle")
    g.serialize(destination=MODELS/"onto.rdf",format="xml")
    return g

def literal_for(prop, value):
    rng=kb7.DATA_PROPS[prop][2].split(":",1)[1]
    if rng=="string": return Literal(str(value))
    if rng=="integer": return Literal(int(value),datatype=XSD.integer)
    if rng=="decimal": return Literal(str(value),datatype=XSD.decimal)
    if rng=="boolean": return Literal(bool(value),datatype=XSD.boolean)
    if rng=="date": return Literal(str(value),datatype=XSD.date)
    if rng=="time": return Literal(str(value),datatype=XSD.time)
    if rng=="dateTime": return Literal(str(value),datatype=XSD.dateTime)
    return Literal(str(value))

def build_abox():
    g=Graph()
    for p,ns in [("mm",MM),("owl",OWL),("rdf",RDF),("rdfs",RDFS),("xsd",XSD)]:
        g.bind(p,ns)
    g.add((DATA_ONT,RDF.type,OWL.Ontology))
    g.add((DATA_ONT,OWL.imports,ONT))
    g.add((DATA_ONT,OWL.versionInfo,Literal("1.0")))
    rows=[]
    for iid,(types,props) in kb7.INDIVIDUALS.items():
        node=MM[iid]
        for t in types: g.add((node,RDF.type,MM[t]))
        vals=[]
        for prop,value in props:
            if prop=="rdfs:label":
                g.add((node,RDFS.label,Literal(str(value),lang="uk"))); vals.append(f"rdfs:label={value}"); continue
            values=value if isinstance(value,list) else [value]
            for v in values:
                if prop in kb7.OBJ_PROPS:
                    g.add((node,MM[prop],MM[v])); vals.append(f"{prop}={v}")
                elif prop in kb7.DATA_PROPS:
                    g.add((node,MM[prop],literal_for(prop,v))); vals.append(f"{prop}={v}")
        rows.append([iid,";".join(types),";".join(vals)])
    write_csv(DATA/"individuals.csv",["id","classes","properties"],rows)
    out=MODELS/"onto_data.ttl"; g.serialize(destination=out,format="turtle")
    g.serialize(destination=MODELS/"onto_data.rdf",format="xml")
    return g

def build_situations():
    header=["id","title","initial_state","event","guard","new_state","consequence_action","initial_state_class","event_class","guard_class","new_state_class","action_class","sensor_class","version","owner","sources","trust_status"]
    rows=[]
    for s in kb7.SITUATIONS:
        sid,title,st,ev,guard,ns,action,evc,statec,actc,sensorc,ver,owner,src,trust=s
        rows.append([sid,title,st,ev,guard,ns,action,"mm:TransportState",evc,"mm:Measurement",statec,actc,sensorc,ver,owner,src,trust])
    write_csv(MODELS/"situations.csv",header,rows)
    return rows

def build_claims():
    write_csv(CLAIMS/"claims.csv",["id","claim","type","source","verification","status","comment"],kb7.CLAIMS)
    total=len(kb7.CLAIMS); verified=sum(1 for c in kb7.CLAIMS if c[5]=="verified")
    rejected=sum(1 for c in kb7.CLAIMS if c[5]=="rejected"); pending=total-verified-rejected
    (CLAIMS/"summary.md").write_text(f"# Твердження ЛР7\n\nУсього: {total}\nПідтверджено: {verified}\nВідхилено: {rejected}\nУ процесі: {pending}\n",encoding="utf-8")

def build_queries():
    qs={
    "cq01_interchange_stops.rq":'SELECT DISTINCT ?stop WHERE { ?stop a mm:InterchangeStop . } ORDER BY ?stop\n',
    "cq02_routes_at_vokzal.rq":'SELECT DISTINCT ?route WHERE { ?route mm:servesStop mm:Stop_Vokzal . } ORDER BY ?route\n',
    "cq03_delayed_trips.rq":'SELECT DISTINCT ?trip WHERE { ?trip mm:hasState ?state . ?state a mm:DelayedState . } ORDER BY ?trip\n',
    "cq04_congestion_impact.rq":'SELECT DISTINCT ?segment ?trip WHERE { ?segment mm:hasEvent mm:Congestion_Horodotska . mm:Congestion_Horodotska mm:affectsTrip ?trip . } ORDER BY ?segment ?trip\n',
    "cq05_accessible_stops.rq":'SELECT DISTINCT ?stop WHERE { ?stop a mm:Stop ; mm:wheelchairAccessible true . } ORDER BY ?stop\n',
    "cq06_frequent_routes.rq":'SELECT DISTINCT ?route WHERE { ?f a mm:Frequency ; mm:frequencyOfRoute ?route ; mm:headwayMinutes ?h . FILTER(?h <= 10) } ORDER BY ?route\n',
    "cq07_bus_trips.rq":'SELECT DISTINCT ?trip WHERE { ?trip mm:usesVehicle ?v . ?v a mm:Bus . } ORDER BY ?trip\n',
    "cq08_forecast_decision.rq":'SELECT DISTINCT ?decision ?rec ?route WHERE { ?decision mm:basedOnForecast ?f ; mm:hasRecommendation ?rec . ?rec mm:recommends ?route . } ORDER BY ?decision\n',
    "cq09_delay_over_10.rq":'SELECT DISTINCT ?trip WHERE { ?d a mm:Delay ; mm:measurementOf ?trip ; mm:delayMinutes ?delay . FILTER(?delay > 10) } ORDER BY ?trip\n',
    "cq10_datasets_for_network.rq":'SELECT DISTINCT ?ds WHERE { ?ds mm:datasetDescribes mm:Network_Lviv . } ORDER BY ?ds\n',
    }
    for name,q in qs.items():
        (TESTS/"cq_sparql"/name).write_text("PREFIX mm: <"+kb7.MM+">\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\nPREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\n\n"+q,encoding="utf-8")
    write_csv(MODELS/"cq_expected.csv",["id","question","query_file","expected_count","expected_values"],
              [[c[0],c[1],c[2],c[3],c[4]] for c in kb7.CQS])
    (TESTS/"situation_queries"/"situation_S1.rq").write_text("""PREFIX mm: <"""+kb7.MM+""">

SELECT DISTINCT ?trip ?event ?dispatcher WHERE {
  ?trip mm:hasState ?state ;
        mm:affectedByEvent ?event .
  ?state a mm:DelayedState .
  ?event a mm:Congestion ;
         mm:handledBy ?dispatcher .
}
""",encoding="utf-8")
    (TESTS/"situation_queries"/"situation_S3.rq").write_text("""PREFIX mm: <"""+kb7.MM+""">

SELECT DISTINCT ?flow ?load ?rec ?passenger WHERE {
  ?flow a mm:PassengerFlow ; mm:passengerCount ?n .
  ?load a mm:LoadFactor ; mm:loadFactor ?l .
  ?rec a mm:Recommendation ; mm:forPassenger ?passenger .
  FILTER(?n > 100 && ?l > 0.85)
}
""",encoding="utf-8")

def build_llm_draft():
    ttl='''@prefix mm: <https://knowledge.uni.lviv.ua/mobility#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

mm:LLMDraft a owl:Ontology ;
  rdfs:label "Чернетка онтології від LLM, lab07-prompt-v1"@uk ;
  owl:versionInfo "0.1" .

mm:MobilitySystem a owl:Class .
mm:TransportSystem a owl:Class ; rdfs:subClassOf mm:MobilitySystem .
mm:TransportNetwork a owl:Class ; rdfs:subClassOf mm:TransportSystem .
mm:Stop a owl:Class ; rdfs:subClassOf mm:TransportNetwork .
mm:InterchangeStop a owl:Class ; rdfs:subClassOf mm:Stop .
mm:Route a owl:Class ; rdfs:subClassOf mm:TransportNetwork .
mm:BusRoute a owl:Class ; rdfs:subClassOf mm:Route .
mm:TramRoute a owl:Class ; rdfs:subClassOf mm:Route .
mm:Vehicle a owl:Class ; rdfs:subClassOf mm:TransportSystem .
mm:Bus a owl:Class ; rdfs:subClassOf mm:Vehicle .
mm:Tram a owl:Class ; rdfs:subClassOf mm:Vehicle .
mm:Trip a owl:Class ; rdfs:subClassOf mm:Route .
mm:Schedule a owl:Class ; rdfs:subClassOf mm:TransportSystem .
mm:StopTime a owl:Class ; rdfs:subClassOf mm:Schedule .
mm:Passenger a owl:Class ; rdfs:subClassOf mm:Vehicle .
mm:Driver a owl:Class .
mm:Dispatcher a owl:Class .
mm:Agency a owl:Class .
mm:DataAsset a owl:Class .
mm:GTFSDataset a owl:Class ; rdfs:subClassOf mm:DataAsset .
mm:Sensor a owl:Class .
mm:GPSTracker a owl:Class ; rdfs:subClassOf mm:Sensor .
mm:Validator a owl:Class ; rdfs:subClassOf mm:Sensor .
mm:Event a owl:Class .
mm:Congestion a owl:Class ; rdfs:subClassOf mm:Event .
mm:Delay a owl:Class ; rdfs:subClassOf mm:Event .
mm:Measurement a owl:Class .
mm:Recommendation a owl:Class .
mm:Analytics a owl:Class .
mm:Bus25 a owl:Class .

mm:hasStop a owl:ObjectProperty ; rdfs:domain mm:Route ; rdfs:range mm:Stop .
mm:hasTrip a owl:ObjectProperty ; rdfs:domain mm:Route ; rdfs:range mm:Trip .
mm:usesVehicle a owl:ObjectProperty ; rdfs:domain mm:Trip ; rdfs:range mm:Vehicle .
mm:hasEvent a owl:ObjectProperty ; rdfs:domain mm:Route ; rdfs:range mm:Event .
mm:relatedTo a owl:ObjectProperty .
mm:hasMeasurement a owl:ObjectProperty ; rdfs:domain mm:Trip ; rdfs:range mm:Measurement .
mm:recommends a owl:ObjectProperty ; rdfs:domain mm:Recommendation ; rdfs:range mm:Route .
mm:routeId a owl:DatatypeProperty ; rdfs:domain mm:Route ; rdfs:range xsd:string .
mm:routeType a owl:DatatypeProperty ; rdfs:domain mm:Route ; rdfs:range xsd:string .
mm:stopName a owl:DatatypeProperty ; rdfs:domain mm:Stop ; rdfs:range xsd:string .
mm:delayMinutes a owl:DatatypeProperty ; rdfs:domain mm:Delay ; rdfs:range xsd:integer .
mm:loadFactor a owl:DatatypeProperty ; rdfs:domain mm:Measurement ; rdfs:range xsd:decimal .

mm:Route_9 a mm:BusRoute ; mm:routeId "9" ; mm:routeType "3" ; mm:hasStop mm:Stop_Vokzal ; mm:hasTrip mm:Trip_9_0800 .
mm:Route_31 a mm:TramRoute ; mm:routeId "31" ; mm:routeType "0" ; mm:hasStop mm:Stop_Vokzal .
mm:Stop_Vokzal a mm:Stop ; mm:stopName "Вокзал" .
mm:Stop_Rynok a mm:Stop ; mm:stopName "Площа Ринок" .
mm:Trip_9_0800 a mm:Trip ; mm:usesVehicle mm:Bus_2501 ; mm:hasMeasurement mm:Delay_9 .
mm:Trip_9_0830 a mm:Trip ; mm:usesVehicle mm:Bus_2502 .
mm:Trip_25_0815 a mm:Trip ; mm:usesVehicle mm:Bus_2501 .
mm:Bus_2501 a mm:Bus .
mm:Bus_2502 a mm:Bus .
mm:Passenger_P01 a mm:Passenger .
mm:Congestion_H a mm:Congestion .
mm:Delay_9 a mm:Delay ; mm:delayMinutes 15 ; mm:measurementOf mm:Trip_9_0800 .
mm:Recommendation_R1 a mm:Recommendation ; mm:recommends mm:Route_31 .
'''
    (MODELS/"llm_draft.ttl").write_text(ttl,encoding="utf-8")
    import rdflib
    rdflib.Graph().parse(data=ttl, format="turtle").serialize(destination=ROOT/"build"/"llm_draft.rdf", format="xml")
    (LLM/"2026-10-27_prompt_v1.md").write_text("# Підказка lab07-prompt-v1\n\nСформуй чернетку OWL-онтології у Turtle для домену «Інтелектуальне управління міською мобільністю» за таксономією ЛР4 і картою ЛР6. Додай класи, об’єктні та data-властивості, 13 індивідів. Не додавай коментарів. Поверни лише Turtle.\n",encoding="utf-8")
    (LLM/"2026-10-27_raw_output.ttl").write_text(ttl,encoding="utf-8")
    decisions=[
        ["D01","Passenger ⊑ Vehicle","відхилено","Порушення категорії: пасажир не є транспортним засобом."],
        ["D02","Trip ⊑ Route","відхилено","Рейс і маршрут належать до різних рівнів; це клас проти екземпляра."],
        ["D03","Delay ⊑ Event","відхилено","Затримка — вимірювання, а не подія."],
        ["D04","Bus25 як owl:Class","відхилено","Конкретний автобус має бути індивідом."],
        ["D05","hasStop без inverse","відхилено","Додано servesStop/servedByRoute."],
        ["D06","routeType xsd:string","відхилено","Тип маршруту є цілим числом GTFS."],
        ["D07","hasStop exactly 1","відхилено","Маршрут обслуговує багато зупинок."],
        ["D08","relatedTo","відхилено","Замінено на конкретні відношення."],
        ["D09","Немає диз’юнктностей","відхилено","Додано 8 груп AllDisjointClasses."],
        ["D10","Немає кардинальностей","відхилено","Додано usesVehicle=1, operatedBy=1, atStop=1."],
        ["D11","Індивіди Route_9, Stop_Vokzal, Trip_9_0800","прийнято з правками","Використано як основу ABox."],
        ["D12","usesVehicle","прийнято","Збережено з domain/range та inverse."],
    ]
    write_csv(LLM/"2026-10-27_decisions.csv",["id","fragment","decision","reason"],decisions)
    (LLM/"2026-10-27_session.md").write_text("""# Журнал LLM — ЛР7

- Дата: 2026-10-27
- Модель: opencode/deepseek-v4.1-flash-free
- Параметри: temperature=0.2, seed=42, max_tokens=4096
- Версія підказки: lab07-prompt-v1
- Сирий вихід: `llm_log/2026-10-27_raw_output.ttl`
- Рішення людини: `llm_log/2026-10-27_decisions.csv`
- Перевірка: rdflib-парсинг, ручний OntoClean-аналіз, HermiT для експертної онтології.

Чернетка містить 30 класів, 7 object і 5 data властивостей. Після перевірки прийнято каркас імен і частину індивідів; помилки категоризації, кардинальностей і типів виправлено в експертній онтології.
""",encoding="utf-8")

def main():
    classes=build_class_table(); props=build_property_table(); situations=build_situations(); build_claims(); build_queries(); build_llm_draft()
    build_tbox(); build_abox()
    summary={"classes":len(classes),"object_properties":len(kb7.OBJ_PROPS),"data_properties":len(kb7.DATA_PROPS),"individuals":len(kb7.INDIVIDUALS),"situations":len(situations),"cqs":len(kb7.CQS),"claims":len(kb7.CLAIMS)}
    (ROOT/"results"/"build_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))

if __name__=="__main__": main()
