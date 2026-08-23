#!/usr/bin/env python3
"""E2E de Extensibilidade (M4): rota /validate do MCP.

Sobe o MCP server num fixture de vault e valida:
  - GET /validate em vault integro retorna ok=true
  - GET /validate em vault com [[link quebrado]] retorna ok=false e lista o problema
Nao altera o vault real. Requer Python stdlib (urllib).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = r"D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
SERVER = os.path.join(VAULT, "80_SYSTEM", "SCRIPTS", "mcp_obsidian_server.py")


def get_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return __import__("json").loads(r.read().decode("utf-8"))


def make_fixture(root, broken=False):
    os.makedirs(os.path.join(root, "10_MEGA_BRAIN"), exist_ok=True)
    os.makedirs(os.path.join(root, "70_MOCS"), exist_ok=True)
    os.makedirs(os.path.join(root, "80_SYSTEM"), exist_ok=True)
    with open(os.path.join(root, "10_MEGA_BRAIN", "INDEX_GERAL.md"), "w", encoding="utf-8") as f:
        f.write("# Index\n")
    with open(os.path.join(root, "70_MOCS", "MOC_OK.md"), "w", encoding="utf-8") as f:
        f.write("---\ntipo: moc\ntags: [moc]\n---\n# OK\n")
    if broken:
        with open(os.path.join(root, "10_MEGA_BRAIN", "WITH_BROKEN.md"), "w", encoding="utf-8") as f:
            f.write("Veja [[NotaQueNaoExiste]] para detalhes.\n")


def run_server(vault, port):
    env = dict(os.environ)
    proc = subprocess.Popen([sys.executable, SERVER, "--port", str(port), "--vault", vault],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    return proc


def main():
    print("=== E2E Extensibilidade (M4) /validate ===")
    results = []
    tmp = tempfile.mkdtemp(prefix="mb_m4_")
    port = 8799
    try:
        # 1. vault integro
        make_fixture(tmp, broken=False)
        proc = run_server(tmp, port)
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(50):
                try:
                    if get_json(f"{base}/health").get("ok"):
                        break
                except Exception:
                    time.sleep(0.2)
            rep_ok = get_json(f"{base}/validate")
            results.append(("validate_ok_true", rep_ok.get("ok") is True and rep_ok.get("total_notas", 0) >= 2))
            print(("PASS" if rep_ok.get("ok") else "FAIL"), "validate_ok_true", f"(ok={rep_ok.get('ok')}, notas={rep_ok.get('total_notas')})")
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except Exception: proc.kill()

        # 2. vault com link quebrado (novo fixture + nova porta)
        proc2 = run_server(tmp, port + 1)
        base2 = f"http://127.0.0.1:{port+1}"
        try:
            for _ in range(50):
                try:
                    if get_json(f"{base2}/health").get("ok"):
                        break
                except Exception:
                    time.sleep(0.2)
            make_fixture(tmp, broken=True)  # adiciona nota com link quebrado
            # reindexa? nao precisa; /validate varre disco
            rep_bad = get_json(f"{base2}/validate")
            tipos = [p.get("tipo") for p in rep_bad.get("problemas", [])]
            results.append(("validate_detects_broken", rep_bad.get("ok") is False and "link_quebrado" in tipos))
            print(("PASS" if ("link_quebrado" in tipos) else "FAIL"), "validate_detects_broken", f"(ok={rep_bad.get('ok')}, tipos={tipos})")
        finally:
            proc2.terminate()
            try: proc2.wait(timeout=5)
            except Exception: proc2.kill()
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
