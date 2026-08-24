#!/usr/bin/env python3
"""test_compress_contract.py — Unidade: contrato de compress_text (S11-G).

Defeitos reais corrigidos:
  1. `tokens_after` podia ESTOURAR `max_tokens`: o marcador "\\n[...truncado]" era
     concatenado DEPOIS de calcular o orcamento, entao o resultado ficava maior que
     o limite pedido (ex.: max_tokens=20 -> tokens_after=22).
  2. `estimate_tokens("")` retornava 1 (texto vazio nao custa token).

Invariantes travadas aqui:
  - `tokens_after <= max_tokens` SEMPRE (a promessa da funcao).
  - `truncated` True <=> o marcador esta presente.
  - Estrutura relevante (headings/tags/wikilinks) preservada quando cabe.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "80_SYSTEM", "SCRIPTS")))
import compress  # noqa: E402

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


TEXTO = "# Titulo\n\n#tag [[link]]\n\nlinha A\nlinha A\n\n\nlinha B\n" * 5


def main():
    print("=== Unidade: compress_text contrato (S11-G) ===")

    check("estimate_tokens('') == 0", compress.estimate_tokens("") == 0,
          f"got={compress.estimate_tokens('')}")
    check("estimate_tokens(None) == 0", compress.estimate_tokens(None) == 0)
    check("estimate_tokens cresce com o texto",
          compress.estimate_tokens("x" * 400) > compress.estimate_tokens("x" * 40))

    # INVARIANTE PRINCIPAL: nunca estourar o orcamento pedido (com piso MIN_TOKENS,
    # pois o proprio marcador "[...truncado]" custa ~3 tokens).
    for mt in (1, 5, 20, 50, 200, 2000):
        r = compress.compress_text(TEXTO, max_tokens=mt)
        teto = max(mt, compress.MIN_TOKENS)
        check(f"tokens_after <= max(max_tokens, MIN_TOKENS) (max={mt})",
              r["tokens_after"] <= teto, f"after={r['tokens_after']} teto={teto}")
        marker = "[...truncado]" in r["compressed"]
        check(f"truncated coerente com marcador (max={mt})",
              r["truncated"] == marker, f"truncated={r['truncated']} marker={marker}")

    # sem truncagem, a estrutura relevante sobrevive
    r = compress.compress_text(TEXTO, max_tokens=5000)
    check("nao truncou com orcamento grande", r["truncated"] is False)
    check("heading preservado", "# Titulo" in r["compressed"])
    check("wikilink preservado", "[[link]]" in r["compressed"])
    check("linha duplicada colapsada", r["compressed"].count("linha A") == 1,
          f"count={r['compressed'].count('linha A')}")
    check("comprimiu (after < before)", r["tokens_after"] < r["tokens_before"],
          f"{r['tokens_after']} vs {r['tokens_before']}")

    # texto vazio nao explode
    r0 = compress.compress_text("", max_tokens=100)
    check("texto vazio nao levanta", r0["tokens_before"] == 0 and
          r0["truncated"] is False, f"got={r0}")

    # compress_note com path inexistente -> None (nao excecao)
    check("compress_note inexistente -> None",
          compress.compress_note(".", "nao/existe/aqui.md") is None)

    print(f"\nRESULTADO: {PASS} passaram, {FAIL} falharam")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
