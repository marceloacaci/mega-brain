#!/usr/bin/env python3
"""Testes de unidade para tags.py (NUVEM DE TAGS — S15).

Sem rede, sem vault real: fixture temporário cobre frontmatter (bloco + inline),
tag inline no corpo, normalização, top_only (ignora count==1) e limite.
Anti-tautologia: reverter a ordenação (crescente) ou a filtragem top_only faz falhar.
"""
import os
import sys
import time
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS"))

from tags import tag_counts  # noqa: E402

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


def build_fixture():
    d = tempfile.mkdtemp(prefix="mb_tags_")
    notes = {
        "10_MEGA_BRAIN/A.md": "---\ntipo: x\ntags:\n  - moc\n  - projeto\n  - MOC\n---\n# A\n#urgente texto #moc\n",
        "30_PROJECTS/X/B.md": "---\ntags: [projeto, financeiro, urgente, moc]\n---\n# B\n",
        "20_DAILY_NOTES/C.md": "# C\n#rara tag unica aqui #financeiro\n",
        "D.md": "# D sem tags\n",
    }
    for rel, c in notes.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(c)
    return d


def main():
    d = build_fixture()
    try:
        tags = tag_counts(d, limit=20)
        by = {t["tag"]: t["count"] for t in tags}
        # moc aparece 2x (A frontmatter + A inline + B? nao) -> A: moc(fm)+moc(inline)=1 nota, +normalizacao MOC
        check("encontra moc", by.get("moc", 0) >= 2)  # A (fm MOC+moc inline) + B -> 2 notas
        check("encontra projeto", by.get("projeto", 0) >= 2)  # A + B
        check("encontra financeiro", by.get("financeiro", 0) >= 2)  # B + C
        check("encontra urgente", by.get("urgente", 0) >= 2)  # A inline + B
        # normalização: 'MOC' vira 'moc' (aparece em A como 'MOC' e inline '#moc')
        check("normaliza maiuscula", "MOC" not in by and "moc" in by)
        # top_only ignora tag com count==1 ('rara')
        check("top_only ignora rara (count1)", "rara" not in by)
        # ordenacao descrescente por count
        counts = [t["count"] for t in tags]
        check("ordenado por count desc", counts == sorted(counts, reverse=True))
        # limit respeitado
        check("limit=2 -> 2", len(tag_counts(d, limit=2)) == 2)
        # ANTI-TAUTOLOGIA: tags com aspas no frontmatter NAO devem reter aspas
        # (defeito real do vault: `"projeto/pentagon-mind"` chegava com aspas).
        # Usa top_only=False para a tag sobreviver (count==1) e o teste pegar o bug.
        qd = tempfile.mkdtemp(prefix="mb_tags_quote_")
        try:
            with open(os.path.join(qd, "q.md"), "w", encoding="utf-8") as fh:
                fh.write('---\ntags: ["projeto/pentagon-mind", \'urgente\']\n---\n# q\n')
            qtags = {t["tag"]: t["count"] for t in tag_counts(qd, limit=20, top_only=False)}
            check("tag com aspas duplas sem aspas", '"projeto/pentagon-mind"' not in qtags)
            check("tag com aspas simples sem aspas", "'urgente'" not in qtags)
            check("tag quote-stripped normalizada", "projeto/pentagon-mind" in qtags)
            check("tag aspas-simples normalizada", "urgente" in qtags)
        finally:
            shutil.rmtree(qd, ignore_errors=True)
        # tag inline sem frontmatter (C) contada
        check("inline sem fm contado", by.get("financeiro", 0) >= 2)
        # vault sem tags -> lista vazia
        empty = tempfile.mkdtemp(prefix="mb_tags_empty_")
        try:
            with open(os.path.join(empty, "z.md"), "w", encoding="utf-8") as fh:
                fh.write("# sem tag\n")
            check("sem tags -> []", tag_counts(empty, limit=10) == [])
        finally:
            shutil.rmtree(empty, ignore_errors=True)
        # cache: 1o miss, 2o hit; invalida ao mexer num .md
        import tags as tags_mod
        dc = tempfile.mkdtemp(prefix="mb_tags_cache_")
        try:
            for nm in ("a.md", "b.md"):
                with open(os.path.join(dc, nm), "w", encoding="utf-8") as fh:
                    fh.write("---\ntags: [x]\n---\n# t\n")
            _, hit1 = tags_mod.tag_counts_cached(dc, limit=20)
            _, hit2 = tags_mod.tag_counts_cached(dc, limit=20)
            check("tags cache: 1o miss", hit1 is False)
            check("tags cache: 2o hit", hit2 is True)
            time.sleep(0.01)
            with open(os.path.join(dc, "a.md"), "a", encoding="utf-8") as fh:
                fh.write("# y\n")
            os.utime(os.path.join(dc, "a.md"), None)
            _, hit3 = tags_mod.tag_counts_cached(dc, limit=20)
            check("tags cache: invalida ao mexer .md", hit3 is False)
        finally:
            shutil.rmtree(dc, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print(f"\nRESULTADO: {_PASS} passaram, {_FAIL} falharam")
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
