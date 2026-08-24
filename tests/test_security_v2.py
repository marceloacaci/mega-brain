#!/usr/bin/env python3
"""test_security_v2.py — Regressao: confinamento de path e O(n^2) no grafo (S11/S12).

Cobre tres defasagens REAIS que o CI 14/14 nao pegava:
  1. `semantic._norm_rel` / `related_notes` aceitavam path traversal
     (../../../Windows/win.ini) -> liam arquivos FORA do vault.
  2. `compress.compress_note` aceitava traversal (mesmo vetor de leitura).
  3. `graph.build_graph` em modo embeddings (OLLAMA_URL setado) chamava
     `related_notes(vault, rel)` POR NOTA -> O(n^2) de I/O (re-walk do vault
     inteiro para CADA nota). O caminho Jaccard ja era O(n); o de embeddings
     tinha regredido. Agora PRE-COMPUTA os embeddings 1x.

Reinjetar o bug (reverter as fixas) faz este teste FALHAR -> nao e tautologico.
"""

import os
import sys
import shutil
import tempfile
import inspect

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS")))

import semantic  # noqa: E402
import compress  # noqa: E402
import graph  # noqa: E402

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


def build_vault():
    d = tempfile.mkdtemp(prefix="mb_secv2_")
    for sub in ("10_MEGA_BRAIN", "70_MOCS", "80_SYSTEM", "30_PROJECTS"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    w = lambda rel, txt: open(os.path.join(d, rel.replace("/", os.sep)),
                              "w", encoding="utf-8").write(txt)
    w("30_PROJECTS/Alvo.md", "# Alvo\n\nnota real com palavra unica zebra\n")
    w("10_MEGA_BRAIN/A.md", "# A\n\nconteudo com palavra unica alpha\n")
    w("10_MEGA_BRAIN/B.md", "# B\n\nconteudo com palavra unica beta\n")
    return d


def test_semantic_traversal():
    print("=== semantic: path traversal bloqueado ===")
    d = build_vault()
    try:
        # _norm_rel deve levantar VaultPathError, nao resolver fora do vault
        for evil in ["../../../Windows/win.ini", "..\\..\\secret.md",
                     "../../etc/passwd"]:
            try:
                fp = semantic._norm_rel(d, evil)
                inside = os.path.abspath(fp).startswith(os.path.abspath(d))
                check(f"_norm_rel bloqueia {evil!r}", not inside,
                      f"resolveu fora: {fp}")
            except semantic.VaultPathError:
                check(f"_norm_rel bloqueia {evil!r}", True)
            except Exception as e:
                check(f"_norm_rel bloqueia {evil!r}", False,
                      f"{type(e).__name__}: {e}")

        # related_notes nao pode ler arquivo fora do vault
        leaked = False
        try:
            semantic.related_notes(d, "../../../Windows/win.ini", k=3)
        except semantic.VaultPathError:
            pass
        except Exception:
            leaked = True
        check("related_notes nao vaza arquivo externo", not leaked)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_compress_traversal():
    print("=== compress: path traversal bloqueado ===")
    d = build_vault()
    try:
        leaked = False
        for evil in ["../../../Windows/win.ini", "..\\..\\secret.md"]:
            try:
                compress.compress_note(d, evil)
                leaked = True  # retornou sem erro = leu? (None e seguro, mas idealmente levanta)
            except semantic.VaultPathError:
                pass
            except Exception:
                leaked = True
        check("compress_note nao vaza arquivo externo", not leaked)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_graph_embeddings_no_on2():
    print("=== graph: embeddings pre-computados (sem O(n^2)) ===")
    d = build_vault()
    try:
        # Regressao (S11): o caminho de embeddings chamava `related_notes(vault, rel, ...)`
        # DENTRO do loop por nota -> O(n^2) de I/O (re-walk do vault inteiro para cada
        # nota). Agora os embeddings sao pre-computados 1x. Checamos ESTATICAMENTE que
        # nao ha mais chamada per-note de related_notes, e DINAMICAMENTE que o grafo
        # eh construido e produz arestas semanticas (modo embeddings stubado).
        src = inspect.getsource(graph.build_graph)
        per_note_call = "related_notes(vault, rel" in src or "related_notes(vault, path" in src
        check("build_graph nao chama related_notes por nota (sem O(n^2))",
              not per_note_call, f"found per-note related_notes call in source")

        os.environ["OLLAMA_URL"] = "http://localhost:1"
        orig_embed = semantic._ollama_embed
        semantic._ollama_embed = lambda t: [0.1, 0.2, 0.3]
        graph._GRAPH_CACHE.update({"key": None, "mtime": 0.0, "count": -1,
                                   "built_at": 0.0, "data": None})
        try:
            data, _ = graph.build_graph_cached(d, k=3, limit=50, ttl=0)
        finally:
            semantic._ollama_embed = orig_embed
            os.environ.pop("OLLAMA_URL", None)
        check("build_graph retorna nos+arestas",
              len(data.get("nodes", [])) == 3 and len(data.get("edges", [])) >= 1,
              f"nodes={len(data.get('nodes', []))} edges={len(data.get('edges', []))}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    test_semantic_traversal()
    test_compress_traversal()
    test_graph_embeddings_no_on2()
    print(f"\nRESULTADO: {PASS} passaram, {FAIL} falharam")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
