#!/usr/bin/env python3
"""semantic.py — Correlação semântica do MEGA BRAIN (v2.0).

Objetivo (brainstorm 1.1/1.4): sugerir notas relacionadas via embeddings locais
(nomic-embed-text / Ollama) ou, na ausência, por sobreposição de palavras-chave
(Jaccard). Mantém o princípio do repo: SEM dependências obrigatórias; o fallback
heurístico sempre funciona.

Uso:
  from semantic import related_notes, suggest
  related_notes(VAULT, "30_PROJECTS/MeuBolso/README.md", k=5)
  suggest(VAULT, "como corrigir bug de parcela")
"""
import math
import os
import re
import threading
import time

from constants import NOTE_LIMIT
from vault_path import vault_path as _vault_path_impl, VaultPathError


# Re-export para manter o contrato de nome (test_security_v2 verifica
# `semantic.VaultPathError` e `semantic._norm_rel`).
def _vault_rel(vault, path):
    """Resolve `path` DENTRO do vault; levanta VaultPathError se escapar.

    Sem isto, `_norm_rel('../../../x.md')` resolvia para fora do vault e
    related_notes/compress abriam arquivos arbitrarios (traversal de leitura).
    """
    base = os.path.abspath(vault)
    rel = (path or "").strip("/\\").replace("\\", "/")
    if not rel:
        raise VaultPathError("path vazio")
    # Confinamento centralizado (vault_path.py): levanta VaultPathError se escapar.
    _vault_path_impl(base, rel)
    # retorna o rel normalizado em separadores nativos p/ reuso seguro
    return rel.replace("/", os.sep)


# ---------------------------------------------------------------------------
# Embeddings locais (Ollama / nomic-embed-text) — OPCIONAL.
# Só usa se OLLAMA_URL estiver setado e o endpoint responder. Caso contrário,
# todo o módulo opera no modo heurístico (Jaccard de tokens).
# ---------------------------------------------------------------------------
_OLLAMA_URL = os.environ.get("OLLAMA_URL", "").rstrip("/")


