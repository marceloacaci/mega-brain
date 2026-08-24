#!/usr/bin/env python3
"""activity.py — Heatmap de atividade do MEGA BRAIN (contagem de notas diárias).

Conta as notas diárias (20_DAILY_NOTES) por data, alimentando o heatmap do
dashboard. Função pura e testável; o servidor a consome via activity_cached().

Reusa o padrão P11-style de cache por assinatura de mtime do vault OU TTL
(igual a recent/tags/backlinks). Independente de outros módulos: traz a sua
própria _vault_mtime_signature().

Uso:
  from activity import activity_counts, activity_cached
  activity_counts(VAULT)  # -> (daily_dir, {"YYYY-MM-DD": n, ...})
  activity_cached(VAULT)  # -> ((daily_dir, by_date), foi_cacheado)
"""
import os
import re
import time
import threading
from constants import prune_vault_dirs

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _daily_dir(vault):
    """Retorna o caminho do diretório de notas diárias ou None se ausente."""
    for d in os.listdir(vault):
        if d.upper().startswith("20_DAILY") or d.upper().startswith("20_DAILY_NOTES"):
            return os.path.join(vault, d)
    return None


def activity_counts(vault):
    """Conta notas diárias por data.

    Returns:
        tuple: (daily_dir_abs_ou_"(ausente)", {"YYYY-MM-DD": n, ...})
    """
    daily_dir = _daily_dir(vault)
    counts = {}
    if daily_dir and os.path.isdir(daily_dir):
        for f in os.listdir(daily_dir):
            m = _DATE_RE.match(f)
            if m:
                counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return (daily_dir or "(ausente)"), counts


def _vault_mtime_signature(vault):
    """Retorna (mtime_max, contagem) das notas .md — usado p/ invalidar cache."""
    newest = 0.0
    count = 0
    for root, dirs, files in os.walk(vault):
        prune_vault_dirs(dirs)
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


_ACT_CACHE = {"key": None, "mtime": 0.0, "data": None, "built_at": 0.0}
_ACT_LOCK = threading.Lock()
_ACT_DEFAULT_TTL = 60.0


def activity_cached(vault, ttl=_ACT_DEFAULT_TTL):
    """Versão cacheada de activity_counts (invalida por mtime do vault ou TTL).

    Retorna ((daily_dir, by_date), foi_cacheado). Chave única (sem parâmetros de
    consulta); thread-safe.
    """
    key = "activity"
    with _ACT_LOCK:
        cached = _ACT_CACHE
        if cached["key"] == key and cached["data"] is not None:
            sig = _vault_mtime_signature(vault)
            if sig[0] == cached["mtime"] and (time.time() - cached["built_at"]) < ttl:
                return cached["data"], True
    data = activity_counts(vault)
    mtime, _ = _vault_mtime_signature(vault)
    with _ACT_LOCK:
        _ACT_CACHE["key"] = key
        _ACT_CACHE["mtime"] = mtime
        _ACT_CACHE["data"] = data
        _ACT_CACHE["built_at"] = time.time()
    return data, False
