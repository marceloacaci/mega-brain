#!/usr/bin/env python3
"""E2E do endpoint /recent do MCP (NOTAS RECENTES — S14).

Sobe o mcp_obsidian_server.py num vault fixture temporário e valida que
GET /recent retorna notas ordenadas por mtime decrescente e respeita `limit`.
Reaproveita helpers de tests/smoke_test.py.

Uso:
  python tests/e2e_recent.py
Exit 0 se passar, 1 se falhar.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smoke_test import make_fixture, get_json, wait_health  # noqa: E402

SERVER = os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS", "mcp_obsidian_server.py"))


def main():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    tmp = tempfile.mkdtemp(prefix="mb_e2e_recent_")
    results = []
    proc = None
    try:
        make_fixture(tmp)
        # cria uma nota adicional MAIS RECENTE (mtime ~agora) p/ testar ordenacao
        new_note = os.path.join(tmp, "80_SYSTEM", "NOVA_RECENTE.md")
        os.makedirs(os.path.dirname(new_note), exist_ok=True)
        with open(new_note, "w", encoding="utf-8") as fh:
            fh.write("# nota nova\n")
        time.sleep(0.05)  # garante mtime distinto

        proc = subprocess.Popen(
            [sys.executable, SERVER, "--port", str(port), "--vault", tmp],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        base = f"http://127.0.0.1:{port}"
        if not wait_health(base):
            print("FAIL health: servidor nao subiu")
            return 1

        # 1) /recent retorna lista e a mais recente e NOVA_RECENTE
        try:
            r = get_json(f"{base}/recent?limit=10")
            rec = r.get("recent", [])
            ok = (isinstance(rec, list) and len(rec) >= 4
                  and rec[0]["path"].endswith("NOVA_RECENTE.md"))
            results.append(("recent_ordenado", ok))
        except Exception as e:
            results.append(("recent_ordenado", False))
            print(f"   erro recent: {e}")

        # 2) limit respeitado
        try:
            r2 = get_json(f"{base}/recent?limit=2")
            results.append(("recent_limit", len(r2.get("recent", [])) == 2))
        except Exception as e:
            results.append(("recent_limit", False))
            print(f"   erro recent limit: {e}")

        # 3) campos obrigatorios (path/mtime/age_days/type)
        try:
            r3 = get_json(f"{base}/recent?limit=1")
            item = r3["recent"][0]
            results.append(("recent_campos", all(k in item for k in ("path", "mtime", "age_days", "type"))))
        except Exception as e:
            results.append(("recent_campos", False))
            print(f"   erro recent campos: {e}")

        # 4) mtime decrescente no payload real
        try:
            r4 = get_json(f"{base}/recent?limit=10")
            mts = [x["mtime"] for x in r4["recent"]]
            results.append(("recent_mtime_desc", mts == sorted(mts, reverse=True)))
        except Exception as e:
            results.append(("recent_mtime_desc", False))
            print(f"   erro recent mtime: {e}")
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
