#!/usr/bin/env python3
"""test_vault_skip_dirs.py — S24: VAULT_SKIP_DIRS exclui pastas nao-nota.

O repo MEGA BRAIN E o vault, entao varrer tests/, .git, node_modules, etc.
como se fossem notas de conteudo corrompe /suggest, /related, /graph e as
assinaturas de cache (ex.: llm_local.reason() sugeria tests/fixture/...md).

Este teste NAO e' tautologico: injetamos a regressao (esvaziar VAULT_SKIP_DIRS
em runtime) e confirmamos que ele passa a FALHAR — prova de que a exclusao
tem valor real, nao e' decorativa.
"""
import os
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS"))

import constants
import semantic
import graph


def _make_vault():
    v = tempfile.mkdtemp(prefix="skipdir_")
    # nota de conteudo
    os.makedirs(os.path.join(v, "10_MEGA_BRAIN"))
    open(os.path.join(v, "10_MEGA_BRAIN", "Nota.md"), "w", encoding="utf-8").write(
        "# Nota\nConteudo sobre parcelas.\n")
    # dirs que NUNCA sao notas
    os.makedirs(os.path.join(v, "tests", "fixture", "70_MOCS"))
    open(os.path.join(v, "tests", "fixture", "70_MOCS", "MOC_Teste.md"), "w",
         encoding="utf-8").write("# MOC Teste\n")
    os.makedirs(os.path.join(v, "node_modules", "x"))
    open(os.path.join(v, "node_modules", "x", "y.md"), "w", encoding="utf-8").write("# y\n")
    return v


def _check(vault):
    rels = [r for r, _ in semantic._vault_notes(vault, limit=constants.NOTE_LIMIT)]
    mtime, count = semantic._vault_mtime_signature(vault)
    g_mtime, g_count = graph._vault_signature(vault, limit=constants.NOTE_LIMIT)
    return rels, count, g_count


def main():
    fails = []
    v = _make_vault()
    try:
        rels, count, g_count = _check(v)
        # 1. nenhum path em tests/ ou node_modules/ deve aparecer
        bad = [r for r in rels if r.split("/", 1)[0] in ("tests", "node_modules")]
        if bad:
            fails.append("vault_notes incluiu dirs proibidos: %r" % bad)
        # 2. a nota de conteudo deve estar presente
        if "10_MEGA_BRAIN/Nota.md" not in rels:
            fails.append("nota de conteudo sumiu de _vault_notes: %r" % rels)
        # 3. contagem de semantic e de graph deve ser 1 (so' a nota de conteudo)
        if count != 1:
            fails.append("semantic._vault_mtime_signature count=%r (esperado 1)" % count)
        if g_count != 1:
            fails.append("graph._vault_signature count=%r (esperado 1)" % g_count)
        # 4. /suggest nao deve sugerir tests/ nem node_modules/
        sug = semantic.suggest(v, "parcelas", k=5)
        sug_bad = [s["path"] for s in sug if s["path"].split("/", 1)[0] in ("tests", "node_modules")]
        if sug_bad:
            fails.append("suggest sugeriu dir proibido: %r" % sug_bad)
    finally:
        shutil.rmtree(v, ignore_errors=True)

    # --- PROVA DE NAO-TAUTOLOGIA: esvaziar o skip set e re-rodar ---
    saved = set(constants.VAULT_SKIP_DIRS)
    constants.VAULT_SKIP_DIRS = set()
    semantic.VAULT_SKIP_DIRS = set()
    graph.VAULT_SKIP_DIRS = set()
    v2 = _make_vault()
    reg_failed = False
    try:
        rels2, _, g2 = _check(v2)
        bad2 = [r for r in rels2 if r.split("/", 1)[0] in ("tests", "node_modules")]
        if not bad2:
            # sem o skip, os dirs proibidos DEVERIAM reaparecer; se nao aparecerem,
            # o teste nao esta realmente testando o skip -> falha a prova.
            reg_failed = True
    finally:
        shutil.rmtree(v2, ignore_errors=True)
        constants.VAULT_SKIP_DIRS = saved
        semantic.VAULT_SKIP_DIRS = saved
        graph.VAULT_SKIP_DIRS = saved
    if reg_failed:
        fails.append("PROVA TAUTOLOGICA: esvaziar VAULT_SKIP_DIRS nao fez tests/ reaparecer "
                     "(teste nao cobre o skip de fato)")

    if fails:
        print("FAIL test_vault_skip_dirs:")
        for f in fails:
            print("  -", f)
        return 1
    print("OK test_vault_skip_dirs: VAULT_SKIP_DIRS exclui tests/ e node_modules/ de "
          "notes, suggest, graph e assinaturas de cache (prova anti-regressao OK)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
