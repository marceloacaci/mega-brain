#!/usr/bin/env python3
"""E2E do endpoint /tags do MCP (NUVEM DE TAGS — S15).

Sobe o mcp_obsidian_server.py num vault fixture temporário e valida que
GET /tags retorna contagem de tags ordenada. Reaproveita helpers de smoke_test.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import socket
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smoke_test import make_fixture, get_json, wait_health  # noqa: E402

SERVER = os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS", "mcp_obsidian_server.py"))


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    tmp = tempfile.mkdtemp(prefix="mb_e2e_tags_")
    results = []
    proc = None
    try:
        make_fixture(tmp)
        # nota extra com tags conhecidas p/ validar a rota
        extra = os.path.join(tmp, "10_MEGA_BRAIN", "Tags.md")
        os.makedirs(os.path.dirname(extra), exist_ok=True)
        with open(extra, "w", encoding="utf-8") as fh:
            fh.write("---\ntags: [meubolso, financeiro]\n---\n# tags\n#teste inline\n")
        # segunda nota com meubolso p/ nao ser filtrada por top_only (count>1)
        extra2 = os.path.join(tmp, "30_PROJECTS", "MeuBolso", "Extra.md")
        os.makedirs(os.path.dirname(extra2), exist_ok=True)
        with open(extra2, "w", encoding="utf-8") as fh:
            fh.write("---\ntags: [meubolso]\n---\n# extra\n")

        proc = subprocess.Popen(
            [sys.executable, SERVER, "--port", str(port), "--vault", tmp],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        base = f"http://127.0.0.1:{port}"
        if not wait_health(base):
            print("FAIL health: servidor nao subiu")
            return 1

        # 1) /tags retorna lista com campos tag/count, ordenada desc
        try:
            r = get_json(f"{base}/tags?limit=20")
            tags = r.get("tags", [])
            ok = isinstance(tags, list) and all("tag" in t and "count" in t for t in tags)
            counts = [t["count"] for t in tags]
            ok = ok and (counts == sorted(counts, reverse=True))
            results.append(("tags_ordenado", ok))
        except Exception as e:
            results.append(("tags_ordenado", False))
            print(f"   erro tags: {e}")

        # 2) nossa tag conhecida aparece
        try:
            r2 = get_json(f"{base}/tags?limit=50")
            by = {t["tag"]: t["count"] for t in r2.get("tags", [])}
            results.append(("tags_contem_meubolso", by.get("meubolso", 0) >= 1))
        except Exception as e:
            results.append(("tags_contem_meubolso", False))
            print(f"   erro tags meubolso: {e}")

        # 3) limit respeitado
        try:
            r3 = get_json(f"{base}/tags?limit=3")
            results.append(("tags_limit", len(r3.get("tags", [])) <= 3))
        except Exception as e:
            results.append(("tags_limit", False))
            print(f"   erro tags limit: {e}")
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
