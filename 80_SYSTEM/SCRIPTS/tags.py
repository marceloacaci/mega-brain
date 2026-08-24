#!/usr/bin/env python3
"""tags.py — Contagem de tags do vault MEGA BRAIN (read-only, utilitário).

Extrai tags (frontmatter `tags:` e inline `#tag`) de todas as notas .md e
devolve a contagem por tag ordenada decrescente. Útil para o dashboard montar
uma nuvem de tags e para o usuário descobrir o vocabulário do segundo cérebro.

Reusa a varredura padrão (ignora .obsidian/.trash) e é uma função pura/testável.
Sem superfície de segurança (não aceita path do usuário).

Uso:
  from tags import tag_counts
  tag_counts(VAULT, limit=20)
  # -> [{"tag": "moc", "count": 12}, ...]
"""
import os
import re
import time
import threading

from constants import NOTE_LIMIT

# Tag inline tipo #tag (letras/dígitos/hífen/underline; sem pontuação solta).
_INLINE_TAG = re.compile(r"(?<![\w/])#([A-Za-z0-9_À-ÿ\-]+)")
# Bloco de tags do frontmatter: lines "  - tag" ou "tags: [a, b]".
_FM_TAG_LINE = re.compile(r"^\s*-\s+([A-Za-z0-9_À-ÿ\-]+)\s*$", re.MULTILINE)
_FM_TAGS_INLINE = re.compile(r"tags:\s*\[([^\]]*)\]", re.IGNORECASE)


def _normalize(tag):
    t = tag.strip().lower()
    return t


def _vault_mtime_signature(vault):
    """Retorna (mtime_max, contagem) das notas .md — usado p/ invalidar cache.

    Invalida o cache de /tags quando qualquer .md muda.
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


def tag_counts(vault, limit=20, top_only=True):
    """Conta tags (frontmatter + inline) de todas as notas .md.

    Args:
        vault: caminho do vault.
        limit: máximo de tags no resultado (limitado a NOTE_LIMIT).
        top_only: se True, ignora tags com contagem 1 (ruído de digitação).

    Returns:
        list[dict] ordenada por count descrescente: [{"tag": str, "count": int}].
    """
    limit = max(1, min(int(limit), NOTE_LIMIT))
    counts = {}
    for root, _, files in os.walk(vault):
        if ".obsidian" in root or ".trash" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            try:
                with open(fp, encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
            except OSError:
                continue
            found = set()
            # frontmatter tags (bloco ou inline)
            fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
            if fm:
                fm_block = fm.group(1)
                inline = _FM_TAGS_INLINE.search(fm_block)
                if inline:
                    for part in inline.group(1).split(","):
                        part = part.strip().lstrip("[").rstrip("]").strip()
                        if part:
                            found.add(_normalize(part))
                for m in _FM_TAG_LINE.finditer(fm_block):
                    found.add(_normalize(m.group(1)))
            # inline #tag no corpo
            for m in _INLINE_TAG.findall(text):
                found.add(_normalize(m))
            for t in found:
                counts[t] = counts.get(t, 0) + 1
    items = [{"tag": t, "count": c} for t, c in counts.items()
             if (not top_only) or c > 1]
    items.sort(key=lambda x: (-x["count"], x["tag"]))
    return items[:limit]


# Cache thread-safe (P11-style) p/ /tags: evita re-varrer o vault a cada poll
# do dashboard. Invalidado por assinatura de mtime do vault OU TTL.
_TAGS_CACHE = {"key": None, "mtime": 0.0, "data": None, "built_at": 0.0}
_TAGS_LOCK = threading.Lock()
_TAGS_DEFAULT_TTL = 60.0


def tag_counts_cached(vault, limit=20, top_only=True, ttl=_TAGS_DEFAULT_TTL):
    """Versão cacheada de tag_counts (invalida por mtime do vault ou TTL).

    Chave do cache: (limit, top_only). Retorna (lista, foi_cacheado). Thread-safe.
    """
    key = (int(limit), bool(top_only))
    with _TAGS_LOCK:
        cached = _TAGS_CACHE
        if cached["key"] == key and cached["data"] is not None:
            sig = _vault_mtime_signature(vault)
            if sig[0] == cached["mtime"] and (time.time() - cached["built_at"]) < ttl:
                return cached["data"], True
    data = tag_counts(vault, limit=limit, top_only=top_only)
    mtime, _ = _vault_mtime_signature(vault)
    with _TAGS_LOCK:
        _TAGS_CACHE["key"] = key
        _TAGS_CACHE["mtime"] = mtime
        _TAGS_CACHE["data"] = data
        _TAGS_CACHE["built_at"] = time.time()
    return data, False
