#!/usr/bin/env python3
"""validate_vault.py — Validacao continua do cofre MEGA BRAIN (M4 Extensibilidade).

Verifica (stdlib, sem dependencias):
  1. Estrutura obrigatoria: pastas 10_MEGA_BRAIN, 70_MOCS, 80_SYSTEM existem.
  2. Frontmatter: notas em 70_MOCS devem ter 'tipo: moc'; notas com frontmatter
     devem ter 'tags' (opcional, mas reportado se ausente).
  3. Links quebrados: [[WikiLink]] que nao apontam para nenhuma nota existente.
  4. Notas vazias (0 bytes).
Retorna dict {ok, problemas:[...], total_notas}.
"""
import os
import re

# Pastas que devem existir
REQUIRED_DIRS = ["10_MEGA_BRAIN", "70_MOCS", "80_SYSTEM"]
# Pastas ignoradas na varredura
IGNORE = {".obsidian", ".trash", ".git"}


def _all_md(root):
    out = []
    for cur, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE]
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.join(cur, f))
    return out


def _read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return ""


def _frontmatter(txt):
    if txt.startswith("---"):
        end = txt.find("---", 3)
        if end != -1:
            return txt[3:end]
    return None


def _note_names(root, notes=None):
    """Nomes (stem, lowercase) das notas. Aceita `notes` ja coletado para
    evitar um segundo os.walk do vault inteiro (era 2x I/O por /validate)."""
    if notes is None:
        notes = _all_md(root)
    return set(os.path.splitext(os.path.basename(p))[0].lower() for p in notes)


# Blocos de codigo/inline-code: wikilinks dentro deles sao exemplo/template,
# nao links reais (ex.: scripts do Excalidraw com `[[${app.metadataCache...}]]`).
_CODE_BLOCK_RE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]*`", re.DOTALL)


def _strip_code(txt):
    return _CODE_BLOCK_RE.sub("", txt)


def validate(vault):
    problems = []
    total = 0

    # 1. Estrutura
    for d in REQUIRED_DIRS:
        if not os.path.isdir(os.path.join(vault, d)):
            problems.append({"tipo": "estrutura", "msg": f"pasta ausente: {d}"})

    notes = _all_md(vault)
    total = len(notes)
    names = _note_names(vault, notes)  # reusa a varredura (sem 2o os.walk)

    for p in notes:
        rel = os.path.relpath(p, vault).replace("\\", "/")
        txt = _read(p)

        # 4. Vazia
        if len(txt.strip()) == 0:
            problems.append({"tipo": "nota_vazia", "path": rel, "msg": "nota com 0 bytes"})
            continue

        # 2. Frontmatter
        fm = _frontmatter(txt)
        if fm is not None and "tipo: moc" in fm.replace(" ", ""):
            if "tags:" not in fm.replace(" ", ""):
                problems.append({"tipo": "moc_sem_tags", "path": rel,
                                 "msg": "MOC sem 'tags' no frontmatter"})
        # 3. Links quebrados (apenas para notas com frontmatter valido ou corpo)
        vistos = set()
        for m in re.findall(r"\[\[([^\]]+)\]\]", _strip_code(txt)):
            # aceita [[pasta/Nota]] (Obsidian resolve pelo basename)
            target = m.split("|")[0].split("#")[0].strip().replace("\\", "/")
            target = target.rsplit("/", 1)[-1].strip().lower()
            # ignora placeholders de template (${...}, {{...}})
            if not target or "${" in m or "{{" in m:
                continue
            if target not in names and target not in vistos:
                vistos.add(target)
                problems.append({"tipo": "link_quebrado", "path": rel,
                                 "msg": f"[[{m}]] aponta para nota inexistente"})

    return {"ok": len(problems) == 0, "total_notas": total, "problemas": problems}


if __name__ == "__main__":
    import json
    import sys
    v = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    print(json.dumps(validate(v), ensure_ascii=False, indent=2))
