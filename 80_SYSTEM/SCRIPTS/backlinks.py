#!/usr/bin/env python3
"""backlinks.py — Backlinks de uma nota do MEGA BRAIN (read-only).

Responde "quem aponta para esta nota?" — a pergunta mais usada de um segundo
cerebro depois da busca. O Obsidian mostra isso na UI, mas o MCP/dashboard nao
tinha o dado exposto; o /graph traz o grafo INTEIRO (caro) quando o usuario so
quer a vizinhanca de entrada de UMA nota.

Resolucao de wikilink segue a mesma regra do graph.py (P16.3): compara por
`stem` (nome do arquivo sem .md) e por titulo (primeiro `# H1` ou stem),
ignorando alias (`[[Nota|alias]]`), heading (`[[Nota#secao]]`) e blocos de
codigo (para nao contar EXEMPLOS de documentacao como link real).

Seguranca: `path` vem do usuario -> confinado via vault_path (VaultPathError).

Uso:
  from backlinks import backlinks
  backlinks(VAULT, "10_MEGA_BRAIN/X.md")
  # -> {"path": "10_MEGA_BRAIN/X.md", "total": 2,
  #     "backlinks": [{"path": "70_MOCS/M.md", "title": "M", "count": 1}, ...]}
"""
import os
import re
import time
import threading

from constants import NOTE_LIMIT
from vault_path import vault_path, VaultPathError

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _strip_code(text):
    """Remove blocos ``` e `inline` — wikilinks ali sao exemplos, nao links."""
    text = _FENCE_RE.sub("", text)
    return _INLINE_CODE_RE.sub("", text)


def _title_of(text, stem):
    for line in text.splitlines()[:20]:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip() or stem
    return stem


def _link_target(raw):
    """Normaliza o alvo de um wikilink: tira alias, heading, extensao e pasta."""
    t = raw.split("|", 1)[0].split("#", 1)[0].strip()
    t = t.replace("\\", "/").strip("/")
    if t.lower().endswith(".md"):
        t = t[:-3]
    if "/" in t:
        t = t.rsplit("/", 1)[1]
    return t.lower()


