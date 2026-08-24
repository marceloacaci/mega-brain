#!/usr/bin/env python3
"""
MEGA BRAIN — Modo preditivo + correlação leve (stdlib, sem dependências).

Usado pelo pre_task_hook para sugerir, ANTES da tarefa, o arquivo mais
relevante do projeto e notas correlacionadas em outros projetos.

Heurística (S3-1, preditivo):
  - Entre as notas de 30_PROJECTS/<proj>/, a "mais relevante" é a que tem
    mais wikilinks ([[...]]) — indica nota-hub do projeto.

Correlação (S3-2, leve):
  - Encontra notas fora do projeto que compartilham >= N palavras-chave
    (tokens de 4+ letras) com a nota sugerida.

Uso:
  python predictive.py suggest --project MeuBolso
  python predictive.py correlate --note "30_PROJECTS/MeuBolso/README.md"
  (ambos imprimem JSON; exit 0 sempre — falha-segura)
"""
import argparse
import json
import os
import re
import sys

# VAULT resolvido de forma portátil: prefere a env MEGABRAIN_VAULT; senão o diretório
# pai do repo (este script vive em 80_SYSTEM/SCRIPTS, o vault é o repo raiz). Não usa
# caminho hardcoded (anti-padrão P3/P5 — quebrava no runner Linux do CI).
VAULT = os.environ.get("MEGABRAIN_VAULT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
WORD = re.compile(r"[a-zA-ZÀ-ÿ]{4,}")


class VaultPathError(ValueError):
    """Path recebido tenta sair do vault (path traversal)."""


def _vault_path(rel):
    """Resolve `rel` DENTRO do vault; levanta VaultPathError se escapar (P16/S11)."""
    base = os.path.abspath(VAULT)
    fp = os.path.abspath(os.path.join(base, (rel or "").strip("/\\").replace("\\", "/")))
    if os.path.normcase(fp) != os.path.normcase(base) and \
            not os.path.normcase(fp).startswith(os.path.normcase(base) + os.sep):
        raise VaultPathError("path fora do vault")
    return fp


def _notes():
    out = []
    for root, _, files in os.walk(VAULT):
        if ".obsidian" in root:
            continue
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.join(root, f))
    return out


def _rel(p):
    return os.path.relpath(p, VAULT).replace("\\", "/")


def _wiki_count(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return len(WIKILINK.findall(fh.read()))
    except Exception:
        return 0


def suggest(project):
    """Retorna a nota-hub do projeto (mais wikilinks)."""
    try:
        proj_dir = _vault_path(os.path.join("30_PROJECTS", project))
    except VaultPathError:
        return {"project": project, "suggested": None, "reason": "projeto fora do vault"}
    if not os.path.isdir(proj_dir):
        return {"project": project, "suggested": None, "reason": "projeto inexistente"}
    candidatos = [os.path.join(proj_dir, f) for f in os.listdir(proj_dir) if f.endswith(".md")]
    if not candidatos:
        return {"project": project, "suggested": None, "reason": "sem notas"}
    melhor = max(candidatos, key=_wiki_count)
    return {
        "project": project,
        "suggested": _rel(melhor),
        "wikilinks": _wiki_count(melhor),
        "reason": "nota com mais wikilinks no projeto",
    }


def correlate(note_rel):
    """Notas fora do projeto que compartilham palavras-chave com a nota dada."""
    try:
        target = _vault_path(note_rel)
    except VaultPathError:
        return {"note": note_rel, "related": [], "reason": "nota fora do vault"}
    if not os.path.exists(target):
        return {"note": note_rel, "related": [], "reason": "nota inexistente"}
    try:
        with open(target, encoding="utf-8", errors="ignore") as fh:
            words = set(w.lower() for w in WORD.findall(fh.read()))
    except Exception:
        return {"note": note_rel, "related": [], "reason": "erro leitura"}
    if not words:
        return {"note": note_rel, "related": [], "reason": "sem palavras-chave"}

    related = []
    for n in _notes():
        if os.path.abspath(n) == os.path.abspath(target):
            continue
        try:
            with open(n, encoding="utf-8", errors="ignore") as fh:
                nwords = set(w.lower() for w in WORD.findall(fh.read()))
        except Exception:
            continue
        shared = words & nwords
        if len(shared) >= 3:
            related.append({"note": _rel(n), "shared": len(shared)})
    related.sort(key=lambda x: x["shared"], reverse=True)
    return {"note": note_rel, "related": related[:5], "reason": ">=3 palavras-chave em comum"}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    ps = sub.add_parser("suggest"); ps.add_argument("--project", required=True)
    pc = sub.add_parser("correlate"); pc.add_argument("--note", required=True)
    args = ap.parse_args()

    try:
        if args.cmd == "suggest":
            print(json.dumps(suggest(args.project), ensure_ascii=False))
        elif args.cmd == "correlate":
            print(json.dumps(correlate(args.note), ensure_ascii=False))
        else:
            print(json.dumps({"error": "use suggest ou correlate"}, ensure_ascii=False))
    except Exception as e:
        # falha-segura: nunca quebra o caller
        print(json.dumps({"error": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
