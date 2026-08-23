#!/usr/bin/env python3
"""compress.py — Compressão de contexto do MEGA BRAIN (v2.0).

Objetivo (brainstorm 1.3): reduzir tokens antes de enviar ao LLM, resumindo
daily notes / MOCs de forma incremental e determinística (sem IA obrigatória).
Mantém cabeçalhos, wikilinks e tags; colapsa linhas redundantes/vazias.

Uso:
  from compress import compress_text, estimate_tokens
  compress_text(daily_note_text, max_tokens=1500)
"""
import re

# Estimativa conservadora: ~4 chars por token (inglês/pt médio).
_CHARS_PER_TOKEN = 4


def estimate_tokens(text):
    """Estimativa de tokens (heurística de 4 chars/token)."""
    return max(1, len(text or "") // _CHARS_PER_TOKEN)


def _is_wikilink(line):
    return "[[" in line and "]]" in line


def _is_heading(line):
    return line.lstrip().startswith("#")


def _is_tag(line):
    s = line.strip()
    return s.startswith("tags:") or (s.startswith("- #") or " #" in s and s.startswith("-"))


def compress_text(text, max_tokens=2000, keep_links=True):
    """Comprime `text` mantendo estrutura relevante.

    Estratégia:
      - Mantém cabeçalhos (#), tags e wikilinks (contexto de grafo).
      - Remove linhas vazias consecutivas e linhas redundantes repetidas.
      - Se ainda exceder max_tokens, trunca preservando o início (cabeçalho MOC).
    Retorna dict {compressed, tokens_before, tokens_after, truncated}.
    """
    before = estimate_tokens(text)
    lines = (text or "").splitlines()
    seen = set()
    out = []
    blank_run = 0
    for line in lines:
        s = line.strip()
        if not s:
            blank_run += 1
            if blank_run <= 1:
                out.append("")
            continue
        blank_run = 0
        # descarta linhas repetidas (ruído de daily notes)
        key = s.lower()
        if key in seen and not _is_wikilink(line) and not _is_heading(line):
            continue
        seen.add(key)
        if keep_links or not _is_wikilink(line):
            out.append(line)
    compressed = "\n".join(out).strip() + "\n"

    truncated = False
    if estimate_tokens(compressed) > max_tokens:
        # trunca por linha preservando cabeçalhos
        budget = max_tokens * _CHARS_PER_TOKEN
        cut = []
        total = 0
        for line in compressed.splitlines():
            if total + len(line) + 1 > budget:
                truncated = True
                break
            cut.append(line)
            total += len(line) + 1
        compressed = "\n".join(cut).strip() + "\n[...truncado]"
        truncated = True

    return {
        "compressed": compressed,
        "tokens_before": before,
        "tokens_after": estimate_tokens(compressed),
        "truncated": truncated,
    }


def compress_note(vault, path, max_tokens=2000):
    """Lê a nota em `path` e retorna compress_text() aplicado."""
    import os
    rel = path.strip("/\\").replace("\\", "/").replace("/", os.sep)
    fp = os.path.join(vault, rel)
    if not os.path.exists(fp):
        return None
    with open(fp, encoding="utf-8", errors="ignore") as fh:
        return compress_text(fh.read(), max_tokens=max_tokens)
