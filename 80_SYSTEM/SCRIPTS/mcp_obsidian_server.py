#!/usr/bin/env python3
"""
MEGA BRAIN — Servidor MCP local (HTTP/JSON, stdlib, sem dependências).

Expõe operações do cofre Obsidian como endpoints JSON:
  GET  /health
  GET  /search?q=TERMO               -> lista de notas que contêm TERMO (com cache TTL)
  GET  /metrics                      -> métricas Prometheus (M3 Observabilidade)
  GET  /validate                     -> validacao continua do vault (M4 Extensibilidade)
  GET  /recent?limit=N&days=D         -> notas modificadas mais recentemente (utilitário)
  GET  /related?path=P&k=5           -> notas relacionadas (v2.0 semântica, fallback Jaccard)
  GET  /suggest?q=Q&k=5              -> sugestão de notas por query (v2.0)
  GET  /compress?path=P&max_tokens=N -> compressão de contexto (v2.0)
  GET  /read?path=NOTE.md            -> conteúdo da nota (relativo ao vault)
  POST /write  {path, content}       -> cria/sobrescreve nota
  POST /append {path, content}       -> anexa conteúdo à nota
  POST /link   {note1, note2}        -> cria [[wikilink]] de note1 -> note2
  POST /tag    {note, tags:[...]}    -> aplica tags (frontmatter ou inline)
  POST /moc    {topic}               -> cria/atualiza MOC em 70_MOCS/
  POST /swarm  {query, agents?}      -> Multi-Agent Swarm (v2.0)
  POST /reason {prompt}              -> LLM local Ollama (v2.0, fallback heurístico)

Cache de /search: TTL em memória (padrão) ou Redis se REDIS_URL estiver setado
e a lib `redis` estiver instalada. Sempre há fallback funcional.

Uso:
  python mcp_obsidian_server.py [--port 8770] [--vault "CAMINHO"]
  Teste: curl http://localhost:8770/health
         curl http://localhost:8770/metrics
"""
import argparse
import json
import os
import re
import sys
import time
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer

