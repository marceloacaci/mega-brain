#!/usr/bin/env python3
"""Orquestrador da suíte de testes MEGA BRAIN (M6 Polimento).

Roda todos os testes de uma vez e reporta o resumo. Útil para o dev validar
localmente antes do PR e para o CI (quality.md: \"pirâmide de testes\").
Nao altera o vault real.

Uso:
  python tests/run_all.py
Exit 0 se tudo passar, 1 se algum falhar.
"""
import subprocess
import sys

SUITE = [
    ("Smoke MCP (8 rotas)", ["python", "tests/smoke_test.py"]),
    ("Debounce watcher (4)", ["python", "tests/test_watcher_debounce.py"]),
    ("E2E validação M4 (2)", ["python", "tests/e2e_validate.py"]),
    ("E2E resiliência M5 (3)", ["python", "tests/e2e_backup.py"]),
    ("E2E hooks (4)", ["python", "tests/e2e_hooks.py"]),
    ("E2E integração (fluxo fim-a-fim)", ["python", "tests/e2e_integration.py"]),
]


def main():
    print("=== MEGA BRAIN — SUÍTE COMPLETA DE TESTES ===\n")
    results = []
    for name, cmd in SUITE:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            passed = p.returncode == 0
            results.append((name, passed, p.returncode))
            tag = "OK " if passed else "FAIL"
            print(f"[{tag}] {name}  (rc={p.returncode})")
            if not passed:
                # mostra só as linhas de resultado do sub-teste
                for line in (p.stdout + p.stderr).splitlines():
                    if "RESULTADO" in line or "PASS " in line or "FAIL " in line:
                        print("      " + line)
        except Exception as e:  # noqa
            results.append((name, False, -1))
            print(f"[FAIL] {name}  (erro: {e})")

    total = len(results)
    ok = sum(1 for _, p, _ in results if p)
    print(f"\n=== RESUMO: {ok}/{total} suítes verdes ===")
    for name, p, rc in results:
        print(f"  {'OK ' if p else 'FAIL'} {name}")
    print("\nVEREDITO:", "TODAS AS SUÍTES VERDES" if ok == total else "HÁ FALHAS")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
