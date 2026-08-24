#!/usr/bin/env python3
"""Testes de unidade para activity.activity_cached (S22 — cache do heatmap).

Verifica o padrao P11-style: 1o acesso = miss, 2o = hit, invalida ao tocar
um .md. Anti-tautologia: reverter o cache (sempre miss) faz o assert de
`cached=True` falhar no 2o acesso.
"""
import os
import sys
import time
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS"))

from activity import activity_counts, activity_cached  # noqa: E402

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
    d = tempfile.mkdtemp(prefix="mb_act_")
    try:
        dd = os.path.join(d, "20_DAILY_NOTES")
        os.makedirs(dd)
        with open(os.path.join(dd, "2026-08-24.md"), "w", encoding="utf-8") as fh:
            fh.write("# hoje\n")
        with open(os.path.join(dd, "2026-08-23.md"), "w", encoding="utf-8") as fh:
            fh.write("# ontem\n")

        # funcao pura
        daily_dir, counts = activity_counts(d)
        check("daily_dir detectado", "20_DAILY_NOTES" in daily_dir)
        check("conta 2 datas", counts.get("2026-08-24") == 1 and counts.get("2026-08-23") == 1)

        # sem dir de daily -> '(ausente)'
        nd = tempfile.mkdtemp(prefix="mb_act2_")
        try:
            dd2, counts2 = activity_counts(nd)
            check("sem daily_dir -> (ausente)", dd2 == "(ausente)")
        finally:
            shutil.rmtree(nd, ignore_errors=True)

        # cache: miss -> hit -> invalida
        (dir1, c1), was1 = activity_cached(d, ttl=30)
        check("activity 1o acesso miss", was1 is False)
        check("activity payload tem as datas", c1.get("2026-08-24") == 1)
        (dir2, c2), was2 = activity_cached(d, ttl=30)
        check("activity 2o acesso hit", was2 is True)
        check("activity hit mantem payload", c2.get("2026-08-24") == 1)

        # tocar um .md (o arquivo de nota diaria de verdade) -> proximo acesso miss
        time.sleep(0.01)
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith(".md"):
                    os.utime(os.path.join(root, f), (time.time() + 5, time.time() + 5))
        (_, c3), was3 = activity_cached(d, ttl=30)
        check("activity apos tocar .md: miss", was3 is False)

        # ttl=0 forca miss
        (_, c4), was4 = activity_cached(d, ttl=0)
        check("activity ttl=0 forca miss", was4 is False)
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print(f"\nACTIVITY-CACHE: {_PASS} pass, {_FAIL} fail")
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
