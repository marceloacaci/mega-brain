#!/usr/bin/env python3
"""e2e_security.py — Endurecimento de rotas: path traversal (S11).

Prova que o MCP recusa paths que saem do vault, tanto em leitura (`GET /read`)
como em escrita (`POST /write`). Antes do fix, `_vault_path` fazia
`os.path.join(VAULT, rel.strip('/\\'))` sem confinar, entao
`path=../../../evil.md` escrevia FORA do vault.

Padroes seguidos: SERVER repo-relative (P3/P5), porta fixa alta (P5),
stderr=PIPE (P7), fixture via tempfile.mkdtemp (P9).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS",
                                     "mcp_obsidian_server.py"))
PORT = 8903
BASE = f"http://127.0.0.1:{PORT}"

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")


def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


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
    print("=== E2E Seguranca S11 (path traversal) ===")
    outer = tempfile.mkdtemp(prefix="mb_sec_")
    vault = os.path.join(outer, "vault")
    os.makedirs(os.path.join(vault, "10_MEGA_BRAIN"))
    with open(os.path.join(vault, "10_MEGA_BRAIN", "ok.md"), "w",
              encoding="utf-8") as fh:
        fh.write("# OK\n\nconteudo legitimo\n")
    # arquivo sensivel FORA do vault (irmao) que nao deve ser alcancavel
    secret = os.path.join(outer, "secret.md")
    with open(secret, "w", encoding="utf-8") as fh:
        fh.write("SEGREDO\n")

    proc = subprocess.Popen(
        [sys.executable, SERVER, "--vault", vault, "--port", str(PORT)],
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

        # 1) leitura legitima continua funcionando (nao quebramos o caminho bom)
        st, body = get("/read?path=10_MEGA_BRAIN/ok.md")
        check("read legitimo = 200", st == 200 and "conteudo legitimo"
              in body.get("content", ""), f"st={st} body={body}")

        # 2) traversal em /read nao vaza arquivo de fora do vault
        st, body = get("/read?path=../secret.md")
        check("read traversal bloqueado (404, sem SEGREDO)",
              st == 404 and "SEGREDO" not in json.dumps(body),
              f"st={st} body={body}")

        # 3) traversal em /write NAO cria arquivo fora do vault
        st, body = post("/write", {"path": "../evil.md", "content": "x"})
        escaped = os.path.join(outer, "evil.md")
        check("write traversal bloqueado (400)", st == 400, f"st={st} body={body}")
        check("nenhum arquivo criado fora do vault",
              not os.path.exists(escaped), f"existe={escaped}")

        # 4) escrita legitima continua funcionando
        st, body = post("/write", {"path": "10_MEGA_BRAIN/nova.md",
                                   "content": "# Nova\n"})
        check("write legitimo = 200",
              st == 200 and os.path.exists(
                  os.path.join(vault, "10_MEGA_BRAIN", "nova.md")),
              f"st={st} body={body}")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            pass
        shutil.rmtree(outer, ignore_errors=True)

    print(f"\nRESULTADO: {PASS} passaram, {FAIL} falharam")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
