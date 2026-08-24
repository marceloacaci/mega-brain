#!/usr/bin/env python3
"""constants.py — Constantes compartilhadas do MEGA BRAIN.

Evita magic numbers duplicados entre os modulos (ex.: teto de notas do
vault usado por semantic e graph). Centralizar aqui torna a consistencia
do teto uma unica fonte de verdade (ver test_note_limit_consistency.py).
"""

# Teto de notas lidas/processadas por varredura do vault. semantic.related_notes,
# semantic.suggest, semantic._vault_notes, graph.build_graph, graph._iter_notes e
# graph._vault_signature usam este valor. Mantido em 600 para cobertura de vaults
# grandes (consistencia das arestas semanticas no /graph vs related_notes/suggest).
NOTE_LIMIT = 600

# Pastas que NUNCA contem notas de conteudo do vault e devem ser ignoradas nas
# varreduras (semantic._vault_notes, _vault_mtime_signature). Sem isso, o repo
# MEGA BRAIN (que E o vault) varre tests/fixture/*.md como se fossem notas —
# corrompendo /suggest, /related e a assinatura de cache (ex.: reason() sugeria
# tests/fixture/70_MOCS/MOC_Teste.md). Estes dirs nunca sao notas do usuario.
VAULT_SKIP_DIRS = {".obsidian", ".trash", ".git", "tests", "node_modules",
                   "__pycache__", ".claudian", ".hypernovum", ".makemd", ".space"}


def prune_vault_dirs(dirs):
    """Podar (in-place) a lista `dirs` do os.walk removendo pastas que NUNCA
    sao notas de conteudo do vault. Uso:
        for root, dirs, files in os.walk(vault):
            prune_vault_dirs(dirs)
            ...
    Evita varrer tests/, node_modules/, .git, etc. (o repo MEGA BRAIN E o vault).
    """
    dirs[:] = [d for d in dirs if d not in VAULT_SKIP_DIRS]

