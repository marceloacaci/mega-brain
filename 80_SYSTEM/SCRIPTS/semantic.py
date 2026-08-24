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


class VaultPathError(ValueError):
    """Path recebido tenta sair do vault (path traversal).

    Equivalente ao VaultPathError do mcp_obsidian_server.py, mas definido aqui
    para que semantic.py confine o `path` de related_notes SEM acoplamento
    circular (o server importa semantic, nao o contrario). Usado tambem como
    contrato de erro nas rotas /related do MCP (P16/S11).
    """


def _vault_rel(vault, path):
    """Resolve `path` DENTRO do vault; levanta VaultPathError se escapar.

    Sem isto, `_norm_rel('../../../x.md')` resolvia para fora do vault e
    related_notes/compress abriam arquivos arbitrarios (traversal de leitura).
    """
    base = os.path.abspath(vault)
    rel = (path or "").strip("/\\").replace("\\", "/")
    if not rel:
        raise VaultPathError("path vazio")
    fp = os.path.abspath(os.path.join(base, rel))
    if os.path.normcase(fp) != os.path.normcase(base) and \
            not os.path.normcase(fp).startswith(os.path.normcase(base) + os.sep):
        raise VaultPathError("path fora do vault")
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


def _vault_notes(vault, limit=600):
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


def related_notes(vault, path, k=5, limit=600):
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


def suggest(vault, query, k=5, limit=600):
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
