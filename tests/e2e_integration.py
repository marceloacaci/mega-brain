#!/usr/bin/env python3
"""E2E de Integração (M6): fluxo fim-a-fim do MEGA BRAIN.

Simula o ciclo real:
  1. pre_task_hook.ps1 (param PT) grava entrada no daily note
  2. MCP /write cria uma nota
  3. MCP /validate confirma o vault íntegro
  4. post_task_hook.ps1 grava resultado no daily note

Usa fixtures em tmp (nao altera o vault real). Requer pwsh 7 + Python stdlib.
Server MCP e hooks resolvidos via repo (nao vault hardcoded) para o CI.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
VAULT = r"D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
HOOKS_DIR = os.path.join(REPO, "80_SYSTEM", "HOOKS_HERMES")
SCRIPTS = os.path.join(REPO, "80_SYSTEM", "SCRIPTS")
SERVER = os.path.join(SCRIPTS, "mcp_obsidian_server.py")


def free_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def get_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def rewrite_vault(script_path, fixture_root):
    """Le o hook e troca o $Vault hardcoded pelo fixture (nao toca o original)."""
    with open(script_path, "r", encoding="utf-8") as f:
        src = f.read()
    src = re.sub(r'\$Vault\s*=\s*"[^"]*"', '$Vault = "%s"' % fixture_root.replace("\\", "\\\\"), src, count=1)
    return src


def run_pwsh(hook_name, fixture_root, *params):
    """Copia o hook para o fixture (preservando hierarquia $PSScriptRoot) e roda."""
    pre = os.path.join(HOOKS_DIR, hook_name)
    hooks_dir = os.path.join(fixture_root, "80_SYSTEM", "HOOKS_HERMES")
    os.makedirs(hooks_dir, exist_ok=True)
    scripts_dir = os.path.join(fixture_root, "80_SYSTEM", "SCRIPTS")
    os.makedirs(scripts_dir, exist_ok=True)
    cfg_src = os.path.join(fixture_root, "80_SYSTEM", "LOGS", "config.json")
    if os.path.exists(cfg_src):
        shutil.copy(cfg_src, os.path.join(scripts_dir, "config.json"))
    reindex_src = os.path.join(SCRIPTS, "reindex_hybrid.ps1")
    if os.path.exists(reindex_src):
        shutil.copy(reindex_src, os.path.join(scripts_dir, "reindex_hybrid.ps1"))
    src = rewrite_vault(pre, fixture_root)
    tmp_hook = os.path.join(hooks_dir, "_hook_run.ps1")
    with open(tmp_hook, "w", encoding="utf-8") as f:
        f.write(src)
    cmd = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", tmp_hook] + list(params)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=fixture_root, env=dict(os.environ))
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return None, "", "pwsh not found"


def make_vault_fixture(root):
    for d in ["10_MEGA_BRAIN", "20_DAILY_NOTES", "70_MOCS", "80_SYSTEM", "80_SYSTEM/SCRIPTS", "80_SYSTEM/LOGS"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)
    with open(os.path.join(root, "10_MEGA_BRAIN", "INDEX_GERAL.md"), "w", encoding="utf-8") as f:
        f.write("# Index\n")
    with open(os.path.join(root, "70_MOCS", "MOC_TEST.md"), "w", encoding="utf-8") as f:
        f.write("---\ntipo: moc\ntags: [moc]\n---\n# Test\n")
    # config.json minimal no LOGS (run_pwsh copia para SCRIPTS do fixture)
    cfg = {
        "vault_path": root,
        "log_path": os.path.join(root, "80_SYSTEM", "LOGS"),
        "auto_reindex": {"force_after_hours": 4, "mode": "hybrid"},
        "watcher_debounce_ms": 2000,
    }
    with open(os.path.join(root, "80_SYSTEM", "LOGS", "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def main():
    print("=== E2E Integração (M6) — fluxo fim-a-fim ===")
    tmp = tempfile.mkdtemp(prefix="mb_m6_")
    results = []
    port = free_port()
    try:
        vault_fx = os.path.join(tmp, "vault")
        os.makedirs(vault_fx)
        make_vault_fixture(vault_fx)

        # 1. pre_task_hook (falha-seguro) grava daily note
        rc1, _, err1 = run_pwsh("pre_task_hook.ps1", vault_fx,
                                "-Tarefa", "Criar nota de teste", "-Projeto", "M6",
                                "-Contexto", "integracao")
        daily = os.path.join(vault_fx, "20_DAILY_NOTES", time.strftime("%Y-%m-%d") + ".md")
        pre_ok = rc1 == 0 and os.path.exists(daily) and "Criar nota de teste" in open(daily, encoding="utf-8").read()
        if not pre_ok:
            print("  pre rc=%s err=%s" % (rc1, err1[:300]))
        results.append(("pre_hook_daily_note", pre_ok))
        print(("PASS" if pre_ok else "FAIL"), "pre_hook_daily_note")

        # 2. sobe MCP e faz /write + /validate
        env = dict(os.environ)
        proc = subprocess.Popen([sys.executable, SERVER, "--port", str(port), "--vault", vault_fx],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        base = f"http://127.0.0.1:{port}"
        try:
            up = False
            for _ in range(100):
                try:
                    if get_json(f"{base}/health").get("ok"):
                        up = True
                        break
                except Exception:
                    time.sleep(0.3)
            if not up:
                print("FAIL: server nao subiu;", proc.stderr.read().decode()[:400])
                results.append(("mcp_write_validate", False))
            else:
                data = json.dumps({"path": "30_PROJECTS/M6/nota.md", "content": "# Nota M6\nVeja [[MOC_TEST]].\n"}).encode()
                req = urllib.request.Request(f"{base}/write", data=data, headers={"Content-Type": "application/json"})
                w = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
                rep = get_json(f"{base}/validate")
                write_ok = w.get("written", "").endswith("nota.md") and rep.get("ok") is True
                results.append(("mcp_write_validate", write_ok))
                print(("PASS" if write_ok else "FAIL"), "mcp_write_validate", f"(ok={rep.get('ok')})")
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except Exception: proc.kill()

        # 3. post_task_hook grava resultado no daily note
        rc2, _, err2 = run_pwsh("post_task_hook.ps1", vault_fx,
                                "-Tarefa", "Criar nota de teste", "-Projeto", "M6",
                                "-Resultado", "ok", "-Resumo", "nota criada via MCP")
        post_ok = rc2 == 0 and os.path.exists(daily) and "nota criada via MCP" in open(daily, encoding="utf-8").read()
        if not post_ok:
            print("  post rc=%s err=%s" % (rc2, err2[:300]))
        results.append(("post_hook_result", post_ok))
        print(("PASS" if post_ok else "FAIL"), "post_hook_result")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = all(p for _, p in results)
    for name, p in results:
        if not p:
            print("FAIL", name)
    print("RESULTADO:", "TODOS PASSARAM" if ok else "FALHAS DETECTADAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
