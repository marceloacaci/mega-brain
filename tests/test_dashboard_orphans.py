#!/usr/bin/env python3
"""test_dashboard_orphans.py — Regressão: painel de Órfãos usa wikilinks (FCS/S10-D).

O painel "Notas Órfãs" do dashboard.html deve listar notas SEM wikilink de/para
outras notas. Arestas 'semantic' (Jaccard/embeddings) conectam quase tudo por
sobreposição de tokens, entao contar o grau TOTAL deixaria o painel sempre vazio
(0 orfãos). A correcao (2026-08-24): renderOrphans conta apenas arestas
kind=='wikilink'.

Este teste EXTRAI a função renderOrphans DO dashboard.html (nao reimplementa) e
a executa contra um grafo fixture com um nó órfão estrutural, usando um stub
mínimo de DOM ($). Trava o comportamento real do browser sem precisar de FCS.

Reinjetar o bug (contar grau total) faz o teste FALHAR -> nao tautologico.
"""

import os
import re
import sys
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.abspath(os.path.join(HERE, "..", "web", "dashboard.html"))

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print("  PASS: " + name)
    else:
        FAIL += 1
        print("  FAIL: " + name + " " + detail)


def extract_render_orphans(html):
    m = re.search(r"function renderOrphans\(g\)\s*\{(.*?)\n    \}", html, re.DOTALL)
    if not m:
        return None
    return "function renderOrphans(g){" + m.group(1) + "\n    }"


def run_render_orphans(js_fn, graph):
    """Executa a função REAL do dashboard via node (JS de verdade), com stub de DOM."""
    harness = js_fn + "\n"
    harness += "const _el = { innerHTML: '' };\n"
    harness += "const $ = (sel) => _el;\n"
    harness += "global.GRAPH = null;\n"
    harness += "renderOrphans(" + json_dumps(graph) + ");\n"
    harness += "console.log(_el.innerHTML);\n"
    with open(os.path.join(tempfile.gettempdir(), "dash_orphan_test.js"), "w", encoding="utf-8") as f:
        f.write(harness)
    out = subprocess.run(["node", f.name], capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(out.stderr)
    return out.stdout


def json_dumps(obj):
    import json
    return json.dumps(obj, ensure_ascii=False)


def main():
    print("=== Unidade: dashboard.renderOrphans (orfãos por wikilink) ===")
    if not os.path.exists(DASHBOARD):
        check("dashboard.html existe", False)
        return 1
    html = open(DASHBOARD, encoding="utf-8").read()
    fn = extract_render_orphans(html)
    check("renderOrphans extraída do dashboard.html", fn is not None)
    if fn is None:
        return 1

    # Grafo fixture: A<->B por wikilink, C orfão estrutural (só arestas semantic).
    graph = {
        "nodes": [
            {"id": "A.md", "label": "A"},
            {"id": "B.md", "label": "B"},
            {"id": "C.md", "label": "Orfao"},
        ],
        "edges": [
            {"source": "A.md", "target": "B.md", "kind": "wikilink"},
            {"source": "A.md", "target": "C.md", "kind": "semantic"},
            {"source": "B.md", "target": "C.md", "kind": "semantic"},
        ],
    }
    out = run_render_orphans(fn, graph)
    check("órfão estrutural 'Orfao' listado", "Orfao" in out, "got=" + repr(out))
    check("nós conectados por wikilink NÃO listados",
          ("A" not in out) and ("B" not in out), "got=" + repr(out))

    # Prova anti-tautologia: reverter p/ grau total (contar todas as arestas) deve
    # fazer 'Orfao' (grau 2 por semantic) SUMIR dos órfãos.
    buggy = fn.replace("if(e.kind==='wikilink'){ if(deg[e.source]!==undefined)deg[e.source]++; if(deg[e.target]!==undefined)deg[e.target]++; }",
                       "if(deg[e.source]!==undefined)deg[e.source]++; if(deg[e.target]!==undefined)deg[e.target]++;")
    if buggy != fn:
        out_buggy = run_render_orphans(buggy, graph)
        check("reverter p/ grau total REMOVE o órfão (prova não-tautologia)",
              "Orfao" not in out_buggy, "buggy_out=" + repr(out_buggy))
    else:
        # se a substituição não casou, pelo menos confirma que o fixo lista Orfao
        check("patch de reverso casou", False, "substituicao nao casou")

    print("\nRESULTADO: %d passaram, %d falharam" % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
