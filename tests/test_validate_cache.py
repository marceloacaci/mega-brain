#!/usr/bin/env python3
"""Testes de unidade para validate_vault.validate_cached (S16-B — cache de /validate).

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

from validate_vault import validate_cached  # noqa: E402

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
    d = tempfile.mkdtemp(prefix="mb_valcache_")
    try:
        p = os.path.join(d, "n.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("# nota\n")
        # 1o acesso: miss
        rep1, c1 = validate_cached(d, ttl=30)
        check("1o acesso e miss (cached=False)", c1 is False)
        check("payload tem total_notas", rep1.get("total_notas") == 1)
        # 2o acesso rapido: hit
        rep2, c2 = validate_cached(d, ttl=30)
        check("2o acesso e hit (cached=True)", c2 is True)
        check("payload estavel no hit", rep2.get("total_notas") == 1)
        # mexer num .md -> mtime muda -> proximo acesso miss
        time.sleep(0.01)
        os.utime(p, (time.time() + 5, time.time() + 5))
        rep3, c3 = validate_cached(d, ttl=30)
        check("apos tocar .md: miss (cached=False)", c3 is False)
        # TTL expirado -> miss mesmo sem mexer
        rep4, c4 = validate_cached(d, ttl=0)
        check("ttl=0 forca miss", c4 is False)
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print(f"\nVALIDATE-CACHE: {_PASS} pass, {_FAIL} fail")
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
