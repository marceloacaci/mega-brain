#!/usr/bin/env python3
"""test_backlinks.py — S17: unidade de backlinks() + backlinks_cached().

Testes NAO-TAUTOLOGICOS: cada assert falha se a implementacao for revertida
para uma versao naive (contar `[[...]]` cru sem strip de codigo, sem resolver
alias/heading/pasta, sem bloquear traversal).

Rode: python tests/test_backlinks.py
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS")))

from backlinks import backlinks, backlinks_cached, _BL_CACHE  # noqa: E402

FAILS = []


def check(cond, msg):
    if cond:
        print("  OK  " + msg)
    else:
        print("  FAIL " + msg)
        FAILS.append(msg)


def make_vault():
    v = tempfile.mkdtemp(prefix="mb_bl_")
    os.makedirs(os.path.join(v, "10_MEGA_BRAIN"))
    os.makedirs(os.path.join(v, "70_MOCS"))

    def w(rel, text):
        p = os.path.join(v, rel.replace("/", os.sep))
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    w("10_MEGA_BRAIN/Alvo.md", "# Alvo\n\nNota alvo.\n")
    # link simples + link com alias (deve contar 2)
    w("70_MOCS/MOC.md", "# MOC Geral\n\n- [[Alvo]]\n- [[Alvo|apelido]]\n")
    # link com heading + com pasta na frente (deve contar 2)
    w("10_MEGA_BRAIN/B.md", "# B\n\n[[Alvo#secao]] e [[10_MEGA_BRAIN/Alvo]]\n")
    # SOMENTE dentro de codigo -> NAO deve contar (nao aparece na lista)
    w("10_MEGA_BRAIN/Doc.md", "# Doc\n\n```\n[[Alvo]]\n```\ne `[[Alvo]]` inline\n")
    # placeholder de template -> nao conta
    w("10_MEGA_BRAIN/Tpl.md", "# Tpl\n\n[[${app.metadataCache.Alvo}]]\n")
    # nao linka nada
    w("10_MEGA_BRAIN/Solto.md", "# Solto\n\nsem links\n")
    return v


def main():
    v = make_vault()
    try:
        r = backlinks(v, "10_MEGA_BRAIN/Alvo.md")
        by = {x["path"]: x["count"] for x in r["backlinks"]}

        check(r["path"] == "10_MEGA_BRAIN/Alvo.md", "path normalizado com '/'")
        check(r["title"] == "Alvo", "titulo lido do H1")
        check(by.get("70_MOCS/MOC.md") == 2,
              "alias [[Alvo|apelido]] conta (esperado 2, got %r)" % by.get("70_MOCS/MOC.md"))
        check(by.get("10_MEGA_BRAIN/B.md") == 2,
              "heading e pasta resolvem (esperado 2, got %r)" % by.get("10_MEGA_BRAIN/B.md"))
        check("10_MEGA_BRAIN/Doc.md" not in by,
              "wikilink em bloco/inline de codigo NAO conta (P16.3)")
        check("10_MEGA_BRAIN/Tpl.md" not in by,
              "placeholder ${...} NAO conta")
        check("10_MEGA_BRAIN/Solto.md" not in by, "nota sem link nao aparece")
        check("10_MEGA_BRAIN/Alvo.md" not in by, "auto-link nao conta")
        check(r["total"] == 2, "total = 2 fontes (got %r)" % r["total"])
        check(r["backlinks"] == sorted(r["backlinks"],
                                      key=lambda x: (-x["count"], x["path"])),
              "ordenado por count desc, path asc")
        check(r["backlinks"][0]["title"] in ("MOC Geral", "B"),
              "titulo da fonte vem do H1")

        # nota inexistente -> FileNotFoundError
        try:
            backlinks(v, "10_MEGA_BRAIN/NaoExiste.md")
            check(False, "nota inexistente levanta FileNotFoundError")
        except FileNotFoundError:
            check(True, "nota inexistente levanta FileNotFoundError")

        # traversal -> VaultPathError (nome exato e' contrato, P17.1)
        try:
            backlinks(v, "../../secret.md")
            check(False, "traversal bloqueado (VaultPathError)")
        except Exception as e:
            check(type(e).__name__ == "VaultPathError",
                  "traversal levanta VaultPathError (got %s)" % type(e).__name__)

        # cache: 1a chamada miss, 2a hit; alterar .md invalida
        _BL_CACHE.clear()
        d1, c1 = backlinks_cached(v, "10_MEGA_BRAIN/Alvo.md")
        d2, c2 = backlinks_cached(v, "10_MEGA_BRAIN/Alvo.md")
        check(c1 is False and c2 is True, "cache: miss depois hit")
        check(d1 == d2, "cache devolve o mesmo payload")
        with open(os.path.join(v, "10_MEGA_BRAIN", "Solto.md"), "a",
                  encoding="utf-8") as fh:
            fh.write("\n[[Alvo]]\n")
        d3, c3 = backlinks_cached(v, "10_MEGA_BRAIN/Alvo.md")
        check(c3 is False, "cache invalida ao mudar um .md")
        check(d3["total"] == 3, "novo backlink detectado (total 3, got %r)" % d3["total"])
    finally:
        shutil.rmtree(v, ignore_errors=True)

    print()
    if FAILS:
        print("RESULTADO: %d FALHA(S)" % len(FAILS))
        return 1
    print("RESULTADO: TODOS OS ASSERTS OK (backlinks S17)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
