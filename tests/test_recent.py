#!/usr/bin/env python3
"""Testes de unidade para recent.py (NOTAS RECENTES — S14).

Sem rede, sem vault real: cria um fixture temporario, verifica ordenacao por
mtime, limite, cutoff e mapeamento de tipo. Anti-tautologia: reverter a
ordenacao (crescente) faz o teste falhar.
"""
import os
import sys
import tempfile
import time
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS"))

from recent import recent_notes  # noqa: E402

# Resultado
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
    d = tempfile.mkdtemp(prefix="mb_recent_")
    # 3 notas em pastas distintas; criadas em momentos diferentes.
    now = time.time()
    paths = [
        (os.path.join(d, "10_MEGA_BRAIN", "Nova.md"), now - 10),       # ~0.0001d
        (os.path.join(d, "docs", "sub", "Guide.md"), now - 60),        # ~0.0007d
        (os.path.join(d, "20_DAILY_NOTES", "Meio.md"), now - 600),     # ~0.0069d
        (os.path.join(d, "70_MOCS", "Antiga.md"), now - 100000),       # ~1.16d
    ]
    for p, mt in paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("# x\n")
        os.utime(p, (mt, mt))
    return d, now


def main():
    d, now = build_fixture()
    try:
        # 1) ordenacao descrescente por mtime
        rows = recent_notes(d, limit=10)
        check("retorna 4 notas", len(rows) == 4)
        mt = [r["mtime"] for r in rows]
        check("ordenado por mtime decrescente", mt == sorted(mt, reverse=True))

        # 2) a mais recente e Nova.md (10_MEGA_BRAIN)
        check("mais recente == Nova.md", rows[0]["path"].endswith("Nova.md"))
        check("tipo de Nova == core", rows[0]["type"] == "core")
        check("tipo de Antiga == moc", any(r["type"] == "moc" and r["path"].endswith("Antiga.md") for r in rows))
        check("tipo de Guide == doc", any(r["type"] == "doc" for r in rows))

        # 3) limite respeitado
        check("limit=2 retorna 2", len(recent_notes(d, limit=2)) == 2)

        # 4) cutoff em dias: 0.5 dia (~43200s) exclui Antiga (100000s=~1.16d),
        #    mantem Nova(10s)/Guide(60s)/Meio(600s).
        cut = recent_notes(d, limit=10, cutoff_days=0.5)
        check("cutoff 0.5d -> 3 notas", len(cut) == 3)
        check("cutoff 0.5d exclui Antiga", not any(r["path"].endswith("Antiga.md") for r in cut))
        # cutoff estreito (0.0002d ~ 17s) -> so Nova (10s); Guide(60s) excluido
        cut2 = recent_notes(d, limit=10, cutoff_days=0.0002)
        check("cutoff 0.0002d -> so Nova", len(cut2) == 1 and cut2[0]["path"].endswith("Nova.md"))

        # 5) age_days positivo e coerente
        check("age_days de Nova ~0.0001", 0 <= rows[0]["age_days"] < 1)

        # 6) limit <= 0 nao quebra (vira 1)
        check("limit invalido -> 1", len(recent_notes(d, limit=0)) == 1)

        # 7) vault vazio -> lista vazia (sem erro)
        empty = tempfile.mkdtemp(prefix="mb_recent_empty_")
        try:
            check("vault vazio -> []", recent_notes(empty, limit=10) == [])
        finally:
            shutil.rmtree(empty, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # 8) cache: primeiro miss, segundo hit; invalida ao mexer num .md
    import recent as recent_mod
    dc = tempfile.mkdtemp(prefix="mb_recent_cache_")
    try:
        for nm in ("a.md", "b.md", "c.md"):
            with open(os.path.join(dc, nm), "w", encoding="utf-8") as fh:
                fh.write("# x\n")
        _, hit1 = recent_mod.recent_notes_cached(dc, limit=3)
        _, hit2 = recent_mod.recent_notes_cached(dc, limit=3)
        check("cache: 1o miss", hit1 is False)
        check("cache: 2o hit", hit2 is True)
        # mexer num arquivo -> mtime muda -> proximo acesso e miss
        time.sleep(0.01)
        with open(os.path.join(dc, "a.md"), "a", encoding="utf-8") as fh:
            fh.write("z\n")
        os.utime(os.path.join(dc, "a.md"), None)
        _, hit3 = recent_mod.recent_notes_cached(dc, limit=3)
        check("cache: invalida ao mexer .md", hit3 is False)
    finally:
        shutil.rmtree(dc, ignore_errors=True)

    print(f"\nRESULTADO: {_PASS} passaram, {_FAIL} falharam")
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
