#!/usr/bin/env python3
"""
MEGA BRAIN — Servidor MCP local (HTTP/JSON, stdlib, sem dependências).

Expõe operações do cofre Obsidian como endpoints JSON:
  GET  /health
  GET  /search?q=TERMO               -> lista de notas que contêm TERMO (com cache TTL)
  GET  /metrics                      -> métricas Prometheus (M3 Observabilidade)
  GET  /validate                     -> validacao continua do vault (M4 Extensibilidade)
  GET  /read?path=NOTE.md            -> conteúdo da nota (relativo ao vault)
  POST /write  {path, content}       -> cria/sobrescreve nota
  POST /append {path, content}       -> anexa conteúdo à nota
  POST /link   {note1, note2}        -> cria [[wikilink]] de note1 -> note2
  POST /tag    {note, tags:[...]}    -> aplica tags (frontmatter ou inline)
  POST /moc    {topic}               -> cria/atualiza MOC em 70_MOCS/

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
import sys
import time
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer

VAULT = r"D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"

# Validacao continua do vault (M4 Extensibilidade)
sys_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
import validate_vault  # noqa: E402

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

def _vault_path(rel):
    return os.path.join(VAULT, rel.strip("/\\"))

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
    fp = _vault_path(rel)
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
            head = head.rstrip() + f"\ntags: []\n"
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
            rep = validate_vault.validate(VAULT)
            with _METRICS_LOCK:
                _METRICS["mcp_requests_total"] += 1
            return self._send(rep)
        if u.path == "/read":
            p = urllib.parse.parse_qs(u.query).get("path", [""])[0]
            c = read_note(p)
            return self._send({"path": p, "content": c} if c is not None
                              else {"error": "not found"}, 404 if c is None else 200)
        if u.path == "/stats":
            # Contagem real de notas .md por pasta-raiz (sem ler o conteúdo).
            total = 0
            by_dir = {}
            for root, _, files in os.walk(VAULT):
                if ".obsidian" in root:
                    continue
                rel_root = os.path.relpath(root, VAULT).replace("\\", "/")
                md = [f for f in files if f.endswith(".md")]
                if md:
                    key = rel_root if rel_root != "." else "(raiz)"
                    # conta apenas a pasta-raiz de 2 níveis (ex.: 10_MEGA_BRAIN)
                    top = key.split("/")[0]
                    by_dir[top] = by_dir.get(top, 0) + len(md)
                    total += len(md)
            with _METRICS_LOCK:
                _METRICS["mcp_requests_total"] += 1
                _METRICS["mcp_notes_total"] = total
            return self._send({"total": total, "by_dir": by_dir})
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