def _ollama_embed(text):
    """Retorna o vetor de embedding via Ollama, ou None se indisponível."""
    if not _OLLAMA_URL:
        return None
    try:
        import urllib.request
        import json
        req = urllib.request.Request(
            _OLLAMA_URL + "/api/embeddings",
            data=json.dumps({"model": "nomic-embed-text", "prompt": text}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode()).get("embedding")
    except Exception:
        return None


_TOKEN_RE = re.compile(r"[a-z0-9áàâãéèêíïóôõúüç]+", re.IGNORECASE)


def _tokens(text):
    return set(t.lower() for t in _TOKEN_RE.findall(text or ""))


def _cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def _vault_notes(vault, limit=NOTE_LIMIT):
    """Gera (rel_path, text) das notas .md (limit p/ performance)."""
    out = []
    for root, _, files in os.walk(vault):
        if ".obsidian" in root:
            continue
        for f in files:
            if f.endswith(".md"):
                fp = os.path.join(root, f)
                try:
                    with open(fp, encoding="utf-8", errors="ignore") as fh:
                        txt = fh.read()
                        out.append((os.path.relpath(fp, vault).replace("\\", "/"), txt))
                except Exception:
                    pass
                if len(out) >= limit:
                    return out
    return out


def _norm_rel(vault, path):
    """Junta vault + path normalizando separadores (cross-platform).

    Endurecido (P16/S11): confina ao vault e levanta VaultPathError em traversal.
    """
    rel = _vault_rel(vault, path)
    return os.path.join(os.path.abspath(vault), rel)


def related_notes(vault, path, k=5, limit=NOTE_LIMIT):
    """Notas mais relacionadas a `path` (cosseno de embeddings se Ollama, senão Jaccard).

    Levanta VaultPathError se `path` escapar do vault (P16/S11).
    """
    target = None
    notes = []
    target_fp = _norm_rel(vault, path)
    for rel, txt in _vault_notes(vault, limit):
        if os.path.join(vault, rel) == target_fp or rel == path.strip("/\\").replace("\\", "/").replace("/", os.sep):
            target = txt
        notes.append((rel, txt))
    if target is None:
        # tenta ler direto (ja confinado por _norm_rel)
        if os.path.exists(target_fp):
            with open(target_fp, encoding="utf-8", errors="ignore") as fh:
                target = fh.read()
    if target is None:
        return []

    emb_target = _ollama_embed(target)
    scored = []
    for rel, txt in notes:
        if rel == path or os.path.relpath(os.path.join(vault, path), vault).replace("\\", "/") == rel:
            continue
        if emb_target is not None:
            emb = _ollama_embed(txt)
            score = _cosine(emb_target, emb) if emb else 0.0
        else:
            a, b = _tokens(target), _tokens(txt)
            score = len(a & b) / len(a | b) if (a | b) else 0.0
        if score > 0:
            scored.append((score, rel))
    scored.sort(reverse=True)
    return [{"path": rel, "score": round(score, 4)} for score, rel in scored[:k]]


def suggest(vault, query, k=5, limit=NOTE_LIMIT):
    """Sugere notas que melhor cobrem a `query` (mesma métrica de related_notes)."""
    q_tokens = _tokens(query)
    q_emb = _ollama_embed(query)
    scored = []
    for rel, txt in _vault_notes(vault, limit):
        if q_emb is not None:
            emb = _ollama_embed(txt)
            score = _cosine(q_emb, emb) if emb else 0.0
        else:
            t = _tokens(txt)
            score = len(q_tokens & t) / len(q_tokens | t) if (q_tokens | t) else 0.0
        if score > 0:
            scored.append((score, rel))
    scored.sort(reverse=True)
    return [{"path": rel, "score": round(score, 4)} for score, rel in scored[:k]]


# ---------------------------------------------------------------------------
# Cache thread-safe (P11-style) p/ /related e /suggest: evita re-varrer o
# vault INTEIRO a cada poll do dashboard. Invalidado por assinatura de mtime
# do vault OU TTL (padrao S14/S15). Reusa _vault_mtime_signature local p/ nao
# acoplar a outros modulos (cada modulo mantem o seu — ver tags.py).
# ---------------------------------------------------------------------------
def _vault_mtime_signature(vault):
    """Retorna (mtime_max, contagem) das notas .md — usado p/ invalidar cache."""
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


_RELATED_CACHE = {"key": None, "mtime": 0.0, "data": None, "built_at": 0.0}
_RELATED_LOCK = threading.Lock()
_RELATED_DEFAULT_TTL = 60.0


def related_cached(vault, path, k=5, limit=NOTE_LIMIT, ttl=_RELATED_DEFAULT_TTL):
    """Versão cacheada de related_notes (invalida por mtime do vault ou TTL).

    Chave do cache: (path, k, limit). Retorna (lista, foi_cacheado). Thread-safe.
    """
    key = (path, int(k), int(limit))
    with _RELATED_LOCK:
        cached = _RELATED_CACHE
        if cached["key"] == key and cached["data"] is not None:
            sig = _vault_mtime_signature(vault)
            if sig[0] == cached["mtime"] and (time.time() - cached["built_at"]) < ttl:
                return cached["data"], True
    data = related_notes(vault, path, k=k, limit=limit)
    mtime, _ = _vault_mtime_signature(vault)
    with _RELATED_LOCK:
        _RELATED_CACHE["key"] = key
        _RELATED_CACHE["mtime"] = mtime
        _RELATED_CACHE["data"] = data
        _RELATED_CACHE["built_at"] = time.time()
    return data, False


_SUGGEST_CACHE = {"key": None, "mtime": 0.0, "data": None, "built_at": 0.0}
_SUGGEST_LOCK = threading.Lock()
_SUGGEST_DEFAULT_TTL = 60.0


def suggest_cached(vault, query, k=5, limit=NOTE_LIMIT, ttl=_SUGGEST_DEFAULT_TTL):
    """Versão cacheada de suggest (invalida por mtime do vault ou TTL).

    Chave do cache: (query, k, limit). Retorna (lista, foi_cacheado). Thread-safe.
    """
    key = (query, int(k), int(limit))
    with _SUGGEST_LOCK:
        cached = _SUGGEST_CACHE
        if cached["key"] == key and cached["data"] is not None:
            sig = _vault_mtime_signature(vault)
            if sig[0] == cached["mtime"] and (time.time() - cached["built_at"]) < ttl:
                return cached["data"], True
    data = suggest(vault, query, k=k, limit=limit)
    mtime, _ = _vault_mtime_signature(vault)
    with _SUGGEST_LOCK:
        _SUGGEST_CACHE["key"] = key
        _SUGGEST_CACHE["mtime"] = mtime
        _SUGGEST_CACHE["data"] = data
        _SUGGEST_CACHE["built_at"] = time.time()
    return data, False