# VAULT default portatil: prefere env MEGABRAIN_VAULT; senao o diretorio pai do
# repo (este script vive em 80_SYSTEM/SCRIPTS, o vault e o repo raiz). Nao usa
# caminho hardcoded do dev (anti-padrao P3/P5 — quebrava no runner Linux do CI).
VAULT_DEFAULT = os.environ.get("MEGABRAIN_VAULT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
VAULT = VAULT_DEFAULT

# Validacao continua do vault (M4 Extensibilidade)
sys_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
import validate_vault  # noqa: E402
from validate_vault import validate_cached  # noqa: E402
from vault_stats import count_by_dir, count_by_dir_cached  # noqa: E402

# ---------------------------------------------------------------------------
# v2.0 — Inovação: semântica, compressão, swarm e LLM local (todos opcionais,
# com fallback heurístico quando Ollama/embeddings não estão disponíveis).
# ---------------------------------------------------------------------------
from semantic import related_notes, suggest, related_cached, suggest_cached  # noqa: E402
from compress import compress_text, compress_note  # noqa: E402
from swarm import run_swarm  # noqa: E402
from llm_local import reason  # noqa: E402
from graph import build_graph_cached  # noqa: E402
from recent import recent_notes, recent_notes_cached  # noqa: E402
from activity import activity_cached  # noqa: E402
from tags import tag_counts, tag_counts_cached  # noqa: E402
from backlinks import backlinks, backlinks_cached, orphans_in_cached, links_cached  # noqa: E402

# ---------------------------------------------------------------------------
# Observabilidade (Sprint 5 / M3): metricas + cache de /search (TTL).
# ---------------------------------------------------------------------------
# Métricas no formato Prometheus (contadores/counters incrementais).
_METRICS = {
    "mcp_requests_total": 0,
    "mcp_search_total": 0,
    "mcp_search_latency_ms_sum": 0.0,
    "mcp_search_cache_hits": 0,
    "mcp_search_cache_miss": 0,
    "mcp_notes_total": 0,
}
_METRICS_LOCK = threading.Lock()

# Cache em memória (fallback sempre disponível). Redis é opcional.
_CACHE = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = float(os.environ.get("REDIS_TTL_SECONDS", "300"))

def _try_redis():
    """Retorna cliente redis se REDIS_URL estiver setado E a lib existir."""
    url = os.environ.get("REDIS_URL", "")
    if not url:
        return None
    try:
        import redis  # dependencia opcional
        return redis.from_url(url)
    except Exception:
        return None

_REDIS = _try_redis()

def _cache_get(q):
    if _REDIS is not None:
        try:
            v = _REDIS.get("mb_cache:" + q)
            if v is not None:
                return json.loads(v)
        except Exception:
            pass
    with _CACHE_LOCK:
        if q in _CACHE:
            ts, val = _CACHE[q]
            if time.time() - ts < _CACHE_TTL:
                return val
            del _CACHE[q]
    return None

def _cache_put(q, val):
    if _REDIS is not None:
        try:
            _REDIS.setex("mb_cache:" + q, int(_CACHE_TTL), json.dumps(val))
        except Exception:
            pass
    with _CACHE_LOCK:
        _CACHE[q] = (time.time(), val)

def _record_search(latency_ms, cache_hit):
    with _METRICS_LOCK:
        _METRICS["mcp_search_total"] += 1
        _METRICS["mcp_search_latency_ms_sum"] += latency_ms
        if cache_hit:
            _METRICS["mcp_search_cache_hits"] += 1
        else:
            _METRICS["mcp_search_cache_miss"] += 1

def _metrics_text():
    lines = []
    with _METRICS_LOCK:
        for k, v in _METRICS.items():
            lines.append(f"# TYPE {k} counter")
            lines.append(f"{k} {v}")
    lines.append("# TYPE mcp_cache_backend gauge")
    lines.append(f"mcp_cache_backend {{backend=\"{'redis' if _REDIS else 'memory'}\"}} 1")
    with _CACHE_LOCK:
        lines.append("# TYPE mcp_cache_entries gauge")
        lines.append(f"mcp_cache_entries {len(_CACHE)}")
    return "\n".join(lines) + "\n"

# Guard de path compartilhado (vault_path.py). As rotas de escrita (/write etc.)
# capturam VaultPathError -> 400; as de leitura (/read) -> 404 (see do_GET/do_POST).
# Mantemos o NOME 'VaultPathError' neste namespace porque o handler verifica
# `type(e).__name__ == "VaultPathError"` (contrato de teste e2e_security).
from vault_path import vault_path as _vault_path_impl, VaultPathError  # noqa: E402


def _vault_path(rel):
    """Resolve `rel` DENTRO do vault (usa o VAULT corrente), recusando traversal."""
    return _vault_path_impl(VAULT, rel)

def search(q):
    q = q.lower()
    hits = []
    for root, _, files in os.walk(VAULT):
        if ".obsidian" in root:
            continue
        for f in files:
            if f.endswith(".md"):
                fp = os.path.join(root, f)
                try:
                    with open(fp, encoding="utf-8", errors="ignore") as fh:
                        txt = fh.read()
                    if q in txt.lower():
                        rel = os.path.relpath(fp, VAULT).replace("\\", "/")
                        hits.append({"path": rel,
                                     "ctx": next((l.strip() for l in txt.splitlines()
                                                  if q in l.lower()), "")[:120]})
                except Exception:
                    pass
    return hits

def cached_search(q):
    """/search com cache (Redis opcional, fallback memória). Mede latência."""
    t0 = time.time()
    cached = _cache_get(q)
    if cached is not None:
        _record_search((time.time() - t0) * 1000, cache_hit=True)
        return cached
    res = search(q)
    _cache_put(q, res)
    _record_search((time.time() - t0) * 1000, cache_hit=False)
    return res

def read_note(rel):
    try:
        fp = _vault_path(rel)
    except VaultPathError:
        return None
    if not os.path.exists(fp):
        return None
    with open(fp, encoding="utf-8") as fh:
        return fh.read()

def write_note(rel, content, mode="w"):
    fp = _vault_path(rel)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, mode, encoding="utf-8") as fh:
        fh.write(content)
    return os.path.relpath(fp, VAULT).replace("\\", "/")

def link(note1, note2):
    name2 = os.path.splitext(os.path.basename(note2))[0]
    content = read_note(note1) or ""
    wl = f"[[{name2}]]"
    if wl not in content:
        content = (content.rstrip() + "\n\n" + wl + "\n")
        write_note(note1, content)
    return True

def tag(note, tags):
    content = read_note(note) or ""
    if content.startswith("---"):
        # frontmatter exists: inject into tags line
        idx = content.find("---", 3)
        head = content[:idx+3]
        body = content[idx+3:]
        if "tags:" in head:
            for t in tags:
                if t not in head:
                    head = head.rstrip() + f"\n  - {t}\n"
        else:
            # frontmatter exists but has NO tags key: inject `tags: [..]` with
            # the requested tags. Previously this branch created `tags: []` and
            # silently DROPPED every requested tag (latent defect).
            head = head.rstrip() + "\ntags: [" + ", ".join(tags) + "]\n"
        content = head + body
    else:
        tags_line = "tags: [" + ", ".join(tags) + "]\n"
        content = "---\n" + tags_line + "---\n\n" + content
    write_note(note, content)
    return True

