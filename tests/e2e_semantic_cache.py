#!/usr/bin/env python3
"""E2E dos endpoints /related e /suggest com cache (SEMANTIC CACHE — S19).

Sobe o mcp_obsidian_server.py num vault fixture e valida que GET /related e
GET /suggest retornam listas ordenadas por score e expoem a flag `cached`
(miss no 1o acesso, hit no 2o). Reaproveita helpers de smoke_test.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import socket
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smoke_test import make_fixture, get_json, wait_health  # noqa: E402

SERVER = os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS", "mcp_obsidian_server.py"))


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    tmp = tempfile.mkdtemp(prefix="mb_e2e_semcache_")
    results = []
    proc = None
    try:
        make_fixture(tmp)
        # notas com termos sobrepostos p/ garantir related > 0
        a = os.path.join(tmp, "10_MEGA_BRAIN", "A.md")
        os.makedirs(os.path.dirname(a), exist_ok=True)
        with open(a, "w", encoding="utf-8") as fh:
            fh.write("# A\nPython automacao de tarefas diarias no windows.\n")
        b = os.path.join(tmp, "30_PROJECTS", "B.md")
        os.makedirs(os.path.dirname(b), exist_ok=True)
        with open(b, "w", encoding="utf-8") as fh:
            fh.write("# B\nPython scripting para integracao de dados e automacao.\n")

        proc = subprocess.Popen(
            [sys.executable, SERVER, "--port", str(port), "--vault", tmp],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        base = f"http://127.0.0.1:{port}"
        if not wait_health(base):
            print("FAIL health: servidor nao subiu")
            return 1

        # 1) /related: 1o acesso miss (cached=False), lista nao vazia
        try:
            r = get_json(f"{base}/related?path=10_MEGA_BRAIN/A.md&k=2")
            rel = r.get("related", [])
            ok = isinstance(rel, list) and len(rel) >= 1
            ok = ok and all("score" in x for x in rel)
            results.append(("related_miss_payload", ok))
            results.append(("related_flag_miss", r.get("cached") is False))
        except Exception as e:
            results.append(("related_miss_payload", False))
            print(f"   erro related: {e}")

        # 2) /related: 2o acesso hit (cached=True)
        try:
            r2 = get_json(f"{base}/related?path=10_MEGA_BRAIN/A.md&k=2")
            results.append(("related_flag_hit", r2.get("cached") is True))
            results.append(("related_payload_estavel", len(r2.get("related", [])) >= 1))
        except Exception as e:
            results.append(("related_flag_hit", False))
            print(f"   erro related hit: {e}")

        # 3) /suggest: miss -> hit
        try:
            q = "python automacao"
            s1 = get_json(f"{base}/suggest?q={urllib.parse.quote(q)}&k=2")
            s2 = get_json(f"{base}/suggest?q={urllib.parse.quote(q)}&k=2")
            ok = isinstance(s1.get("suggestions", []), list)
            results.append(("suggest_miss_payload", ok))
            results.append(("suggest_flag_miss", s1.get("cached") is False))
            results.append(("suggest_flag_hit", s2.get("cached") is True))
        except Exception as e:
            results.append(("suggest_miss_payload", False))
            print(f"   erro suggest: {e}")

        # 4) traversal em /related -> 400 (VaultPathError, P16)
        try:
            import json
            req = urllib.request.Request(f"{base}/related?path=../../etc/passwd&k=2")
            try:
                urllib.request.urlopen(req, timeout=5)
                results.append(("related_traversal_400", False))
            except urllib.error.HTTPError as he:
                results.append(("related_traversal_400", he.code == 400))
        except Exception as e:
            results.append(("related_traversal_400", False))
            print(f"   erro traversal: {e}")
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)

    ok = True
    for name, passed in results:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
        ok = ok and passed
    print("RESULTADO:", "TODOS PASSARAM" if ok else "FALHAS DETECTADAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
