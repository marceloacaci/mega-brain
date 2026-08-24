#!/usr/bin/env python3
"""vault_path.py — Confinamento de path ao vault (anti path-traversal).

Fonte unica do guard VaultPathError + vault_path(vault, rel). Antes, o mesmo
bloco de confinamento era duplicado em mcp_obsidian_server, semantic, predictive
e (implicitamente) compress. Centralizar aqui garante que uma correção de
segurança se propaga a todas as rotas/funcoes de uma vez (sem drift entre
implementacoes).

Contrato: levanta VaultPathError se `rel` tentar sair do vault. O MCP e semantic
verificam `type(e).__name__ == "VaultPathError"` para mapear traversal -> HTTP 400;
manter o NOME exato da classe e' parte do contrato de teste (test_security_v2 /
e2e_security / test_predictive_security).
"""
import os


class VaultPathError(ValueError):
    """Path recebido tenta sair do vault (path traversal)."""


def vault_path(vault, rel):
    """Resolve `rel` DENTRO do vault; levanta VaultPathError se escapar.

    `rel` pode vir de URL/JSON (com '/' ou '\\'); normalizamos para '/'.
    Retorna o caminho absoluto confinado. NUNCA resolve para fora de `vault`
    (nem retorna o proprio vault como arquivo — exige um nome de nota nao-vazio).
    """
    base = os.path.abspath(vault)
    rel = (rel or "").replace("\\", "/").strip("/")
    if not rel:
        raise VaultPathError("path vazio")
    fp = os.path.abspath(os.path.join(base, rel))
    if os.path.normcase(fp) != os.path.normcase(base) and \
            not os.path.normcase(fp).startswith(os.path.normcase(base) + os.sep):
        raise VaultPathError("path fora do vault")
    return fp