def _iter_notes(vault, limit=NOTE_LIMIT):
    """Itera (rel, stem, text) das notas .md do vault (ignora .obsidian/.trash)."""
    n = 0
    for root, _, files in os.walk(vault):
        if ".obsidian" in root or ".trash" in root:
            continue
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            if n >= limit:
                return
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, vault).replace("\\", "/")
            try:
                with open(fp, encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
            except OSError:
                continue
            n += 1
            yield rel, f[:-3], text


def backlinks(vault, path, limit=NOTE_LIMIT):
    """Lista as notas que apontam para `path` via wikilink.

    Args:
        vault: caminho do vault.
        path: caminho relativo da nota alvo (ex. "10_MEGA_BRAIN/X.md").
        limit: teto de notas varridas (default NOTE_LIMIT).

    Returns:
        dict com "path" (rel normalizado), "total" e "backlinks" (lista de
        {"path","title","count"} ordenada por count desc, depois path asc).

    Raises:
        VaultPathError: se `path` tentar sair do vault.
        FileNotFoundError: se a nota alvo nao existir.
    """
    fp = vault_path(vault, path)  # confina (levanta VaultPathError)
    if not os.path.isfile(fp):
        raise FileNotFoundError(path)
    rel_target = os.path.relpath(fp, os.path.abspath(vault)).replace("\\", "/")
    stem = os.path.basename(rel_target)[:-3]
    try:
        with open(fp, encoding="utf-8", errors="ignore") as fh:
            target_title = _title_of(fh.read(), stem)
    except OSError:
        target_title = stem
    names = {stem.lower(), target_title.lower()}

    out = []
    for rel, src_stem, text in _iter_notes(vault, limit=limit):
        if rel == rel_target:
            continue  # nao conta auto-link
        body = _strip_code(text)
        count = 0
        for raw in WIKILINK_RE.findall(body):
            if "${" in raw or "{{" in raw:
                continue  # placeholder de template (Excalidraw etc.) — P16.3
            if _link_target(raw) in names:
                count += 1
        if count:
            out.append({"path": rel, "title": _title_of(text, src_stem),
                        "count": count})
    out.sort(key=lambda x: (-x["count"], x["path"]))
    return {"path": rel_target, "title": target_title,
            "total": len(out), "backlinks": out}


# ---------------------------------------------------------------------------
# Cache thread-safe (padrao P11/S14/S15): invalida por assinatura de mtime
# do vault OU por TTL. Chave inclui o path alvo.
# ---------------------------------------------------------------------------
_BL_CACHE = {}
_BL_LOCK = threading.Lock()
_BL_DEFAULT_TTL = 60.0
_BL_MAX_ENTRIES = 64


def _vault_mtime_signature(vault):
    """Retorna (mtime_max, contagem) das notas .md — invalida o cache."""
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


def backlinks_cached(vault, path, limit=NOTE_LIMIT, ttl=_BL_DEFAULT_TTL):
    """Versao cacheada de backlinks(). Retorna (dict, foi_cacheado).

    Erros (VaultPathError/FileNotFoundError) NAO sao cacheados — propagam.
    """
    key = (os.path.abspath(vault), (path or "").replace("\\", "/").strip("/"),
           int(limit))
    with _BL_LOCK:
        entry = _BL_CACHE.get(key)
        if entry:
            sig = _vault_mtime_signature(vault)
            if sig[0] == entry["mtime"] and (time.time() - entry["built_at"]) < ttl:
                return entry["data"], True
    data = backlinks(vault, path, limit=limit)
    mtime, _ = _vault_mtime_signature(vault)
    with _BL_LOCK:
        if len(_BL_CACHE) >= _BL_MAX_ENTRIES:
            _BL_CACHE.clear()  # politica simples: evita crescimento ilimitado
        _BL_CACHE[key] = {"mtime": mtime, "data": data, "built_at": time.time()}
    return data, False


# ---------------------------------------------------------------------------
# S17-B: orfas de ENTRADA — notas que ninguem linka.
# IMPORTANTE: implementado em UMA passada O(n) (indice de nomes + contagem de
# links por alvo). Chamar backlinks() por nota seria O(n^2) de I/O — o mesmo
# defeito que fez /graph levar 60s no vault real (P16.2).
# ---------------------------------------------------------------------------
def orphans_in(vault, limit=NOTE_LIMIT):
    """Lista as notas que NAO recebem nenhum wikilink (orfas de entrada).

    Diferente das "notas orfas" do dashboard (grau 0 no /graph, que considera
    tambem arestas semanticas e links de SAIDA): aqui e' estritamente
    "ninguem aponta para ela" — o sinal de que a nota esta invisivel no vault.

    Returns:
        dict: {"total_notas", "total_orfas", "orphans":[{"path","title"}]}
    """
    notes = list(_iter_notes(vault, limit=limit))
    # nome (stem/titulo, lower) -> rel  |  e rel -> titulo
    lookup = {}
    titles = {}
    for rel, stem, text in notes:
        t = _title_of(text, stem)
        titles[rel] = t
        lookup.setdefault(stem.lower(), rel)
        lookup.setdefault(t.lower(), rel)
    linked = set()
    for rel, _stem, text in notes:
        body = _strip_code(text)
        for raw in WIKILINK_RE.findall(body):
            if "${" in raw or "{{" in raw:
                continue
            trel = lookup.get(_link_target(raw))
            if trel and trel != rel:  # auto-link nao salva a nota
                linked.add(trel)
    orph = [{"path": rel, "title": titles[rel]}
            for rel, _s, _t in notes if rel not in linked]
    orph.sort(key=lambda x: x["path"])
    return {"total_notas": len(notes), "total_orfas": len(orph),
            "orphans": orph}


_ORPH_CACHE = {"key": None, "mtime": 0.0, "data": None, "built_at": 0.0}
_ORPH_LOCK = threading.Lock()


def orphans_in_cached(vault, limit=NOTE_LIMIT, ttl=_BL_DEFAULT_TTL):
    """Versao cacheada de orphans_in(). Retorna (dict, foi_cacheado)."""
    key = (os.path.abspath(vault), int(limit))
    with _ORPH_LOCK:
        c = _ORPH_CACHE
        if c["key"] == key and c["data"] is not None:
            sig = _vault_mtime_signature(vault)
            if sig[0] == c["mtime"] and (time.time() - c["built_at"]) < ttl:
                return c["data"], True
    data = orphans_in(vault, limit=limit)
    mtime, _ = _vault_mtime_signature(vault)
    with _ORPH_LOCK:
        _ORPH_CACHE.update({"key": key, "mtime": mtime, "data": data,
                            "built_at": time.time()})
    return data, False
