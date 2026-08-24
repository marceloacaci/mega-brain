#!/usr/bin/env python3
"""test_validate_links.py — Unidade: falsos positivos de link_quebrado (S11).

Cobre as regras adicionadas em `validate_vault.validate`:
  1. `[[pasta/Nota]]` resolve pelo basename (Obsidian faz isso) -> NAO e quebrado.
  2. Wikilink dentro de bloco de codigo (``` ou `inline`) e exemplo -> ignorado.
  3. Placeholder de template (`${...}` / `{{...}}`) -> ignorado.
  4. Link realmente inexistente -> AINDA e reportado (nao suprimimos demais).
  5. O mesmo alvo repetido na MESMA nota reporta 1x (dedupe), nao N vezes.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS")))
import validate_vault  # noqa: E402

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")


def build_vault():
    d = tempfile.mkdtemp(prefix="mb_vlinks_")
    for sub in ("10_MEGA_BRAIN", "70_MOCS", "80_SYSTEM", "30_PROJECTS"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    w = lambda rel, txt: open(os.path.join(d, rel.replace("/", os.sep)),
                              "w", encoding="utf-8").write(txt)
    w("30_PROJECTS/Alvo.md", "# Alvo\n\nnota real\n")
    w("10_MEGA_BRAIN/subpath.md", "# subpath\n\nlink [[30_PROJECTS/Alvo]] com pasta\n")
    w("10_MEGA_BRAIN/emcodigo.md",
      "# emcodigo\n\ninline `[[NaoExisteInline]]` e bloco:\n\n"
      "```\n[[NaoExisteBloco]]\n```\n")
    w("10_MEGA_BRAIN/template.md", "# template\n\n[[${app.metadata.foo}]] e [[{{titulo}}]]\n")
    w("10_MEGA_BRAIN/quebrado.md", "# quebrado\n\n[[FantasmaReal]] aqui\n")
    w("10_MEGA_BRAIN/repetido.md",
      "# repetido\n\n[[MesmoFantasma]] e [[MesmoFantasma]] e [[MesmoFantasma]]\n")
    return d


def main():
    print("=== Unidade: validate_vault links (S11) ===")
    d = build_vault()
    try:
        rep = validate_vault.validate(d)
        broken = [p for p in rep["problemas"] if p["tipo"] == "link_quebrado"]
        by_path = {}
        for p in broken:
            by_path.setdefault(p["path"], []).append(p["msg"])

        check("[[pasta/Nota]] nao e falso positivo",
              "10_MEGA_BRAIN/subpath.md" not in by_path, f"got={by_path}")
        check("wikilink em bloco/inline de codigo ignorado",
              "10_MEGA_BRAIN/emcodigo.md" not in by_path, f"got={by_path}")
        check("placeholder de template ignorado",
              "10_MEGA_BRAIN/template.md" not in by_path, f"got={by_path}")
        check("link realmente inexistente AINDA e reportado",
              len(by_path.get("10_MEGA_BRAIN/quebrado.md", [])) == 1,
              f"got={by_path.get('10_MEGA_BRAIN/quebrado.md')}")
        check("alvo repetido reporta 1x (dedupe)",
              len(by_path.get("10_MEGA_BRAIN/repetido.md", [])) == 1,
              f"got={by_path.get('10_MEGA_BRAIN/repetido.md')}")
        check("total_notas conta todas as notas", rep["total_notas"] == 6,
              f"got={rep['total_notas']}")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print(f"\nRESULTADO: {PASS} passaram, {FAIL} falharam")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
