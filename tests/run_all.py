#!/usr/bin/env python3
"""Orquestrador da suíte de testes MEGA BRAIN (M6 Polimento).

Roda todos os testes de uma vez e reporta o resumo. Útil para o dev validar
localmente antes do PR e para o CI (quality.md: \"pirâmide de testes\").
Nao altera o vault real.

Uso:
  python tests/run_all.py
Exit 0 se tudo passar, 1 se algum falhar.
"""
import os
import subprocess
import sys

# No CI (GitHub Actions), os testes Windows-specific (e2e_backup, e2e_hooks)
# rodam no job Windows dedicado. O run_all no job Linux pula eles para evitar
# flakiness por ambiente (pwsh/robocopy ausentes ou aninhamento de subprocess).
IN_CI = bool(os.environ.get("GITHUB_ACTIONS"))

SUITE = [
    ("Smoke MCP (8 rotas)", ["python", "tests/smoke_test.py"]),
    ("Debounce watcher (4)", ["python", "tests/test_watcher_debounce.py"]),
    ("E2E validação M4 (2)", ["python", "tests/e2e_validate.py"]),
    ("E2E v2.0 inovação (5)", ["python", "tests/e2e_v2.py"]),
    ("E2E Ollama S10-A (skip se ausente)", ["python", "tests/e2e_ollama.py"]),
    ("E2E Dashboard S10-B (grafo+html)", ["python", "tests/e2e_dashboard.py"]),
    ("E2E Governanca S10-C (injection+PII)", ["python", "tests/e2e_governance.py"]),
    ("E2E Seguranca S11 (path traversal)", ["python", "tests/e2e_security.py"]),
    ("Unidade validate links S11 (6)", ["python", "tests/test_validate_links.py"]),
    ("Unidade governance PII S11 (20)", ["python", "tests/test_governance_pii.py"]),
    ("Unidade compress contrato S11 (22)", ["python", "tests/test_compress_contract.py"]),
    ("Unidade segurança v2 S12 (traversal+On2)", ["python", "tests/test_security_v2.py"]),
    ("Unidade dashboard orfãos S12 (wikilink)", ["python", "tests/test_dashboard_orphans.py"]),
    ("Unidade teto notas semantic==graph S12", ["python", "tests/test_note_limit_consistency.py"]),
    ("Unidade predictive traversal S12", ["python", "tests/test_predictive_security.py"]),
    ("Unidade modulos compartilhados S13 (const+guards)", ["python", "tests/test_shared_modules.py"]),
    ("Unidade notas recentes S14 (ordenacao+limit+cutoff)", ["python", "tests/test_recent.py"]),
    ("E2E notas recentes S14 (rota /recent)", ["python", "tests/e2e_recent.py"]),
    ("Unidade nuvem de tags S15 (frontmatter+inline+top_only)", ["python", "tests/test_tags.py"]),
    ("E2E nuvem de tags S15 (rota /tags)", ["python", "tests/e2e_tags.py"]),
    ("Unidade tag() S16 (nao dropa tags)", ["python", "tests/test_tag_func.py"]),
    ("Unidade cache /validate S16 (mtime/TTL)", ["python", "tests/test_validate_cache.py"]),
    ("Unidade backlinks S17 (alias+codigo+traversal)", ["python", "tests/test_backlinks.py"]),
    ("E2E backlinks S17 (rota /backlinks)", ["python", "tests/e2e_backlinks.py"]),
    ("Unidade links saida S20 (alias+codigo+auto+quebrado+cache)", ["python", "tests/test_links.py"]),
    ("E2E links saida S20 (rota /links)", ["python", "tests/e2e_links.py"]),
    ("Unidade cache atividade S22 (heatmap mtime/TTL)", ["python", "tests/test_activity_cache.py"]),
    ("Unidade cache semantico S19 (related+suggest)", ["python", "tests/test_semantic_cache.py"]),
    ("E2E cache semantico S19 (rotas /related+/suggest)", ["python", "tests/e2e_semantic_cache.py"]),
    ("E2E integração (fluxo fim-a-fim)", ["python", "tests/e2e_integration.py"]),
    ("E2E integração (fluxo fim-a-fim)", ["python", "tests/e2e_integration.py"]),
]
if not IN_CI:
    # Apenas local: estes precisam de pwsh/robocopy (Windows) e tem job proprio no CI.
    SUITE += [
        ("E2E resiliência M5 (3)", ["python", "tests/e2e_backup.py"]),
        ("E2E hooks (4)", ["python", "tests/e2e_hooks.py"]),
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
