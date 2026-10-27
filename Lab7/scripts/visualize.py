# -*- coding: utf-8 -*-
import subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb7
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"models"
OUT.mkdir(exist_ok=True)

def dot(src, out, fmt="png"):
    p=subprocess.run(["dot","-T"+fmt,"-o",str(out)],input=src.encode("utf-8"),capture_output=True)
    if p.returncode: raise SystemExit(p.stderr.decode())

def hierarchy():
    core=["MobilitySystem","TransportSystem","TransportNetwork","TransportNode","Stop","InterchangeStop","AccessibleStop","NetworkSegment","CongestedSegment","TransportRoute","BusRoute","TramRoute","TrolleybusRoute","Vehicle","Bus","Tram","Trolleybus","Trip","DelayedTrip","Actor","Passenger","Driver","Dispatcher","TransportAgency"]
    lines=['digraph G {','graph [rankdir=TB, bgcolor="white", nodesep=0.28, ranksep=0.55, pad=0.2];','node [shape=box, style="rounded,filled", fillcolor="#F2F3F4", color="#555555", fontname="DejaVu Sans", fontsize=10, margin="0.08,0.04"];','edge [color="#777777", arrowsize=0.6];','label="Ядро ієрархії онтології (24 з 58 класів)"; fontname="DejaVu Sans"; fontsize=14; labelloc=t;']
    for cid in core:
        fill="#DDEBF7" if cid in ("MobilitySystem","TransportSystem","TransportNetwork","TransportNode","Actor","DataAsset","Analytics","Event","TransportState","Measurement") else "#F2F3F4"
        lines.append(f'"{cid}" [label="{cid}", fillcolor="{fill}"];')
    for cid,(label,parent,defn,src) in kb7.CLASSES.items():
        if cid in core and parent in core: lines.append(f'"{parent}" -> "{cid}";')
    lines.append('}')
    dot("\n".join(lines), OUT/"class_hierarchy_core.png")

def abox():
    nodes={
      "Route_9":("Route_9","#DDEBF7"),"Trip_9_0800":("Trip_9_0800","#FFF2CC"),"Bus_2501":("Bus_2501","#E2EFDA"),
      "State_Delayed_9":("State_Delayed_9","#FCE4D6"),"Congestion_Horodotska":("Congestion_Horodotska","#F8CBAD"),
      "Dispatcher_01":("Dispatcher_01","#E4DFEC"),"Delay_9_0800":("Delay_9_0800","#EDEDED"),
      "Recommendation_R1":("Recommendation_R1","#E2EFDA"),"Stop_Vokzal":("Stop_Vokzal","#DDEBF7"),
      "Passenger_P01":("Passenger_P01","#E4DFEC"),"Agency_LvivAvtobus":("Agency_LvivAvtobus","#E4DFEC"),
    }
    edges=[("Route_9","hasTrip","Trip_9_0800"),("Trip_9_0800","usesVehicle","Bus_2501"),
           ("Trip_9_0800","hasState","State_Delayed_9"),("Trip_9_0800","affectedByEvent","Congestion_Horodotska"),
           ("Congestion_Horodotska","handledBy","Dispatcher_01"),("Trip_9_0800","hasMeasurement","Delay_9_0800"),
           ("Recommendation_R1","recommends","Route_9"),("Route_9","servesStop","Stop_Vokzal"),
           ("Recommendation_R1","forPassenger","Passenger_P01"),("Trip_9_0800","operatedBy","Agency_LvivAvtobus")]
    lines=['digraph A {','graph [rankdir=LR, bgcolor="white", nodesep=0.22, ranksep=0.45, pad=0.2];','node [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=11, color="#555555"];','edge [fontname="DejaVu Sans", fontsize=9, color="#555555", arrowsize=0.6];','label="Фрагмент ABox: затриманий рейс 9"; fontname="DejaVu Sans"; fontsize=14; labelloc=t;']
    for k,(lab,fill) in nodes.items(): lines.append(f'"{k}" [label="{lab}", fillcolor="{fill}"];')
    for s,p,o in edges: lines.append(f'"{s}" -> "{o}" [label="{p}"];')
    lines.append('}')
    dot("\n".join(lines), OUT/"abox_core.png")

if __name__=="__main__":
    hierarchy(); abox(); print("ok")
