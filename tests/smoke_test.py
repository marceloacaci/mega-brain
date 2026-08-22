#!/usr/bin/env python3
"""
MEGA BRAIN — Smoke test do MCP server (stdlib, sem dependências).

Sobe o mcp_obsidian_server.py num vault fixture temporário e valida as rotas
principais (GET /health, /search, /stats; POST /write, /read via /read GET).

Uso:
  python tests/smoke_test.py [--port 8799] [--server 80_SYSTEM/SCRIPTS/mcp_obsidian_server.py]

Saída: linhas "PASS/FAIL <nome>" e exit code 0 se tudo passar, 1 se falhar.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SERVER = os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS", "mcp_obsidian_server.py")


def make_fixture(root):
    """Cria um vault mínimo com 3 notas .md espalhadas."""
    os.makedirs(os.path.join(root, "10_MEGA_BRAIN"), exist_ok=True)
    os.makedirs(os.path.join(root, "30_PROJECTS", "MeuBolso"), exist_ok=True)
    notes = {
        "10_MEGA_BRAIN/INDEX_GERAL.md": "---\ntipo: meta-indice\n---\n\n# Index\n",
        "30_PROJECTS/MeuBolso/README.md": "# MeuBolso\nApp de finanças pessoais.\n",
        "30_PROJECTS/MeuBolso/TAREFAS.md": "# Tarefas\n- corrigir bug de parcela\n",
    }
    for rel, content in notes.items():
        with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
            fh.write(content)
    return notes


def get_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post_json(url, payload, timeout=5):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def wait_health(base, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            get_json(f"{base}/health")
            return True
        except Exception:
            time.sleep(0.2)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--server", default=DEFAULT_SERVER)
    args = ap.parse_args()

    server = os.path.abspath(args.server)
    if not os.path.exists(server):
        print(f"FAIL setup: server nao encontrado em {server}")
        return 1

    tmp = tempfile.mkdtemp(prefix="megabrain_fixture_")
    try:
        make_fixture(tmp)
        env = dict(os.environ)
        proc = subprocess.Popen(
            [sys.executable, server, "--port", str(args.port), "--vault", tmp],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
        )
        base = f"http://127.0.0.1:{args.port}"
        results = []

        if not wait_health(base):
            print("FAIL health: servidor nao subiu")
            proc.terminate()
            return 1

        # 1. health
        try:
            h = get_json(f"{base}/health")
            results.append(("health", h.get("ok") is True))
        except Exception as e:
            results.append(("health", False)); print(f"   erro health: {e}")

        # 2. write + read
        try:
            post_json(f"{base}/write", {"path": "40_AREAS/teste.md", "content": "conteudo de teste"})
            rd = get_json(f"{base}/read?path=40_AREAS/teste.md")
            results.append(("write+read", rd.get("content") == "conteudo de teste"))
        except Exception as e:
            results.append(("write+read", False)); print(f"   erro write/read: {e}")

        # 3. search (case-insensitive)
        try:
            s = get_json(f"{base}/search?q=" + urllib.parse.quote("parcela"))
            hits = s.get("hits", [])
            results.append(("search", any("parcela" in h.get("ctx", "").lower() for h in hits)))
        except Exception as e:
            results.append(("search", False)); print(f"   erro search: {e}")

        # 4. stats (contagem por pasta)
        try:
            st = get_json(f"{base}/stats")
            by_dir = st.get("by_dir", {})
            results.append(("stats", st.get("total", 0) >= 3 and "30_PROJECTS" in by_dir))
        except Exception as e:
            results.append(("stats", False)); print(f"   erro stats: {e}")

        # 5. rename (preserva conteudo)
        try:
            post_json(f"{base}/write", {"path": "40_AREAS/old.md", "content": "conteudo velho"})
            rn = post_json(f"{base}/rename", {"path": "40_AREAS/old.md", "new_name": "new.md"})
            rd2 = get_json(f"{base}/read?path=" + urllib.parse.quote("40_AREAS/new.md"))
            exists_old = False
            try:
                get_json(f"{base}/read?path=" + urllib.parse.quote("40_AREAS/old.md"))
                exists_old = True
            except Exception:
                pass
            results.append(("rename", rn.get("renamed") == "40_AREAS/new.md" and rd2.get("content") == "conteudo velho" and not exists_old))
        except Exception as e:
            results.append(("rename", False)); print(f"   erro rename: {e}")

        # 6. move (preserva nome)
        try:
            post_json(f"{base}/write", {"path": "40_AREAS/tomove.md", "content": "mover"})
            mv = post_json(f"{base}/move", {"path": "40_AREAS/tomove.md", "new_dir": "70_MOCS"})
            rd3 = get_json(f"{base}/read?path=" + urllib.parse.quote("70_MOCS/tomove.md"))
            results.append(("move", mv.get("moved") == "70_MOCS/tomove.md" and rd3.get("content") == "mover"))
        except Exception as e:
            results.append(("move", False)); print(f"   erro move: {e}")

        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = True
    for name, passed in results:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
        ok = ok and passed
    print("RESULTADO:", "TODOS PASSARAM" if ok else "FALHAS DETECTADAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
