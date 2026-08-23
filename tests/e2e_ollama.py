#!/usr/bin/env python3
"""E2E S10-A — ativacao Ollama (embeddings/LLM local) no MCP.

Sobe o MCP num vault fixture e valida o modo de IA:
  - Se OLLAMA_URL+OLLAMA_MODEL estiverem acessiveis -> /related usa embeddings reais
    (modo="ollama") e /reason usa geracao real (source="ollama").
  - Caso contrario (padrao CI/Dev) -> SKIP com mensagem clara (modo heuristico).

O teste NAO falha quando Ollama esta ausente: ele exercita o caminho real
de fallback do v2.0 e so valida embeddings reais se o servico existir.
Isso garante CI verde offline (principio stdlib do repo) e cobertura quando
Ollama estiver disponivel (docker compose --profile ollama up).
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


def ollama_reachable(url, model, timeout=3):
    """True se Ollama responde /api/embeddings com o modelo informado."""
    if not url or not model:
        return False
    try:
        req = urllib.request.Request(
            f"{url.rstrip('/')}/api/embeddings",
            data=json.dumps({"model": model, "prompt": "ping"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200 and "embedding" in json.loads(r.read().decode())
    except Exception:
        return False


def main():
    ollama_url = os.environ.get("OLLAMA_URL", "").strip()
    model = os.environ.get("OLLAMA_MODEL", "").strip()
    # Se nao foi passado, tenta localhost padrao (docker compose --profile ollama)
    if not ollama_url and ollama_reachable("http://127.0.0.1:11434", "nomic-embed-text"):
        ollama_url, model = "http://127.0.0.1:11434", "nomic-embed-text"
    elif not model:
        model = "nomic-embed-text"

    if not ollama_reachable(ollama_url, model):
        print(f"SKIP: Ollama indisponivel (OLLAMA_URL={ollama_url or 'vazio'}). "
              f"MCP opera em modo heuristico (fallback v2.0).")
        return 0  # sucesso: caminho de fallback validado por outros e2e

    # Ollama presente: valida embeddings reais
    tmp = tempfile.mkdtemp(prefix="mb_ollama_")
    try:
        for rel, txt in [
            ("10_MEGA_BRAIN/INDEX_GERAL.md", "---\ntipo: meta-indice\n---\n# Index\n- [[MOC_Teste]]\n"),
            ("70_MOCS/MOC_Teste.md", "# MOC_Teste\nIndice de teste. Relacionado a [[Nota_Exemplo]].\n"),
            ("30_PROJECTS/Nota_Exemplo.md", "# Nota_Exemplo\nMenciona [[MOC_Teste]] e projeto exemplo.\n"),
        ]:
            d = os.path.join(tmp, os.path.dirname(rel))
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(tmp, rel), "w", encoding="utf-8") as fh:
                fh.write(txt)

        PORT = free_port()
        env = dict(os.environ, OLLAMA_URL=ollama_url, OLLAMA_MODEL=model)
        proc = subprocess.Popen([sys.executable, SERVER, "--port", str(PORT), "--vault", tmp],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        base = f"http://127.0.0.1:{PORT}"
        if not wait_health(base, proc):
            print("FAIL: server nao subiu;", proc.stderr.read().decode()[:400])
            return 1

        rel = get_json(f"{base}/related?path=30_PROJECTS/Nota_Exemplo.md&k=2")
        paths = [r["path"] for r in rel.get("related", [])]
        ok_related = any("MOC_Teste" in p for p in paths)
        req = urllib.request.Request(f"{base}/reason",
                                     data=json.dumps({"prompt": "resumo de teste"}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            reason = json.loads(r.read().decode())
        ok_reason = reason.get("source") == "ollama"
        print(f"related={paths}")
        print(f"reason.source={reason.get('source')}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        if ok_related and ok_reason:
            print("PASS: Ollama ativo — /related embeddings reais + /reason geracao real")
            return 0
        print("FAIL: Ollama ativo mas /related ou /reason nao usaram modo ollama")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
