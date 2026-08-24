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


import time
import threading

# Cache thread-safe (P11-style) p/ /stats: evita re-varrer o vault a cada poll
# do dashboard. Invalidado por assinatura de mtime do vault OU TTL.
_STATS_CACHE = {"mtime": 0.0, "data": None, "built_at": 0.0}
_STATS_LOCK = threading.Lock()
_STATS_DEFAULT_TTL = 60.0  # segundos


def _vault_mtime_signature(vault):
    """Retorna (mtime_max, contagem) das notas .md — usado p/ invalidar cache.

    Invalida o cache de /stats quando qualquer .md muda (mesmo critério dos
    caches de /recent e /tags).
    """
    newest = 0.0
    count = 0
    for root, _, files in os.walk(vault):
        if ".obsidian" in root or ".trash" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            try:
                m = os.path.getmtime(os.path.join(root, f))
            except OSError:
                continue
            if m > newest:
                newest = m
            count += 1
    return newest, count


def count_by_dir_cached(vault, ttl=_STATS_DEFAULT_TTL):
    """Versão cacheada de count_by_dir (invalida por mtime do vault ou TTL).

    Retorna ((total, by_dir), foi_cacheado). Thread-safe. Semântica idêntica a
    count_by_dir() quando há miss.
    """
    with _STATS_LOCK:
        cached = _STATS_CACHE
        if cached["data"] is not None:
            sig = _vault_mtime_signature(vault)
            if sig[0] == cached["mtime"] and (time.time() - cached["built_at"]) < ttl:
                return cached["data"], True
    data = count_by_dir(vault)
    mtime, _ = _vault_mtime_signature(vault)
    with _STATS_LOCK:
        _STATS_CACHE["mtime"] = mtime
        _STATS_CACHE["data"] = data
        _STATS_CACHE["built_at"] = time.time()
    return data, False
