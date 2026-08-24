#!/usr/bin/env python3
"""test_note_limit_consistency.py — Regressao: teto de notas semantic==graph (S12).

O `semantic` (related_notes/suggest/_vault_notes) e o `graph` (build_graph/_iter_notes)
devem usar o MESMO teto de notas. Se divergirem, em vaults grandes o /graph inclui
notas que related_notes/suggest ignoram -> arestas semanticas inconsistentes (P11 flag).

Reverter qualquer default para 400 (ou outro valor != 600) faz o teste FALHAR.
"""

import os
import sys
import inspect

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS")))

import semantic  # noqa: E402
import graph  # noqa: E402

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


def _default(param_fn, name):
    sig = inspect.signature(param_fn)
    return sig.parameters[name].default


def main():
    print("=== Unidade: teto de notas semantic == graph ===")
    sem_ceiling = _default(semantic.related_notes, "limit")
    graph_ceiling = _default(graph.build_graph, "limit")
    check("related_notes limit == build_graph limit",
          sem_ceiling == graph_ceiling, f"sem={sem_ceiling} graph={graph_ceiling}")
    check("teto é 600 (coerente com vaults grandes)",
          sem_ceiling == 600, f"got={sem_ceiling}")
    check("suggest limit coerente",
          _default(semantic.suggest, "limit") == graph_ceiling,
          f"suggest={_default(semantic.suggest, 'limit')}")
    check("_vault_notes limit coerente",
          _default(semantic._vault_notes, "limit") == graph_ceiling,
          f"_vault_notes={_default(semantic._vault_notes, 'limit')}")
    print("\nRESULTADO: %d passaram, %d falharam" % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
