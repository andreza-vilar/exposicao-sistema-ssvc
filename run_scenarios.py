#!/usr/bin/env python3
"""Roda o analisador em todos os cenários e reporta acurácia, matriz de confusão e erros por direção."""
import json
from pathlib import Path
from exposure_analyzer import Cloud, analyze, load_manifests, LEVELS, RANK

root = Path(__file__).parent / "scenarios"
conf = {e: {p: 0 for p in LEVELS} for e in LEVELS}
rows, under, over = [], 0, 0
for d in sorted(root.iterdir()):
    exp = json.load(open(d / "expected.json"))["system_exposure"]
    cloud = Cloud(json.load(open(d / "cloud.json"))) if (d / "cloud.json").exists() else None
    res = analyze(load_manifests(d / "manifests.yaml"), cloud)
    got = res["system_exposure"]
    conf[exp][got] += 1
    under += RANK[got] < RANK[exp]; over += RANK[got] > RANK[exp]
    wl = res["workloads"][0]
    rows.append((d.name, exp, got, wl["confidence"], "OK" if exp == got else "ERRO"))
for r in rows: print("{:<52} esperado={:<11} obtido={:<11} conf={:<6} {}".format(*r))
n = len(rows); ok = sum(r[4] == "OK" for r in rows)
print(f"\nAcurácia: {ok}/{n} = {ok/n:.0%}   subestimativas: {under}   superestimativas: {over}")
print("\nMatriz de confusão (linhas = esperado, colunas = obtido)")
print("{:<12}".format("") + "".join(f"{l:<12}" for l in LEVELS))
for e in LEVELS: print("{:<12}".format(e) + "".join(f"{conf[e][p]:<12}" for p in LEVELS))
