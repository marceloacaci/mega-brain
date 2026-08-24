#!/usr/bin/env python3
"""E2E — dashboard web consome o grafo + painéis do MCP (S10-B + painéis v2.1).

Sobe o MCP num vault fixture e valida:
  - GET /graph retorna nos + arestas validos.
  - GET /activity retorna contrato {daily_dir, by_date}.
  - GET /validate retorna contrato {ok, total_notas, problemas}.
  - web/dashboard.html referencia os painéis: /graph, /activity, /validate, donut, orphans, legenda.
O teste NAO precisa de browser: valida o contrato de dados + o HTML.
"""
import os
import sys
import json
import time
import shutil
import socket
import subprocess
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.abspath(os.path.join(HERE, ".."))
SERVER = os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS", "mcp_obsidian_server.py"))
DASHBOARD = os.path.abspath(os.path.join(HERE, "..", "web", "dashboard.html"))


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def wait_health(base, proc=None, tries=100, delay=0.3):
    for _ in range(tries):
        try:
            with urllib.request.urlopen(f"{base}/health", timeout=2) as r:
                if json.loads(r.read()).get("ok"):
                    return True
        except Exception:
            if proc and proc.poll() is not None:
                return False
        time.sleep(delay)
    return False


def get_json(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main():
    if not os.path.exists(DASHBOARD):
        print("FAIL: web/dashboard.html ausente")
        return 1
    html = open(DASHBOARD, encoding="utf-8").read()
    # contratos consumidos pelo dashboard (painéis v2.1)
    for token in ["/graph", "/activity", "/validate", "id=\"donut\"", "id=\"orphans\"", "id=\"nodeTip\"",
                  "heatmap", "Caminho de Conexão", "Grafana", "Tema"]:
        if token not in html:
            print(f"FAIL: dashboard.html nao referencia '{token}'")
            return 1

    tmp = tempfile.mkdtemp(prefix="mb_dash_")
    try:
        for rel, txt in [
            ("10_MEGA_BRAIN/INDEX_GERAL.md", "---\ntipo: meta-indice\n---\n# Index\n- [[MOC_Teste]]\n"),
            ("70_MOCS/MOC_Teste.md", "# MOC_Teste\nRelacionado a [[Nota_Exemplo]].\n"),
            ("30_PROJECTS/Nota_Exemplo.md", "# Nota_Exemplo\nMenciona [[MOC_Teste]] e projeto exemplo.\n"),
        ]:
            d = os.path.join(tmp, os.path.dirname(rel))
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(tmp, rel), "w", encoding="utf-8") as fh:
                fh.write(txt)

        PORT = free_port()
        proc = subprocess.Popen([sys.executable, SERVER, "--port", str(PORT), "--vault", tmp],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        base = f"http://127.0.0.1:{PORT}"
        if not wait_health(base, proc):
            print("FAIL: server nao subiu;", proc.stderr.read().decode()[:400])
            return 1

        g = get_json(f"{base}/graph?k=3")
        n_nodes = len(g.get("nodes", []))
        n_edges = len(g.get("edges", []))
        act = get_json(f"{base}/activity")
        val = get_json(f"{base}/validate")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

        ok = (n_nodes >= 1 and n_edges >= 1
              and isinstance(act.get("by_date"), dict)
              and "ok" in val and "total_notas" in val and "problemas" in val)
        if ok:
            print(f"PASS: /graph={n_nodes}n/{n_edges}e, /activity ok, /validate ok (problemas={len(val['problemas'])})")
            return 0
        print(f"FAIL: graph={n_nodes}/{n_edges} activity={act} validate={val}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
