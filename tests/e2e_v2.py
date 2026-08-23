#!/usr/bin/env python3
"""E2E v2.0 do MEGA BRAIN — inovação (semântica, compressão, swarm, LLM local).

Sobe o MCP num vault fixture e valida as rotas v2.0 no modo FALLBACK (sem Ollama):
  - GET /related  (Jaccard de tokens)
  - GET /suggest  (Jaccard de tokens)
  - GET /compress (compressão por regras)
  - POST /swarm   (5 agentes coordenados)
  - POST /reason  (fallback heurístico)
Nao altera o vault real. Requer Python stdlib. Server resolvido via repo.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
SERVER = os.path.join(REPO, "80_SYSTEM", "SCRIPTS", "mcp_obsidian_server.py")


def get_json(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post_json(url, payload, timeout=30):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def wait_health(base, tries=100, delay=0.3):
    for _ in range(tries):
        try:
            if get_json(f"{base}/health").get("ok"):
                return True
        except Exception:
            pass
        time.sleep(delay)
    return False


def make_fixture(root):
    os.makedirs(os.path.join(root, "10_MEGA_BRAIN"), exist_ok=True)
    os.makedirs(os.path.join(root, "30_PROJECTS", "MeuBolso"), exist_ok=True)
    notes = {
        "10_MEGA_BRAIN/INDEX_GERAL.md": "---\ntipo: meta-indice\n---\n\n# Index\n\n- [[MOC_Parcelas]]\n",
        "30_PROJECTS/MeuBolso/README.md": "# MeuBolso\nApp de financas pessoais com controle de parcelas.\n",
        "30_PROJECTS/MeuBolso/PARCELAS.md": "# Parcelas\nComo corrigir bug de parcela no checkout.\nVeja [[MOC_Parcelas]].\n",
    }
    for rel, content in notes.items():
        with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
            fh.write(content)
    # daily note grande para testar compressao
    daily = "# " + "Daily Note\n" + ("linha repetida de ruido\n" * 5) + "tarefa real de parcela\n[[MOC_Parcelas]]\n#tag\n"
    os.makedirs(os.path.join(root, "20_DAILY_NOTES"), exist_ok=True)
    with open(os.path.join(root, "20_DAILY_NOTES", "2026-08-23.md"), "w", encoding="utf-8") as fh:
        fh.write(daily)


def main():
    print("=== E2E v2.0 (fallback heurístico, sem Ollama) ===")
    results = []
    tmp = tempfile.mkdtemp(prefix="mb_v2_")
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    try:
        make_fixture(tmp)
        proc = subprocess.Popen([sys.executable, SERVER, "--port", str(port), "--vault", tmp],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        base = f"http://127.0.0.1:{port}"
        try:
            if not wait_health(base):
                print("FAIL: server nao subiu;", proc.stderr.read().decode()[:400])
                return 1

            # /related (Jaccard)
            rep = get_json(f"{base}/related?path=30_PROJECTS/MeuBolso/PARCELAS.md&k=3")
            rel_ok = isinstance(rep.get("related"), list) and any(
                "PARCELAS" in r.get("path", "").upper() or r.get("score", 0) > 0 for r in rep["related"])
            results.append(("related_jaccard", rel_ok))
            print(("PASS" if rel_ok else "FAIL"), "related_jaccard", f"(n={len(rep.get('related', []))})")

            # /suggest
            rep = get_json(f"{base}/suggest?q=parcela%20bug&k=3")
            sug_ok = isinstance(rep.get("suggestions"), list) and len(rep["suggestions"]) >= 1
            results.append(("suggest", sug_ok))
            print(("PASS" if sug_ok else "FAIL"), "suggest", f"(n={len(rep.get('suggestions', []))})")

            # /compress (daily note com ruido)
            rep = get_json(f"{base}/compress?path=20_DAILY_NOTES/2026-08-23.md&max_tokens=200")
            comp_ok = (rep.get("tokens_after", 999) < rep.get("tokens_before", 0)) and "tarefa real" in rep.get("compressed", "")
            results.append(("compress", comp_ok))
            print(("PASS" if comp_ok else "FAIL"), "compress",
                  f"(before={rep.get('tokens_before')}, after={rep.get('tokens_after')})")

            # /swarm
            rep = post_json(f"{base}/swarm", {"query": "criar nota sobre parcelas", "agents": None})
            swarm_ok = set(["indexer", "correlator", "guardian", "predictive", "metric"]).issubset(rep.get("agents", {}).keys())
            results.append(("swarm", swarm_ok))
            print(("PASS" if swarm_ok else "FAIL"), "swarm", f"(agents={list(rep.get('agents', {}).keys())})")

            # /reason (fallback heuristico)
            rep = post_json(f"{base}/reason", {"prompt": "como corrigir bug de parcela"})
            reason_ok = rep.get("source") == "heuristic" and "tarefa recebida" in rep.get("response", "").lower()
            results.append(("reason_heuristic", reason_ok))
            print(("PASS" if reason_ok else "FAIL"), "reason_heuristic", f"(source={rep.get('source')})")

        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except Exception: proc.kill()
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
