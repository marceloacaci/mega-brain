#!/usr/bin/env python3
"""e2e_backlinks.py — S17: rota GET /backlinks do MCP.

Sobe o MCP (repo-relative — P5) num vault fixture temporario e valida:
  1. /backlinks?path=<nota> devolve as fontes corretas + flag `cached`
  2. 2a chamada vem do cache (cached=True)
  3. path ausente -> 400
  4. nota inexistente -> 404
  5. traversal (../..) -> 400 (nunca 200)

Rode: python tests/e2e_backlinks.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS",
                                      "mcp_obsidian_server.py"))
PORT = 8903  # porta fixa alta (P5.3 — evita race do free_port)
BASE = "http://127.0.0.1:%d" % PORT

FAILS = []


def check(cond, msg):
    if cond:
        print("  OK  " + msg)
    else:
        print("  FAIL " + msg)
        FAILS.append(msg)


def make_vault():
    v = tempfile.mkdtemp(prefix="mb_e2ebl_")
    os.makedirs(os.path.join(v, "10_MEGA_BRAIN"))
    os.makedirs(os.path.join(v, "70_MOCS"))

    def w(rel, text):
        with open(os.path.join(v, rel.replace("/", os.sep)), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    w("10_MEGA_BRAIN/Alvo.md", "# Alvo\n\nnota alvo\n")
    w("70_MOCS/MOC.md", "# MOC\n\n[[Alvo]] e [[Alvo|ap]]\n")
    w("10_MEGA_BRAIN/Outra.md", "# Outra\n\n[[Alvo]]\n")
    w("10_MEGA_BRAIN/Nada.md", "# Nada\n\nsem link\n")
    return v


def get(path, timeout=20):
    """GET -> (status, payload_dict). Nao levanta em 4xx/5xx."""
    try:
        with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, {"raw": body[:200]}


def wait_health(proc, tries=200):
    for _ in range(tries):
        if proc.poll() is not None:
            break
        try:
            st, d = get("/health", timeout=2)
            if st == 200 and d.get("ok"):
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def main():
    vault = make_vault()
    env = dict(os.environ)
    env["MCP_PORT"] = str(PORT)
    env["MCP_HOST"] = "127.0.0.1"
    env["VAULT"] = vault
    env["OBSIDIAN_VAULT"] = vault
    proc = subprocess.Popen(
        [sys.executable, SERVER, "--vault", vault, "--port", str(PORT)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        if not wait_health(proc):
            err = b""
            try:
                err = proc.stderr.read()[:800]  # P7: nunca esconder o stderr
            except Exception:
                pass
            print("FAIL: server nao subiu; stderr=", err.decode("utf-8", "ignore"))
            return 1

        st, d = get("/backlinks?path=" + urllib.parse.quote("10_MEGA_BRAIN/Alvo.md"))
        check(st == 200, "GET /backlinks -> 200 (got %s)" % st)
        paths = {x["path"]: x["count"] for x in d.get("backlinks", [])}
        check(d.get("total") == 2, "total=2 fontes (got %r)" % d.get("total"))
        check(paths.get("70_MOCS/MOC.md") == 2, "MOC conta 2 (alias incluso)")
        check(paths.get("10_MEGA_BRAIN/Outra.md") == 1, "Outra conta 1")
        check("10_MEGA_BRAIN/Nada.md" not in paths, "nota sem link ausente")
        check(d.get("cached") is False, "1a chamada nao cacheada")

        st2, d2 = get("/backlinks?path=" + urllib.parse.quote("10_MEGA_BRAIN/Alvo.md"))
        check(st2 == 200 and d2.get("cached") is True,
              "2a chamada vem do cache (cached=%r)" % d2.get("cached"))

        st3, _ = get("/backlinks")
        check(st3 == 400, "path ausente -> 400 (got %s)" % st3)

        st4, _ = get("/backlinks?path=" + urllib.parse.quote("10_MEGA_BRAIN/XX.md"))
        check(st4 == 404, "nota inexistente -> 404 (got %s)" % st4)

        st5, d5 = get("/backlinks?path=" + urllib.parse.quote("../../secret.md"))
        check(st5 == 400, "traversal -> 400 (got %s)" % st5)
        check(st5 != 200, "traversal NUNCA retorna 200")
    finally:
        try:
            proc.terminate()  # encerra APENAS o server que este teste subiu
            proc.wait(timeout=10)
        except Exception:
            pass
        shutil.rmtree(vault, ignore_errors=True)

    print()
    if FAILS:
        print("RESULTADO: %d FALHA(S)" % len(FAILS))
        return 1
    print("RESULTADO: E2E /backlinks OK (S17)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
