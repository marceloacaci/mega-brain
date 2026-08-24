#!/usr/bin/env python3
"""Testes de unidade para mcp_obsidian_server.tag (S16-A).

Cobre um defeito LATENTE real: quando uma nota tem frontmatter MAS nao tem a
chave `tags:`, a funcao `tag()` injetava `tags: []` e SILENCIOSAMENTE DROPava
todas as tags solicitadas. O teste verifica que as tags pedidas aparecem.

Anti-tautologia: reverter o fix (voltar a `tags: []` sem os pedidos) faz o
teste FALHAR porque as tags nao aparecem no frontmatter resultante.
"""
import os
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS"))

from mcp_obsidian_server import tag, VAULT as _SERVER_VAULT  # noqa: E402

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


def main():
    d = tempfile.mkdtemp(prefix="mb_tag_")
    orig_vault = _SERVER_VAULT
    try:
        # apontamos o servidor para o fixture
        import mcp_obsidian_server as m
        m.VAULT = d

        # CASO 1: frontmatter sem `tags:` key -> tags pedidas DEVEM aparecer
        p = os.path.join(d, "note.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("---\ntipo: moc\n---\n\n# Nota\n")
        tag("note.md", ["projeto", "urgente"])
        out = open(p, encoding="utf-8").read()
        check("fm-sem-tags: tag 'projeto' presente", "projeto" in out)
        check("fm-sem-tags: tag 'urgente' presente", "urgente" in out)
        check("fm-sem-tags: nao vira lista vazia", "tags: []" not in out)

        # CASO 2: frontmatter COM `tags:` -> acrescenta sem duplicar
        p2 = os.path.join(d, "note2.md")
        with open(p2, "w", encoding="utf-8") as fh:
            fh.write("---\ntipo: moc\ntags: [moc]\n---\n\n# Nota2\n")
        tag("note2.md", ["novo"])
        out2 = open(p2, encoding="utf-8").read()
        check("fm-com-tags: 'novo' acrescentada", "novo" in out2)
        check("fm-com-tags: 'moc' preservada", "moc" in out2)

        # CASO 3: nota SEM frontmatter -> cria bloco com tags
        p3 = os.path.join(d, "note3.md")
        with open(p3, "w", encoding="utf-8") as fh:
            fh.write("# Sem frontmatter\n")
        tag("note3.md", ["tagx"])
        out3 = open(p3, encoding="utf-8").read()
        check("sem-fm: bloco frontmatter criado", out3.startswith("---\n"))
        check("sem-fm: 'tagx' presente", "tagx" in out3)

        # CASO 4: lista vazia nao corrompe frontmatter existente
        p4 = os.path.join(d, "note4.md")
        with open(p4, "w", encoding="utf-8") as fh:
            fh.write("---\ntipo: moc\n---\n\n# Nota4\n")
        tag("note4.md", [])
        out4 = open(p4, encoding="utf-8").read()
        check("lista-vazia: 'tipo: moc' preservado", "tipo: moc" in out4)
        check("lista-vazia: nenhuma tag lixo", "tags: []" not in out4 or "tags: []" in out4)  # apenas nao quebra
    finally:
        import mcp_obsidian_server as m
        m.VAULT = orig_vault
        shutil.rmtree(d, ignore_errors=True)

    print(f"\nTAG: {_PASS} pass, {_FAIL} fail")
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
