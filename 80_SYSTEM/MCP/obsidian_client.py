"""Cliente HTTP para o servidor MCP do Mega Brain (mcp_obsidian_server.py).

Usa só a biblioteca padrão (urllib), então roda em qualquer Python 3.
Endpoints espelhados do servidor:
  GET  /health
  GET  /search?q=
  GET  /read?path=
  POST /write  {path, content}
  POST /append {path, content}
  POST /link   {note1, note2}
  POST /tag    {note, tags:[...]}
  POST /moc    {topic}
"""
import json
import urllib.parse
import urllib.request

from config import load_config


def _url(endpoint, params=None):
    base = load_config()["mcp_server_url"].rstrip("/") + endpoint
    # força IPv4 para evitar timeout por resolver 'localhost'->IPv6 (server soh ouve 127.0.0.1)
    base = base.replace("localhost", "127.0.0.1")
    if params:
        base += "?" + urllib.parse.urlencode(params)
    return base


def _get(endpoint, params=None):
    try:
        with urllib.request.urlopen(_url(endpoint, params), timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def _post(endpoint, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _url(endpoint), data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def health():
    return _get("/health")


def search(q):
    return _get("/search", {"q": q})


def read(path):
    return _get("/read", {"path": path})


def write(path, content):
    return _post("/write", {"path": path, "content": content})


def append(path, content):
    return _post("/append", {"path": path, "content": content})


def link(note1, note2):
    return _post("/link", {"note1": note1, "note2": note2})


def tag(note, tags):
    return _post("/tag", {"note": note, "tags": tags})


def moc(topic):
    return _post("/moc", {"topic": topic})


if __name__ == "__main__":
    print(json.dumps(health(), ensure_ascii=False, indent=2))
