# -*- coding: utf-8 -*-
"""Генерує рисунки звіту ЛР8."""
import json, subprocess
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from kb8 import MODELS, RESULTS

def pipeline():
    dot = '''digraph G {
rankdir=LR; bgcolor="white"; fontname="DejaVu Sans"; nodesep=0.25; ranksep=0.35;
node [shape=box, style="rounded,filled", fillcolor="#EAF2F8", color="#2C3E50", fontname="DejaVu Sans", fontsize=11, margin="0.12,0.07"];
edge [color="#2C3E50", arrowsize=0.7, fontname="DejaVu Sans", fontsize=9];
prompt [label="Питання +\\nсхема"];
llm [label="LLM\\nчернетка SPARQL"];
parser [label="Парсер\\nrdflib"];
schema [label="Перевірка\\nсхеми mm:"];
exec [label="Fuseki\\nLIMIT 100"];
cmp [label="Порівняння\\nз еталоном"];
prompt -> llm -> parser -> schema -> exec -> cmp;
schema -> stop [label="відхилено", style=dashed, color="#C0392B", fontcolor="#C0392B"];
stop [label="звіт про\\nпомилку", fillcolor="#FDEDEC", color="#C0392B"];
}
'''
    p = MODELS / "pipeline.dot"; p.write_text(dot, encoding="utf-8")
    subprocess.run(["dot", "-Tpng", str(p), "-o", str(MODELS / "pipeline.png")], check=True)

def bars():
    d = json.loads((RESULTS / "t2s_results.json").read_text(encoding="utf-8"))
    s = d["summary"]
    labels = ["Синтаксис", "Схема", "Правильний результат"]
    before = [s["before"]["syntax"], s["before"]["schema"], s["before"]["correct"]]
    after = [s["after"]["syntax"], s["after"]["schema"], s["after"]["correct"]]
    x = range(len(labels)); w = 0.36
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=180)
    ax.bar([i-w/2 for i in x], before, w, label="до покращення", color="#C0392B")
    ax.bar([i+w/2 for i in x], after, w, label="після покращення", color="#1E8449")
    for i, (b, a) in enumerate(zip(before, after)):
        ax.text(i-w/2, b+0.25, str(b), ha="center", fontsize=10)
        ax.text(i+w/2, a+0.25, str(a), ha="center", fontsize=10)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_ylim(0, 17); ax.set_ylabel("Кількість із 15")
    ax.set_title("Text-to-SPARQL: метрики до і після покращення підказки")
    ax.legend(); ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(MODELS / "t2s_metrics.png"); plt.close(fig)

    q = json.loads((RESULTS / "query_results.json").read_text(encoding="utf-8"))["timing"]
    labels = ["HTTP baseline", "HTTP optimized", "rdflib baseline", "rdflib optimized"]
    vals = [q["baseline_median_ms"], q["optimized_median_ms"],
            q["inprocess_baseline_median_ms"], q["inprocess_optimized_median_ms"]]
    fig, ax = plt.subplots(figsize=(7.5, 3.2), dpi=180)
    cols = ["#C0392B", "#1E8449", "#C0392B", "#1E8449"]
    ax.bar(labels, vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.15, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_ylabel("мс, медіана")
    ax.set_title("Час виконання запиту Q06: baseline vs optimized")
    ax.tick_params(axis="x", rotation=12); ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(MODELS / "query_timing.png"); plt.close(fig)

    sh = json.loads((RESULTS / "shacl_summary.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(4.2, 3.0), dpi=180)
    ax.bar(["Валідний", "Дефектний"], [sh["valid"]["violations"], sh["invalid"]["violations"]],
           color=["#1E8449", "#C0392B"])
    for i, v in enumerate([sh["valid"]["violations"], sh["invalid"]["violations"]]):
        ax.text(i, v + 0.05, str(v), ha="center")
    ax.set_ylim(0, 4); ax.set_ylabel("Порушення")
    ax.set_title("SHACL: кількість порушень")
    fig.tight_layout(); fig.savefig(MODELS / "shacl_results.png"); plt.close(fig)

if __name__ == "__main__":
    pipeline(); bars(); print("figures:", [p.name for p in MODELS.glob("*.png")])
