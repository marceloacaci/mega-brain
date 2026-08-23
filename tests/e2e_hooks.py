#!/usr/bin/env python3
"""E2E dos hooks MEGA BRAIN (stdlib, sem dependencias).

Copia pre_/post_task_hook.ps1 para um vault fixture temporario, reescreve o
$Vault hardcoded para o fixture (em memoria, SEM alterar os arquivos originais)
e invoca os hooks com params PT. Valida:
  - daily note criada com a linha de inicio (pre) e execucao (post)
  - reindex light disparado (pre) quando .last_light.txt ausente
  - fallback falha-segura: hook nao quebra mesmo se vault estiver "corrompido"

Uso:
  python tests/e2e_hooks.py
Saida: linhas "PASS/FAIL <nome>" e exit 0 se tudo passar, 1 se falhar.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS_DIR = os.path.join(HERE, "..", "80_SYSTEM", "HOOKS_HERMES")
REINDEX = os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS", "reindex_hybrid.ps1")
CONFIG = os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS", "config.json")


def make_fixture(root):
    """Cria a estrutura minima do vault + config apontando para o fixture."""
    for d in ["10_MEGA_BRAIN", "20_DAILY_NOTES", "00_INBOX", "80_SYSTEM/LOGS"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)
    # config.json minimal com log_path e auto_reindex
    cfg = {
        "vault_path": root,
        "log_path": os.path.join(root, "80_SYSTEM", "LOGS"),
        "auto_reindex": {"force_after_hours": 4, "mode": "hybrid"},
        "watcher_debounce_ms": 2000,
    }
    with open(os.path.join(root, "80_SYSTEM", "LOGS", "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    # link simbolico de config para o SCRIPTS ler
    with open(os.path.join(root, "config_link.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    # INDEX_GERAL.md fake (para o hook ler)
    with open(os.path.join(root, "10_MEGA_BRAIN", "INDEX_GERAL.md"), "w", encoding="utf-8") as f:
        f.write("---\ntipo: meta-indice\n---\n\n# Index\n")
    return root


def rewrite_vault(script_path, fixture_root):
    """Le o hook e troca o $Vault hardcoded pelo fixture (nao toca o original)."""
    with open(script_path, "r", encoding="utf-8") as f:
        src = f.read()
    # substitui a linha '$Vault = "..."' pelo caminho do fixture
    import re
    src = re.sub(r'\$Vault\s*=\s*"[^"]*"', '$Vault = "%s"' % fixture_root.replace("\\", "\\\\"), src, count=1)
    return src


def run_hook(src, fixture_root, params, label):
    """Grava o hook em 80_SYSTEM/HOOKS_HERMES/ (preservando a hierarquia real
    para que $PSScriptRoot\\..\\SCRIPTS\\config.json resolva corretamente)."""
    hooks_dir = os.path.join(fixture_root, "80_SYSTEM", "HOOKS_HERMES")
    os.makedirs(hooks_dir, exist_ok=True)
    # garante que config.json e reindex existam no SCRIPTS do fixture
    scripts_dir = os.path.join(fixture_root, "80_SYSTEM", "SCRIPTS")
    os.makedirs(scripts_dir, exist_ok=True)
    cfg_src = os.path.join(fixture_root, "80_SYSTEM", "LOGS", "config.json")
    if os.path.exists(cfg_src):
        shutil.copy(cfg_src, os.path.join(scripts_dir, "config.json"))
    reindex_src = os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS", "reindex_hybrid.ps1")
    if os.path.exists(reindex_src):
        shutil.copy(reindex_src, os.path.join(scripts_dir, "reindex_hybrid.ps1"))
    tmp_hook = os.path.join(hooks_dir, "_hook_run.ps1")
    with open(tmp_hook, "w", encoding="utf-8") as f:
        f.write(src)
    cmd = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", tmp_hook] + params
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                              cwd=fixture_root, env=dict(os.environ))
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        # pwsh ausente no runner (ex.: ubuntu CI) -> reporta skip, nao falha
        return None, "", "pwsh not found"


def main():
    pre = os.path.join(HOOKS_DIR, "pre_task_hook.ps1")
    post = os.path.join(HOOKS_DIR, "post_task_hook.ps1")
    if not (os.path.exists(pre) and os.path.exists(post)):
        print("FAIL setup: hooks nao encontrados")
        return 1

    tmp = tempfile.mkdtemp(prefix="mb_e2e_")
    results = []
    try:
        make_fixture(tmp)
        pre_src = rewrite_vault(pre, tmp)
        post_src = rewrite_vault(post, tmp)

        today = date.today().strftime("%Y-%m-%d")
        daily = os.path.join(tmp, "20_DAILY_NOTES", today + ".md")

        # 1. pre hook (caso normal)
        rc, out, err = run_hook(pre_src, tmp, ["-Tarefa", "tarefa e2e", "-Projeto", "MeuBolso", "-Stack", "Electron,Vue"], "pre")
        if rc is None:
            print("SKIP pre (pwsh ausente)")
        else:
            ok = (rc == 0) and os.path.exists(daily) and "Início" in open(daily, encoding="utf-8").read()
            results.append(("pre_daily_note", ok))
            if not ok:
                print("  rc=%s err=%s" % (rc, err[:300]))

        # 2. post hook (caso normal)
        rc, out, err = run_hook(post_src, tmp, ["-Tarefa", "tarefa e2e", "-Projeto", "MeuBolso", "-Resultado", "sucesso", "-Resumo", "feito"], "post")
        if rc is None:
            print("SKIP post (pwsh ausente)")
        else:
            content = open(daily, encoding="utf-8").read() if os.path.exists(daily) else ""
            ok = (rc == 0) and ("✅" in content or "Resultado" in content)
            results.append(("post_daily_note", ok))
            if not ok:
                print("  rc=%s err=%s" % (rc, err[:300]))

        # 3. reindex light disparado (pre cria .last_light.txt quando ausente)
        last_light = os.path.join(tmp, "80_SYSTEM", "LOGS", ".last_light.txt")
        # roda pre de novo para forcar reindex
        run_hook(pre_src, tmp, ["-Tarefa", "segunda", "-Projeto", "X"], "pre2")
        ok = os.path.exists(last_light)
        results.append(("reindex_light_timestamp", ok))

        # 4. fallback falha-segura: config corrompido nao quebra o hook
        with open(os.path.join(tmp, "80_SYSTEM", "SCRIPTS", "config.json"), "w", encoding="utf-8") as f:
            f.write("{ invalid json ")
        rc, out, err = run_hook(pre_src, tmp, ["-Tarefa", "apos corromper", "-Projeto", "X"], "pre_corrupt")
        ok = (rc is not None and rc == 0)
        results.append(("hook_failsafe_on_corrupt_config", ok))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok_all = True
    for name, passed in results:
        print("%s %s" % ("PASS" if passed else "FAIL", name))
        ok_all = ok_all and passed
    print("RESULTADO:", "TODOS PASSARAM" if ok_all else "FALHAS DETECTADAS")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
