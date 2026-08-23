#!/usr/bin/env python3
"""graph.py — Grafo de conhecimento do MEGA BRAIN (v2.0 / S10-B).

Objetivo: expor nos (notas) e arestas (relacionamento semantico + wikilinks)
como estrutura serializavel para o dashboard web. Sem dependencias externas.
"""
import os
import re

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


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


def _iter_notes(vault, limit=600):
    count = 0
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
            except Exception:
                continue
            rel = os.path.relpath(fp, vault).replace("\\", "/")
            yield rel, text
            count += 1
            if count >= limit:
                return


def build_graph(vault, k=3, limit=600):
    """Retorna {'nodes':[{id,label,type}], 'edges':[{source,target,weight}]}."""
    notes = {}
    for rel, text in _iter_notes(vault, limit):
        stem = os.path.basename(rel)[:-3]
        notes[rel] = {"stem": stem, "title": _title_of(text, stem),
                      "type": _folder_type(rel), "text": text}

    nodes = [{"id": rel, "label": n["title"], "type": n["type"]} for rel, n in notes.items()]

    edges = []
    seen = set()
    for rel, n in notes.items():
        # arestas explicitas via [[wikilink]]
        for lm in WIKILINK_RE.findall(n["text"]):
            target = lm.split("|")[0].split("/")[-1].strip().lower()
            trel = _match_rel(target, notes)
            if trel and trel != rel:
                key = (rel, trel)
                if key not in seen:
                    seen.add(key)
                    edges.append({"source": rel, "target": trel, "weight": 1.0, "kind": "wikilink"})
        # arestas semanticas (Jaccard) — import local p/ evitar ciclo
        try:
            from semantic import related_notes
            for r in related_notes(vault, rel, k=k):
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


def _match_rel(target_lower, notes):
    for rel, n in notes.items():
        if n["stem"].lower() == target_lower or n["title"].lower() == target_lower:
            return rel
    return None