def moc(topic):
    rel = f"70_MOCS/MOC_{topic}.md"
    name = f"MOC_{topic}"
    content = read_note(rel) or (
        f"---\ntipo: moc\ntags: [moc, {topic.lower()}]\n---\n\n# {name}\n\n"
        f"Mapa de conteúdo para **{topic}**.\n\n## Tópicos\n- \n\n"
        f"## Conexões\n- [[INDEX_GERAL]]\n")
    if "## Conexões" not in content:
        content += "\n## Conexões\n- [[INDEX_GERAL]]\n"
    return write_note(rel, content)

def rename_note(rel, new_name):
    """Renomeia um arquivo .md preservando o diretório e o conteúdo.
    new_name pode vir com ou sem extensão (.md é garantido)."""
    fp = _vault_path(rel)
    if not os.path.exists(fp):
        return None
    if not new_name.lower().endswith(".md"):
        new_name += ".md"
    new_fp = os.path.join(os.path.dirname(fp), new_name)
    if os.path.abspath(new_fp) == os.path.abspath(fp):
        return rel  # mesmo nome, nada a fazer
    if os.path.exists(new_fp):
        return None  # destino já existe: evita sobrescrever
    os.rename(fp, new_fp)
    return os.path.relpath(new_fp, VAULT).replace("\\", "/")

