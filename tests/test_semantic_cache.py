#!/usr/bin/env python3
"""Testes de unidade para semantic.related_cached / suggest_cached (S19).

Verifica o padrao P11-style: 1o acesso = miss, 2o = hit, e invalida ao mexer
num .md (mtime muda). Anti-tautologia: reverter o cache (sempre miss) faz o
teste FALHAR no assert de `cached=True` no 2o acesso.
"""
import os
import sys
import time
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS"))

from semantic import related_cached, suggest_cached  # noqa: E402

_PASS = 0
_FAIL = 0


def check(name, cond):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  PASS {name}")
    else:
        _FAIL += 1
        print(f"  FAIL {name}")


def _fixture():
    """Cria vault temp com 3 notas linkadas para exercitar related/suggest."""
    d = tempfile.mkdtemp(prefix="mb_semcache_")
    with open(os.path.join(d, "A.md"), "w", encoding="utf-8") as fh:
        fh.write("# A\nPython automacao de tarefas diarias.\n")
    with open(os.path.join(d, "B.md"), "w", encoding="utf-8") as fh:
        fh.write("# B\nPython scripting para integracao de dados.\n")
    with open(os.path.join(d, "C.md"), "w", encoding="utf-8") as fh:
        fh.write("# C\nReceita de bolo de chocolate.\n")
    return d


def main():
    d = _fixture()
    try:
        # related: 1o acesso miss, 2o hit, toque invalida
        rel1, c1 = related_cached(d, "A.md", k=2, ttl=30)
        check("related 1o acesso e miss", c1 is False)
        check("related retorna lista", isinstance(rel1, list) and len(rel1) >= 1)
        check("related ordena por score (B mais proximo)", rel1[0]["path"] == "B.md")
        rel2, c2 = related_cached(d, "A.md", k=2, ttl=30)
        check("related 2o acesso e hit", c2 is True)
        check("related hit mantem payload", len(rel2) == len(rel1))

        # alteracao de mtime -> proximo acesso miss
        time.sleep(0.01)
        for f in os.listdir(d):
            if f.endswith(".md"):
                os.utime(os.path.join(d, f), (time.time() + 5, time.time() + 5))
        rel3, c3 = related_cached(d, "A.md", k=2, ttl=30)
        check("related apos tocar .md: miss", c3 is False)

        # ttl=0 forca miss
        rel4, c4 = related_cached(d, "A.md", k=2, ttl=0)
        check("related ttl=0 forca miss", c4 is False)

        # suggest: padrao analogo
        s1, sc1 = suggest_cached(d, "python automacao", k=2, ttl=30)
        check("suggest 1o acesso e miss", sc1 is False)
        check("suggest retorna lista", isinstance(s1, list) and len(s1) >= 1)
        s2, sc2 = suggest_cached(d, "python automacao", k=2, ttl=30)
        check("suggest 2o acesso e hit", sc2 is True)

        time.sleep(0.01)
        for f in os.listdir(d):
            if f.endswith(".md"):
                os.utime(os.path.join(d, f), (time.time() + 5, time.time() + 5))
        s3, sc3 = suggest_cached(d, "python automacao", k=2, ttl=30)
        check("suggest apos tocar .md: miss", sc3 is False)

        # chaves distintas (query/path diferente) -> caches separados
        sX, _ = suggest_cached(d, "receita bolo", k=2, ttl=30)
        check("suggest query diferente da outra lista (C topa)", sX[0]["path"] == "C.md")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print(f"\nSEMANTIC-CACHE: {_PASS} pass, {_FAIL} fail")
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
