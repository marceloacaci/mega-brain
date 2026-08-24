#!/usr/bin/env python3
"""recent.py — Notas modificadas mais recentemente no MEGA BRAIN.

Endpoint utilitário (somente-leitura, sem superfície de segurança): lista as
notas .md mais recentes do vault ordenadas por mtime decrescente. Útil para o
dashboard mostrar "o que mudou por último" num segundo cérebro.

Reusa a mesma lógica de varredura e o mapeamento de tipo do graph.py, mas é
uma função pura e testável isoladamente (sem subir o MCP).

Uso:
  from recent import recent_notes
  recent_notes(VAULT, limit=10)
  # -> [{"path": "10_MEGA_BRAIN/X.md", "mtime": 169..., "age_days": 1.2, "type": "core"}]
"""
import os
import time
import threading

from constants import NOTE_LIMIT

# Mapeamento de pasta-raiz -> tipo (espelha graph._folder_type, mantido aqui
# para nao acoplar recent ao grafo inteiro).
_FOLDER_TYPE = {
    "10_MEGA_BRAIN": "core",
    "70_MOCS": "moc",
    "30_PROJECTS": "project",
    "20_DAILY_NOTES": "daily",
    "40_AREAS": "area",
    "50_RESOURCES": "resource",
    "60_ARCHIVE": "archive",
    "80_SYSTEM": "system",
    "90_ALERTS": "alert",
    "docs": "doc",
}


def _folder_type(rel):
    top = rel.split("/", 1)[0]
    return _FOLDER_TYPE.get(top, "note")


def _vault_mtime_signature(vault):
    """Retorna (mtime_max, contagem) das notas .md — usado p/ invalidar cache.

    Equivalente a graph._vault_signature mas independente (recent.py nao importa
    graph). Invalida o cache de /recent quando qualquer .md muda.
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


# Cache thread-safe (P11-style) p/ /recent: evita re-varrer o vault a cada
# poll do dashboard. Invalidado por assinatura de mtime OU TTL.
_RECENT_CACHE = {"key": None, "mtime": 0.0, "data": None, "built_at": 0.0}
_RECENT_LOCK = threading.Lock()
_RECENT_DEFAULT_TTL = 60.0  # segundos


def recent_notes_cached(vault, limit=10, cutoff_days=None, ttl=_RECENT_DEFAULT_TTL):
    """Versão cacheada de recent_notes (invalida por mtime do vault ou TTL).

    A chave do cache inclui (limit, cutoff_days); retorna (lista, foi_cacheado).
    Thread-safe. Semântica idêntica a recent_notes() quando há miss.
    """
    key = (int(limit), cutoff_days)
    with _RECENT_LOCK:
        cached = _RECENT_CACHE
        if cached["key"] == key and cached["data"] is not None:
            sig = _vault_mtime_signature(vault)
            if sig[0] == cached["mtime"] and (time.time() - cached["built_at"]) < ttl:
                return cached["data"], True
    data = recent_notes(vault, limit=limit, cutoff_days=cutoff_days)
    mtime, _ = _vault_mtime_signature(vault)
    with _RECENT_LOCK:
        _RECENT_CACHE["key"] = key
        _RECENT_CACHE["mtime"] = mtime
        _RECENT_CACHE["data"] = data
        _RECENT_CACHE["built_at"] = time.time()
    return data, False


def recent_notes(vault, limit=10, cutoff_days=None):
    """Lista até `limit` notas .md mais recentes (mtime descrescente).

    Args:
        vault: caminho do vault.
        limit: máximo de itens (limitado a NOTE_LIMIT p/ evitar varredura enorme).
        cutoff_days: se dado, ignora notas mais antigas que N dias (None = todas).

    Returns:
        list[dict] com path, mtime (epoch float), age_days (float), type (str).
        Ordenado por mtime descrescente; estável em empate (path asc).
    """
    limit = max(1, min(int(limit), NOTE_LIMIT))
    now = time.time()
    rows = []
    for root, _, files in os.walk(vault):
        if ".obsidian" in root or ".trash" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            try:
                m = os.path.getmtime(fp)
            except OSError:
                continue
            age = (now - m) / 86400.0
            if cutoff_days is not None and age > cutoff_days:
                continue
            rel = os.path.relpath(fp, vault).replace("\\", "/")
            rows.append({"path": rel, "mtime": m,
                         "age_days": round(age, 3), "type": _folder_type(rel)})
    rows.sort(key=lambda r: (-r["mtime"], r["path"]))
    return rows[:limit]
