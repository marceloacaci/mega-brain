#!/usr/bin/env python3
"""graph.py — Grafo de conhecimento do MEGA BRAIN (v2.0 / S10-B).

Objetivo: expor nos (notas) e arestas (relacionamento semantico + wikilinks)
como estrutura serializavel para o dashboard web. Sem dependencias externas.
"""
import os
import re
import time
import threading

from constants import NOTE_LIMIT, VAULT_SKIP_DIRS

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# ---------------------------------------------------------------------------
# Cache de grafo por mtime (P11): build_graph e O(n^2) em Jaccard. Para evitar
# recomputar o grafo a cada /graph (caro em vaults grandes), cacheamos o
# resultado e invalidamos por mtime + contagem de notas do vault.
# ---------------------------------------------------------------------------
_GRAPH_CACHE = {"key": None, "mtime": 0.0, "count": -1, "built_at": 0.0, "data": None}
_GRAPH_LOCK = threading.Lock()


def _vault_signature(vault, limit=NOTE_LIMIT):
    """Retorna (mtime_max, contagem) das notas .md — usado p/ invalidar cache.

    Ignora VAULT_SKIP_DIRS (tests/, .git, etc.) — o repo MEGA BRAIN E o vault.
    """
    newest = 0.0
    count = 0
    for root, dirs, files in os.walk(vault):
        parts = set(os.path.basename(root).split(os.sep))
        if parts & VAULT_SKIP_DIRS:
            dirs[:] = []
            continue
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
            if count >= limit:
                return newest, count
    return newest, count


def _title_of(text, stem):
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # tenta 'tipo:' no frontmatter
    fm = FRONTMATTER_RE.match(text)
    if fm:
        tm = re.search(r"^tipo:\s*(.+)$", fm.group(1), re.MULTILINE)
        if tm:
            return tm.group(1).strip()
    return stem


def _folder_type(rel):
    top = rel.split("/", 1)[0]
    mapping = {
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
    return mapping.get(top, "note")


def _iter_notes(vault, limit=NOTE_LIMIT):
    """Itera (rel_path, text) das notas .md. Ignora VAULT_SKIP_DIRS."""
    count = 0
    for root, dirs, files in os.walk(vault):
        parts = set(os.path.basename(root).split(os.sep))
        if parts & VAULT_SKIP_DIRS:
            dirs[:] = []
            continue
        if ".obsidian" in root or ".trash" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            try:
                with open(fp, encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
            except Exception:
                continue
            rel = os.path.relpath(fp, vault).replace("\\", "/")
            yield rel, text
            count += 1
            if count >= limit:
                return


def build_graph(vault, k=3, limit=NOTE_LIMIT):
    """Retorna {'nodes':[{id,label,type}], 'edges':[{source,target,weight}]}."""
    notes = {}
    for rel, text in _iter_notes(vault, limit):
        stem = os.path.basename(rel)[:-3]
        notes[rel] = {"stem": stem, "title": _title_of(text, stem),
                      "type": _folder_type(rel), "text": text}

    nodes = [{"id": rel, "label": n["title"], "type": n["type"]} for rel, n in notes.items()]

    # indice de lookup p/ wikilinks: evita _match_rel O(n) por link (O(n*m) total)
    lookup = {}
    for rel, n in notes.items():
        lookup.setdefault(n["stem"].lower(), rel)
        lookup.setdefault(n["title"].lower(), rel)

    # tokens/embeddings pre-computados UMA vez por nota (antes: related_notes
    # re-lia e re-tokenizava o vault inteiro para CADA nota -> O(n^2) de I/O em
    # disco, tanto no caminho Jaccard quanto no de embeddings/Ollama).
    use_embeddings = bool(os.environ.get("OLLAMA_URL", "").strip())
    tokens = {}
    embeds = {}
    if use_embeddings:
        try:
            from semantic import _ollama_embed
            for rel, n in notes.items():
                embeds[rel] = _ollama_embed(n["text"])
        except Exception:
            embeds = {}
            use_embeddings = False
    if not use_embeddings:
        try:
            from semantic import _tokens as _sem_tokens
        except Exception:
            _sem_tokens = None
        if _sem_tokens is not None:
            for rel, n in notes.items():
                tokens[rel] = _sem_tokens(n["text"])

    edges = []
    seen = set()
    for rel, n in notes.items():
        # arestas explicitas via [[wikilink]]
        for lm in WIKILINK_RE.findall(n["text"]):
            target = lm.split("|")[0].split("/")[-1].strip().lower()
            trel = lookup.get(target)
            if trel and trel != rel:
                key = (rel, trel)
                if key not in seen:
                    seen.add(key)
                    edges.append({"source": rel, "target": trel, "weight": 1.0, "kind": "wikilink"})
        # arestas semanticas (pre-computadas: embeddings OU Jaccard em tokens)
        try:
            if use_embeddings and embeds:
                from semantic import _cosine
                tgt = embeds.get(rel)
                if tgt is not None:
                    scored = []
                    for orel, e in embeds.items():
                        if orel == rel or e is None:
                            continue
                        sc = _cosine(tgt, e)
                        if sc > 0:
                            scored.append((sc, orel))
                    scored.sort(reverse=True)
                    rel_out = [{"path": orel, "score": round(s, 4)} for s, orel in scored[:k]]
                else:
                    rel_out = []
            elif tokens:
                a = tokens.get(rel) or set()
                scored = []
                for orel, b in tokens.items():
                    if orel == rel or not (a or b):
                        continue
                    union = len(a | b)
                    if not union:
                        continue
                    score = len(a & b) / union
                    if score > 0:
                        scored.append((score, orel))
                scored.sort(reverse=True)
                rel_out = [{"path": orel, "score": round(s, 4)} for s, orel in scored[:k]]
            else:
                rel_out = []
            for r in rel_out:
                trel = r["path"]
                if trel == rel:
                    continue
                key = tuple(sorted((rel, trel)))
                if key in seen:
                    continue
                seen.add(key)
                edges.append({"source": rel, "target": trel, "weight": round(r["score"], 4), "kind": "semantic"})
        except Exception:
            pass
    return {"nodes": nodes, "edges": edges}


def build_graph_cached(vault, k=3, limit=NOTE_LIMIT, ttl=300):
    """Versão cacheada de build_graph (P11): evita O(n^2) repetido no /graph.

    O cache e invalidado por assinatura do vault (mtime maximo + contagem de
    notas) OU por TTL. O parametro `k`/`limit` faz parte da chave, entao
    /graph?k=5 e /graph?k=3 geram caches distintos. Thread-safe.
    Retorna (data, was_cached).
    """
    key = (k, limit)
    with _GRAPH_LOCK:
        cached = _GRAPH_CACHE
        if (cached["key"] == key and cached["data"] is not None
                and time.time() - cached["built_at"] < ttl):
            sig = _vault_signature(vault, limit)
            if sig[0] == cached["mtime"] and sig[1] == cached["count"]:
                return cached["data"], True
    # cache miss / invalidado -> recomputa
    data = build_graph(vault, k=k, limit=limit)
    mtime, count = _vault_signature(vault, limit)
    with _GRAPH_LOCK:
        _GRAPH_CACHE["key"] = key
        _GRAPH_CACHE["mtime"] = mtime
        _GRAPH_CACHE["count"] = count
        _GRAPH_CACHE["built_at"] = time.time()
        _GRAPH_CACHE["data"] = data
    return data, False
