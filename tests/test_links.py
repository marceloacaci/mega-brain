#!/usr/bin/env python3
"""Testes de unidade para backlinks.links (S20 — links de saida de uma nota).

Verifica: resolve alias/heading/pasta, ignora codigo/placeholder, nao conta
auto-link, marca alvo inexistente como nao-resolvido, e a versao cacheada
(miss->hit->invalida). Anti-tautologia: reverter a resolucao faz o teste
falhar no assert de `resolved`/conta.
"""
import os
import sys
import time
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS"))

from backlinks import links, links_cached  # noqa: E402

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
    d = tempfile.mkdtemp(prefix="mb_links_")
    with open(os.path.join(d, "A.md"), "w", encoding="utf-8") as fh:
        fh.write("# A\nVeja [[B]] e [[C|apelido de C]].\n`[[B]]` em codigo nao conta.\n")
    with open(os.path.join(d, "B.md"), "w", encoding="utf-8") as fh:
        fh.write("# B\n")
    os.makedirs(os.path.join(d, "30_PROJECTS", "Proj"), exist_ok=True)
    with open(os.path.join(d, "30_PROJECTS", "Proj", "C.md"), "w", encoding="utf-8") as fh:
        fh.write("# Titulo C\n")
    with open(os.path.join(d, "D.md"), "w", encoding="utf-8") as fh:
        # link quebrado + placeholder (nao devem resolver)
        fh.write("# D\n[[NotaQueNaoExiste]] e ${nota.placeholder} [[templ]]]\n")
    return d


def main():
    d = _fixture()
    try:
        rep = links(d, "A.md")
        check("path normalizado", rep["path"] == "A.md")
        check("total de links = 2 (B e C; codigo ignorado)", rep["total"] == 2)
        by = {x["target"]: x for x in rep["links"]}
        check("resolve B por stem", by.get("B", {}).get("resolved") is True)
        check("resolve C por pasta/alias (titulo)", by.get("C", {}).get("resolved") is True)
        check("titulo de C veio do frontmatter/H1", by.get("C", {}).get("title") == "Titulo C")
        check("conta repeticao de B (1x, pois 2o esta em codigo)", by.get("B", {}).get("count") == 1)

        repd = links(d, "D.md")
        bd = {x["target"]: x for x in repd["links"]}
        check("link quebrado marcado nao-resolvido", bd.get("NotaQueNaoExiste", {}).get("resolved") is False)
        check("placeholder ${...} nao vira link", "nota.placeholder" not in bd)

        # auto-link: nota que aponta so para si mesma nao gera saida util
        with open(os.path.join(d, "E.md"), "w", encoding="utf-8") as fh:
            fh.write("# E\n[[E]]\n")
        repe = links(d, "E.md")
        check("auto-link nao conta como saida", repe["total"] == 0)

        # cache: miss -> hit -> invalida
        r1, c1 = links_cached(d, "A.md", ttl=30)
        check("links 1o acesso miss", c1 is False)
        check("links cache payload", r1["total"] == 2)
        r2, c2 = links_cached(d, "A.md", ttl=30)
        check("links 2o acesso hit", c2 is True)
        time.sleep(0.01)
        for f in os.listdir(d):
            if f.endswith(".md"):
                os.utime(os.path.join(d, f), (time.time() + 5, time.time() + 5))
        r3, c3 = links_cached(d, "A.md", ttl=30)
        check("links apos tocar .md: miss", c3 is False)
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print(f"\nLINKS-UNIT: {_PASS} pass, {_FAIL} fail")
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