def move_note(rel, new_dir):
    """Move um arquivo .md para new_dir (relativo ao vault), preservando o nome."""
    fp = _vault_path(rel)
    if not os.path.exists(fp):
        return None
    dest_dir = _vault_path(new_dir)
    os.makedirs(dest_dir, exist_ok=True)
    new_fp = os.path.join(dest_dir, os.path.basename(fp))
    if os.path.exists(new_fp):
        return None  # destino já existe: evita sobrescrever
    os.rename(fp, new_fp)
    return os.path.relpath(new_fp, VAULT).replace("\\", "/")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silencioso

    def _send(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_metrics(self):
        with _METRICS_LOCK:
            _METRICS["mcp_requests_total"] += 1
        body = _metrics_text().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # Responde ao preflight CORS (necessário para POST cross-origin a partir
        # de páginas web servidas noutra origem, ex.: localhost:8800 -> :8770).
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            return self._do_get()
        except Exception as e:  # P8: nunca derruba a conexao; retorna 500 legivel
            try:
                return self._send({"error": f"unhandled GET error: {e}"}, 500)
            except Exception:
                pass

    def _do_get(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/health":
            return self._send({"ok": True, "vault": VAULT})
        if u.path == "/search":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            return self._send({"query": q, "hits": cached_search(q),
                               "cache": "redis" if _REDIS else "memory"})
        if u.path == "/metrics":
            return self._send_metrics()
        if u.path == "/validate":
            try:
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                # P11-style cache: evita re-varrer o vault a cada poll do dashboard.
                rep, was_cached = validate_cached(VAULT, ttl=_CACHE_TTL)
                rep = dict(rep)
                rep["cached"] = was_cached
                return self._send(rep)
            except Exception as e:
                return self._send({"error": f"validate failed: {e}"}, 500)
        if u.path == "/read":
            p = urllib.parse.parse_qs(u.query).get("path", [""])[0]
            c = read_note(p)
            return self._send({"path": p, "content": c} if c is not None
                              else {"error": "not found"}, 404 if c is None else 200)
        if u.path == "/stats":
            # Contagem real de notas .md por pasta-raiz (sem ler o conteúdo).
            # Reusa vault_stats.count_by_dir_cached (P11-style: evita re-varredura
            # a cada poll do dashboard; invalida por mtime do vault ou TTL).
            (total, by_dir), was_cached = count_by_dir_cached(VAULT, ttl=_CACHE_TTL)
            with _METRICS_LOCK:
                _METRICS["mcp_requests_total"] += 1
                _METRICS["mcp_notes_total"] = total
            return self._send({"total": total, "by_dir": by_dir, "cached": was_cached})
        if u.path == "/recent":
            # Notas modificadas mais recentemente (utilitário somente-leitura).
            try:
                try:
                    lim = int(urllib.parse.parse_qs(u.query).get("limit", ["10"])[0])
                except ValueError:
                    lim = 10
                cd = urllib.parse.parse_qs(u.query).get("days", [""])[0]
                cutoff = float(cd) if cd else None
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                # usa cache por mtime/TTL (P11-style) p/ evitar re-varredura a cada poll
                data, was_cached = recent_notes_cached(VAULT, limit=lim, cutoff_days=cutoff, ttl=_CACHE_TTL)
                return self._send({"recent": data, "cached": was_cached})
            except Exception as e:
                return self._send({"error": f"recent failed: {e}"}, 500)
        if u.path == "/tags":
            # Nuvem de tags: contagem de tags (frontmatter + inline) do vault.
            try:
                try:
                    tl = int(urllib.parse.parse_qs(u.query).get("limit", ["20"])[0])
                except ValueError:
                    tl = 20
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                # cache por mtime/TTL (P11-style) p/ evitar re-varredura a cada poll
                data, was_cached = tag_counts_cached(VAULT, limit=tl)
                return self._send({"tags": data, "cached": was_cached})
            except Exception as e:
                return self._send({"error": f"tags failed: {e}"}, 500)
        if u.path == "/orphans-in":
            # S17-B: notas que NINGUEM linka (orfas de entrada). Uma passada O(n).
            try:
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                data, was_cached = orphans_in_cached(VAULT, ttl=_CACHE_TTL)
                data["cached"] = was_cached
                return self._send(data)
            except Exception as e:
                return self._send({"error": f"orphans-in failed: {e}"}, 500)
        if u.path == "/backlinks":
            # S17: quem aponta para esta nota (vizinhanca de entrada, sem grafo inteiro).
            try:
                qp = urllib.parse.parse_qs(u.query)
                rel = qp.get("path", [""])[0]
                if not rel:
                    return self._send({"error": "parametro 'path' obrigatorio"}, 400)
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                data, was_cached = backlinks_cached(VAULT, rel, ttl=_CACHE_TTL)
                data["cached"] = was_cached
                return self._send(data)
            except FileNotFoundError:
                return self._send({"error": "nota nao encontrada"}, 404)
            except Exception as e:
                # traversal -> 400 (igual as demais rotas com path do usuario)
                if type(e).__name__ == "VaultPathError":
                    return self._send({"error": f"path invalido: {e}"}, 400)
                return self._send({"error": f"backlinks failed: {e}"}, 500)
        if u.path == "/links":
            # S20: links de SAIDA da nota (complemento simetrico dos backlinks).
            try:
                qp = urllib.parse.parse_qs(u.query)
                rel = qp.get("path", [""])[0]
                if not rel:
                    return self._send({"error": "parametro 'path' obrigatorio"}, 400)
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                data, was_cached = links_cached(VAULT, rel, ttl=_CACHE_TTL)
                data["cached"] = was_cached
                return self._send(data)
            except FileNotFoundError:
                return self._send({"error": "nota nao encontrada"}, 404)
            except Exception as e:
                if type(e).__name__ == "VaultPathError":
                    return self._send({"error": f"path invalido: {e}"}, 400)
                return self._send({"error": f"links failed: {e}"}, 500)
        if u.path == "/activity":
            # Heatmap de atividade: conta notas diarias (20_DAILY_NOTES) por data.
            # S22: cache por mtime/TTL (padrao S14/S15) evita re-varredura a cada poll.
            try:
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                (daily_dir, by_date), was_cached = activity_cached(VAULT, ttl=_CACHE_TTL)
                return self._send({"daily_dir": daily_dir, "by_date": by_date,
                                   "cached": was_cached})
            except Exception as e:
                return self._send({"error": f"activity failed: {e}"}, 500)
        # ---- v2.0 rotas de inovação (com fallback heurístico) ----
        if u.path == "/related":
            try:
                p = urllib.parse.parse_qs(u.query).get("path", [""])[0]
                k = int(urllib.parse.parse_qs(u.query).get("k", ["5"])[0])
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                # S19: cache por mtime/TTL (padrao S14/S15) evita re-varredura do vault.
                data, was_cached = related_cached(VAULT, p, k=k, ttl=_CACHE_TTL)
                out = {"path": p, "related": data, "cached": was_cached}
                return self._send(out)
            except Exception as e:
                # traversal (semantic.VaultPathError) -> 400, igual às rotas de escrita
                if type(e).__name__ == "VaultPathError":
                    return self._send({"error": f"path invalido: {e}"}, 400)
                return self._send({"error": f"related failed: {e}"}, 500)
        if u.path == "/suggest":
            try:
                q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
                k = int(urllib.parse.parse_qs(u.query).get("k", ["5"])[0])
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                # S19: cache por mtime/TTL (padrao S14/S15).
                data, was_cached = suggest_cached(VAULT, q, k=k, ttl=_CACHE_TTL)
                out = {"query": q, "suggestions": data, "cached": was_cached}
                return self._send(out)
            except Exception as e:
                return self._send({"error": f"suggest failed: {e}"}, 500)
        if u.path == "/compress":
            try:
                p = urllib.parse.parse_qs(u.query).get("path", [""])[0]
                max_t = int(urllib.parse.parse_qs(u.query).get("max_tokens", ["2000"])[0])
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                rep = compress_note(VAULT, p, max_tokens=max_t)
                return self._send(rep if rep else {"error": "not found"}, 404 if not rep else 200)
            except Exception as e:
                # traversal (semantic.VaultPathError) -> 400, igual às rotas de escrita
                if type(e).__name__ == "VaultPathError":
                    return self._send({"error": f"path invalido: {e}"}, 400)
                return self._send({"error": f"compress failed: {e}"}, 500)
        if u.path == "/graph":
            try:
                k = int(urllib.parse.parse_qs(u.query).get("k", ["3"])[0])
                limit = int(urllib.parse.parse_qs(u.query).get("limit", ["600"])[0])
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                # P11: usa cache por mtime p/ evitar O(n^2) Jaccard repetido.
                data, was_cached = build_graph_cached(VAULT, k=k, limit=limit, ttl=_CACHE_TTL)
                data = dict(data)
                data["cached"] = was_cached
                return self._send(data)
            except Exception as e:
                return self._send({"error": f"graph failed: {e}"}, 500)
        self._send({"error": "unknown endpoint"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return self._send({"error": "bad json"}, 400)
        u = urllib.parse.urlparse(self.path)
        try:
            if u.path == "/write":
                return self._send({"written": write_note(data["path"], data["content"])})
            if u.path == "/append":
                return self._send({"appended": write_note(data["path"], "\n" + data["content"], "a")})
            if u.path == "/link":
                return self._send({"linked": link(data["note1"], data["note2"])})
            if u.path == "/tag":
                return self._send({"tagged": tag(data["note"], data.get("tags", []))})
            if u.path == "/moc":
                return self._send({"moc": moc(data["topic"])})
            if u.path == "/rename":
                new = rename_note(data["path"], data["new_name"])
                return self._send({"renamed": new} if new is not None
                                  else {"error": "not found"}, 404 if new is None else 200)
            if u.path == "/move":
                new = move_note(data["path"], data["new_dir"])
                return self._send({"moved": new} if new is not None
                                  else {"error": "not found"}, 404 if new is None else 200)
            # ---- v2.0 ----
            if u.path == "/swarm":
                agents = data.get("agents")
                result = run_swarm(VAULT, data.get("query", ""), agents=agents)
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                return self._send(result)
            if u.path == "/reason":
                result = reason(data.get("prompt", ""), vault=VAULT)
                with _METRICS_LOCK:
                    _METRICS["mcp_requests_total"] += 1
                return self._send(result)
        except VaultPathError as e:
            # Endurecimento: path traversal em rotas de escrita -> 400, nunca 500
            return self._send({"error": f"path invalido: {e}"}, 400)
        except Exception as e:
            return self._send({"error": f"server error: {e}"}, 500)
        self._send({"error": "unknown endpoint"}, 404)

def main():
    global VAULT, _CACHE_TTL, _REDIS
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("MCP_PORT", "8770")))
    ap.add_argument("--vault", default=VAULT)
    ap.add_argument("--host", default=os.environ.get("MCP_HOST", "127.0.0.1"))
    args = ap.parse_args()
    VAULT = args.vault
    # TTL de cache e Redis podem vir de env (docker-compose os injeta).
    try:
        _CACHE_TTL = float(os.environ.get("REDIS_TTL_SECONDS", _CACHE_TTL))
    except Exception:
        pass
    _REDIS = _try_redis()
    print(f"[MEGA BRAIN MCP] ouvindo em http://{args.host}:{args.port}")
    print(f"[MEGA BRAIN MCP] vault: {VAULT}")
    print(f"[MEGA BRAIN MCP] cache: {'redis' if _REDIS else 'memory'} (ttl={_CACHE_TTL:.0f}s)")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()

if __name__ == "__main__":
    main()
