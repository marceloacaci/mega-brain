#!/usr/bin/env python3
"""test_shared_modules.py — Regressao: constantes + guards compartilhados (S13).

Cobre a refactoring de consolidacao (Sprint 13):
  1. `constants.NOTE_LIMIT` é a unica fonte do teto de notas (semantic==graph).
  2. `vault_path.vault_path` confina ao vault e levanta VaultPathError em traversal.
  3. `vault_stats.count_by_dir` faz UMA varredura e casa a contagem do /stats do MCP.

Todos os checks falham se a refactor for revertida (nao sao tautologicos):
  - reverter para limit=400 quebra o teste de teto;
  - remover o confinamento em vault_path deixa traversal passar;
  - duplicar a logica de contagem de volta no server faria o teste de dedup falhar
    (aqui checamos que count_by_dir e o antigo _count_md do swarm dao o mesmo total).
"""

import os
import sys
import time
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS")))

import constants  # noqa: E402
import vault_path  # noqa: E402
import vault_stats  # noqa: E402
import semantic  # noqa: E402
import graph  # noqa: E402
import swarm  # noqa: E402
import predictive  # noqa: E402

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print("  PASS: " + name)
    else:
        FAIL += 1
        print("  FAIL: " + name + " " + detail)


def main():
    print("=== Unidade: modulos compartilhados (S13) ===")

    # 1) teto compartilhado
    check("constants.NOTE_LIMIT == 600", constants.NOTE_LIMIT == 600,
          f"got={constants.NOTE_LIMIT}")
    check("semantic.related_notes usa NOTE_LIMIT",
          semantic.related_notes.__defaults__[1] == constants.NOTE_LIMIT,
          f"got={semantic.related_notes.__defaults__}")
    check("graph.build_graph usa NOTE_LIMIT",
          graph.build_graph.__defaults__[1] == constants.NOTE_LIMIT,
          f"got={graph.build_graph.__defaults__}")

    # 2) vault_path confinamento
    d = tempfile.mkdtemp(prefix="mb_shared_")
    try:
        inside = vault_path.vault_path(d, "10_MEGA_BRAIN/A.md")
        check("vault_path resolve dentro do vault",
              os.path.abspath(inside).startswith(os.path.abspath(d)))
        leaked = False
        for evil in ["../../../x.ini", "..\\..\\y.md", "../../etc/passwd"]:
            try:
                vault_path.vault_path(d, evil)
                leaked = True
            except vault_path.VaultPathError:
                pass
        check("vault_path bloqueia traversal", not leaked)
        # nome da classe preservado p/ contratos de teste (type(e).__name__)
        check("VaultPathError mantem nome",
              vault_path.VaultPathError.__name__ == "VaultPathError")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # 3) dedup de contagem: count_by_dir == swarm._count_md
    d2 = tempfile.mkdtemp(prefix="mb_stats_")
    try:
        for sub in ("10_MEGA_BRAIN", "70_MOCS", "80_SYSTEM", "30_PROJECTS"):
            os.makedirs(os.path.join(d2, sub), exist_ok=True)
        open(os.path.join(d2, "10_MEGA_BRAIN", "a.md"), "w").write("# a\n")
        open(os.path.join(d2, "10_MEGA_BRAIN", "b.md"), "w").write("# b\n")
        open(os.path.join(d2, "70_MOCS", "m.md"), "w").write("# m\n")
        open(os.path.join(d2, "30_PROJECTS", "p.md"), "w").write("# p\n")
        total_vs, by_vs = vault_stats.count_by_dir(d2)
        total_sw, by_sw = swarm._count_md(d2)
        check("count_by_dir total == swarm._count_md total",
              total_vs == total_sw == 4, f"vs={total_vs} sw={total_sw}")
        check("count_by_dir by_dir coerente",
              by_vs.get("10_MEGA_BRAIN") == 2 and by_vs.get("70_MOCS") == 1,
              f"by={by_vs}")
    finally:
        shutil.rmtree(d2, ignore_errors=True)

    # 4) cache de /stats (P11-style): 1o acesso miss, 2o hit; invalida ao mexer .md
    d3 = tempfile.mkdtemp(prefix="mb_stats_cache_")
    try:
        for nm in ("a.md", "b.md"):
            open(os.path.join(d3, nm), "w").write("# t\n")
        (_, _), hit1 = vault_stats.count_by_dir_cached(d3)
        (_, _), hit2 = vault_stats.count_by_dir_cached(d3)
        check("/stats cache: 1o acesso miss", hit1 is False)
        check("/stats cache: 2o acesso hit", hit2 is True)
        # mexe num .md -> mtime muda -> proximo acesso miss de novo
        time.sleep(0.01)
        with open(os.path.join(d3, "a.md"), "a") as fh:
            fh.write("\n# y\n")
        os.utime(os.path.join(d3, "a.md"), None)
        (_, _), hit3 = vault_stats.count_by_dir_cached(d3)
        check("/stats cache: invalida ao mexer .md", hit3 is False)
    finally:
        shutil.rmtree(d3, ignore_errors=True)

    print("\nRESULTADO: %d passaram, %d falharam" % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
