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
