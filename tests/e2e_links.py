#!/usr/bin/env python3
"""e2e_links.py — S20: rota GET /links do MCP.

Sobe o MCP (repo-relative — P5) num vault fixture temporario e valida:
  1. /links?path=<nota> devolve os links de saida + flag `cached`
  2. 2a chamada vem do cache (cached=True)
  3. path ausente -> 400
  4. nota inexistente -> 404
  5. traversal (../..) -> 400 (nunca 200)

Rode: python tests/e2e_links.py
"""
import json
import os
import shutil
import socket
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

# Porta dinamica (P5/P10): evita colisao com processos zumbis de runs anteriores
# que seguravam a porta fixa e faziam o teste bater no servidor errado (404).
def _free_port():
    """Porta alta livre: evita colisao com servidores zumbis em run_all."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


PORT = _free_port()
BASE = "http://127.0.0.1:%d" % PORT

FAILS = []


def check(cond, msg):
    if cond:
        print("  OK  " + msg)
    else:
        print("  FAIL " + msg)
        FAILS.append(msg)


def make_vault():
    v = tempfile.mkdtemp(prefix="mb_e2elinks_")
    os.makedirs(os.path.join(v, "10_MEGA_BRAIN"))
    os.makedirs(os.path.join(v, "30_PROJECTS", "Proj"))

    def w(rel, text):
        with open(os.path.join(v, rel.replace("/", os.sep)), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    w("10_MEGA_BRAIN/Origem.md", "# Origem\n[[Alvo]] e [[30_PROJECTS/Proj/Destino|ap]].\n`[[Alvo]]` em codigo nao conta.\n")
    w("10_MEGA_BRAIN/Alvo.md", "# Alvo\n")
    w("30_PROJECTS/Proj/Destino.md", "# Destino\n")
    w("10_MEGA_BRAIN/Quebrado.md", "# Quebrado\n[[Inexistente]] e ${ph}}\n")
    return v


def get(path, timeout=20):
    try:
        with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception:
        return None, {}


def wait_health(proc, tries=200):
    for _ in range(tries):
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
        if proc.poll() is not None:
            break
    return False


def main():
    v = make_vault()
    proc = subprocess.Popen(
        [sys.executable, SERVER, "--vault", v, "--port", str(PORT)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        if not wait_health(proc):
            err = b""
            try:
                err = proc.stderr.read()
            except Exception:
                pass
            print("FAIL: server nao subiu; stderr=", err.decode()[:800])
            return 1

        # 1) links de saida
        st, body = get("/links?path=10_MEGA_BRAIN/Origem.md")
        check(st == 200, "/links Origem -> 200 (st=%s)" % st)
        links = body.get("links", [])
        check(body.get("total") == 2 or len(links) == 2,
              "/links total=2 (B e C; codigo ignorado) got=%s" % body.get("total"))
        by = {x["target"]: x for x in links}
        check(by.get("Alvo", {}).get("resolved") is True, "resolve Alvo por stem")
        check(by.get("30_PROJECTS/Proj/Destino", {}).get("resolved") is True,
              "resolve Destino por pasta/alias")
        check(by.get("Alvo", {}).get("count") == 1, "conta 1x (2o em codigo)")

        # 2) cache hit
        st2, body2 = get("/links?path=10_MEGA_BRAIN/Origem.md")
        check(body2.get("cached") is True, "/links 2a chamada cached=True")

        # 3/4/5) erros
        st3, _ = get("/links")
        check(st3 == 400, "/links sem path -> 400 (st=%s)" % st3)

        st4, _ = get("/links?path=10_MEGA_BRAIN/NaoExiste.md")
        check(st4 == 404, "/links nota inexistente -> 404 (st=%s)" % st4)

        st5, _ = get("/links?path=../../Windows/win.ini")
        check(st5 == 400, "/links traversal -> 400 (st=%s)" % st5)

        # link quebrado marcado nao-resolvido
        stq, bodyq = get("/links?path=10_MEGA_BRAIN/Quebrado.md")
        bq = {x["target"]: x for x in bodyq.get("links", [])}
        check(bq.get("Inexistente", {}).get("resolved") is False,
              "link quebrado -> resolved=False")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            pass
        shutil.rmtree(v, ignore_errors=True)

    if FAILS:
        print("\nRESULTADO: %d FALHA(S): %s" % (len(FAILS), "; ".join(FAILS)))
        return 1
    print("\nRESULTADO: TODOS PASSARAM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
