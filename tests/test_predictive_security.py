#!/usr/bin/env python3
"""test_predictive_security.py — Regressao: predictive.py confina ao vault (S12).

`predictive.correlate(note_rel)` e `predictive.suggest(project)` juntavam o argumento
ao VAULT SEM confinamento -> path traversal (correlate('../../etc/passwd') abria
arquivo de fora). Agora usam `_vault_path` (VaultPathError). Reverter a confinacao
faz o teste FALHAR.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS")))

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
    print("=== Unidade: predictive.py confinamento de path (S12) ===")
    # 1) correlate com traversal deve ser bloqueado (sem ler arquivo externo)
    r = predictive.correlate("../../Windows/win.ini")
    check("correlate bloqueia traversal", r.get("reason") == "nota fora do vault",
          f"got={r}")
    # 2) correlate com projeto legitimo funciona
    r2 = predictive.correlate("30_PROJECTS/MeuBolso/README.md")
    check("correlate nota legitima funciona", "related" in r2 and "reason" in r2,
          f"got={r2.get('reason')}")
    # 3) suggest com traversal de projeto nao vaza
    r3 = predictive.suggest("../x")
    check("suggest nao vaza path (projeto inexistente/confinado)",
          r3.get("suggested") is None, f"got={r3}")
    # 4) suggest legitimo
    r4 = predictive.suggest("MeuBolso")
    check("suggest projeto legitimo funciona", r4.get("suggested") is not None,
          f"got={r4.get('suggested')}")
    print("\nRESULTADO: %d passaram, %d falharam" % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
