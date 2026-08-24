#!/usr/bin/env python3
"""e2e_api_contract.py — S21: o contrato documentado em docs/api-reference.md
casa com o comportamento REAL do MCP?

Motivacao (P13): vários bugs do dashboard passaram no CI porque o cliente leu uma
chave que a rota não devolve (ex.: `data.results` quando `/search` devolve `hits`).
Esta suíte é o guard-rail: se alguém renomear uma chave de resposta ou mudar um
status code, ela fica VERMELHA — e a documentação deixa de mentir silenciosamente.

Cobre, contra um MCP real num vault fixture:
  - as chaves de resposta de 12 rotas GET;
  - `/metrics` é TEXTO Prometheus (não JSON);
  - `/search` expõe `hits` (e NÃO `results`), com `ctx` nos itens;
  - `graph.nodes[].id` é reutilizável direto em `/backlinks?path=`;
  - rota desconhecida -> 404 `unknown endpoint`;
  - traversal: `/read` -> 404, `/backlinks` e `/links` -> 400; `path` ausente -> 400.

Rode: python tests/e2e_api_contract.py
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
DOC = os.path.abspath(os.path.join(HERE, "..", "docs", "api-reference.md"))
PORT = 8909  # porta fixa alta (P5.3)
BASE = "http://127.0.0.1:%d" % PORT

FAILS = []


def check(cond, msg):
    print(("  OK  " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def make_vault():
    v = tempfile.mkdtemp(prefix="mb_api_")
    os.makedirs(os.path.join(v, "10_MEGA_BRAIN"))
    os.makedirs(os.path.join(v, "20_DAILY_NOTES"))

    def w(rel, t):
        with open(os.path.join(v, rel.replace("/", os.sep)), "w",
                  encoding="utf-8") as fh:
            fh.write(t)

    w("10_MEGA_BRAIN/A.md", "# A\n\ntag #teste\n\n[[B]]\n")
    w("10_MEGA_BRAIN/B.md", "# B\n\ncorpo com termo alfa #teste\n")
    w("20_DAILY_NOTES/2026-08-24.md", "# hoje\n")
    return v


def get(path, timeout=30):
    """GET -> (status, dict). Payload nao-JSON vira {'_text': ...}."""
    try:
        with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
            body = r.read().decode("utf-8", "ignore")
            try:
                return r.status, json.loads(body)
            except ValueError:
                return r.status, {"_text": body[:200]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"_text": raw[:200]}


# Contrato documentado em docs/api-reference.md: rota -> chaves obrigatorias.
EXPECTED = [
    ("/health", ["ok", "vault"]),
    ("/search?q=alfa", ["query", "hits", "cache"]),
    ("/read?path=10_MEGA_BRAIN/A.md", ["path", "content"]),
    ("/stats", ["total", "by_dir", "cached"]),
    ("/recent?limit=5", ["recent", "cached"]),
    ("/tags?limit=10", ["tags", "cached"]),
    ("/activity", ["daily_dir", "by_date"]),
    ("/graph?k=2", ["nodes", "edges"]),
    ("/backlinks?path=10_MEGA_BRAIN/B.md",
     ["path", "title", "total", "backlinks", "cached"]),
    ("/links?path=10_MEGA_BRAIN/A.md",
     ["path", "title", "total", "links", "cached"]),
    ("/orphans-in", ["total_notas", "total_orfas", "orphans", "cached"]),
    ("/validate", ["ok", "total_notas", "problemas"]),
]


def wait_health(proc, tries=200):
    for _ in range(tries):
        if proc.poll() is not None:
            return False
        try:
            if get("/health", timeout=2)[1].get("ok"):
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def main():
    print("=== E2E contrato de API S21 (docs/api-reference.md vs MCP real) ===")
    check(os.path.isfile(DOC), "docs/api-reference.md existe")
    vault = make_vault()
    env = dict(os.environ)
    env["MCP_PORT"] = str(PORT)
    env["MCP_HOST"] = "127.0.0.1"
    proc = subprocess.Popen(
        [sys.executable, SERVER, "--vault", vault, "--port", str(PORT)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        if not wait_health(proc):
            err = b""
            try:
                err = proc.stderr.read()[:800]  # P7: stderr sempre visivel
            except Exception:
                pass
            print("FAIL: server nao subiu; stderr=",
                  err.decode("utf-8", "ignore"))
            return 1

        doc = open(DOC, encoding="utf-8").read()

        for route, keys in EXPECTED:
            st, d = get(route)
            check(st == 200, "%s -> 200 (got %s)" % (route, st))
            miss = [k for k in keys if k not in d]
            check(not miss, "%s tem as chaves documentadas%s"
                  % (route, (" (faltam %s)" % miss) if miss else ""))
            # a rota precisa estar MENCIONADA no doc (evita doc defasado)
            base = route.split("?")[0]
            check(base in doc, "%s aparece em api-reference.md" % base)

        st, d = get("/metrics")
        check(st == 200 and "mcp_requests_total" in d.get("_text", ""),
              "/metrics devolve TEXTO Prometheus (nao JSON)")

        _, d = get("/search?q=alfa")
        check("results" not in d,
              "/search NAO expoe 'results' (so 'hits') — contrato do P13")
        hits = d.get("hits", [])
        check(len(hits) >= 1 and "ctx" in hits[0],
              "itens de /search tem 'ctx' (nao 'snippet')")

        _, g = get("/graph?k=2")
        nid = (g.get("nodes") or [{}])[0].get("id", "")
        st2, _ = get("/backlinks?path=" + urllib.parse.quote(nid))
        check(bool(nid) and st2 == 200,
              "graph.nodes[].id serve direto em /backlinks?path= (got %s)" % st2)

        st3, d3 = get("/naoexiste")
        check(st3 == 404 and d3.get("error") == "unknown endpoint",
              "rota desconhecida -> 404 'unknown endpoint'")

        trav = urllib.parse.quote("../../x.md")
        check(get("/read?path=" + trav)[0] == 404, "/read traversal -> 404")
        check(get("/backlinks?path=" + trav)[0] == 400,
              "/backlinks traversal -> 400")
        check(get("/links?path=" + trav)[0] == 400, "/links traversal -> 400")
        check(get("/backlinks")[0] == 400, "/backlinks sem path -> 400")
        check(get("/links")[0] == 400, "/links sem path -> 400")
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
    print("RESULTADO: contrato de API OK (doc casa com o MCP real)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
