#!/usr/bin/env python3
"""vault_stats.py — Contagem de notas .md por pasta-raiz (uma unica varredura).

Centraliza a logica de varredura que era duplicada entre swarm._count_md e a
rota /stats do MCP. Manter um unico ponto evita drift (ex.: contagem divergente
entre o swarm e o endpoint de metricas).

Retorna (total_md, {pasta_raiz: n}) numa unica passada de os.walk.
"""
import os


def count_by_dir(vault):
    """Uma unica varredura: (total_md, {pasta_raiz: n}).

    Ignora .obsidian. A chave de by_dir e a pasta-raiz (1o nivel, ex.:
    10_MEGA_BRAIN); a raiz do vault vira '(raiz)'.
    """
    total = 0
    by_dir = {}
    for root, _, files in os.walk(vault):
        if ".obsidian" in root:
            continue
        md = [f for f in files if f.endswith(".md")]
        if not md:
            continue
        rel = os.path.relpath(root, vault).replace("\\", "/")
        top = rel.split("/")[0] if rel != "." else "(raiz)"
        by_dir[top] = by_dir.get(top, 0) + len(md)
        total += len(md)
    return total, by_dir
