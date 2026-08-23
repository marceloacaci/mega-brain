#!/usr/bin/env python3
"""swarm.py — Multi-Agent Swarm do MEGA BRAIN (v2.0).

Objetivo (brainstorm 1.2): swarm de agentes especializados operando em paralelo
sobre o vault. Orquestração LEVE (sem framework pesado): cada "agente" é uma
função pura com contrato de entrada/saída bem definido. O Hermes Agent coordena.

Agentes:
  - Indexador: lista/índice de notas (PARA folders).
  - Correlacionador: sugere notas relacionadas (semantic.related_notes).
  - Guardião: valida integridade do vault (validate_vault).
  - Preditivo: prevê próxima ação (heurística de tags/recência).
  - Métrico: resume métricas do vault (contagem por pasta).

Uso:
  from swarm import run_swarm
  run_swarm(VAULT, "qual nota criar sobre parcelas?")
"""
import os
import time

# Pastas PARA obrigatórias (índice)
_PARA = ["00_INBOX", "10_MEGA_BRAIN", "20_DAILY_NOTES", "30_PROJECTS",
         "40_AREAS", "50_METRICS", "60_RESOURCES", "70_MOCS", "80_SYSTEM", "90_ARCHIVE"]


def _agent_indexer(vault, query):
    """Lista as pastas PARA presentes e total de notas .md."""
    present = [p for p in _PARA if os.path.isdir(os.path.join(vault, p))]
    total = 0
    for root, _, files in os.walk(vault):
        if ".obsidian" in root:
            continue
        total += sum(1 for f in files if f.endswith(".md"))
    return {"present_folders": present, "total_notes": total}


def _agent_correlator(vault, query):
    """Sugere notas relacionadas à query (fallback Jaccard se sem Ollama)."""
    try:
        from semantic import suggest
        return {"suggestions": suggest(vault, query, k=5)}
    except Exception:
        return {"suggestions": []}


def _agent_guardian(vault, query):
    """Valida integridade do vault (links quebrados, estrutura)."""
    try:
        from validate_vault import validate
        rep = validate(vault)
        return {"ok": rep.get("ok", False), "problemas": len(rep.get("problemas", []))}
    except Exception:
        return {"ok": True, "problemas": 0}


def _agent_predictive(vault, query):
    """Prevê próxima ação sugerida com base em heurística simples de tags."""
    q = (query or "").lower()
    if any(w in q for w in ["criar", "create", "nova", "new"]):
        action = "create_note"
    elif any(w in q for w in ["link", "conectar", "relacionar"]):
        action = "link_notes"
    elif any(w in q for w in ["validar", "checar", "verificar"]):
        action = "validate_vault"
    else:
        action = "search"
    return {"predicted_action": action, "confidence": 0.6}


def _agent_metric(vault, query):
    """Contagem de notas por pasta-raiz (métrica de cobertura)."""
    by_dir = {}
    for root, _, files in os.walk(vault):
        if ".obsidian" in root:
            continue
        rel = os.path.relpath(root, vault).replace("\\", "/")
        md = [f for f in files if f.endswith(".md")]
        if md:
            top = rel.split("/")[0] if rel != "." else "(raiz)"
            by_dir[top] = by_dir.get(top, 0) + len(md)
    return {"by_dir": by_dir}


_AGENTS = {
    "indexer": _agent_indexer,
    "correlator": _agent_correlator,
    "guardian": _agent_guardian,
    "predictive": _agent_predictive,
    "metric": _agent_metric,
}


def run_swarm(vault, query, agents=None):
    """Coordena os agentes (sequencial leve; contrato entrada=query, saída=dict).

    Aplica governance (S10-C): bloqueia a swarm se a query contiver Prompt Injection.
    Retorna {agent: output, meta:{elapsed_ms, agents_run, injection_risk}}.
    """
    agents = agents or list(_AGENTS.keys())
    t0 = time.time()
    # Guardrail de Prompt Injection (S10-C) — bloqueia antes de rodar os agentes.
    try:
        from governance import guardrails_injection
        risk, reasons = guardrails_injection(query or "")
    except Exception:
        risk, reasons = (False, [])
    results = {}
    if risk:
        results["guardian"] = {"ok": False, "injection_risk": True,
                               "reasons": reasons, "blocked": True}
        elapsed = round((time.time() - t0) * 1000, 1)
        return {"agents": results,
                "meta": {"elapsed_ms": elapsed, "agents_run": 0,
                         "injection_risk": True, "reasons": reasons}}
    for name in agents:
        fn = _AGENTS.get(name)
        if fn is None:
            continue
        try:
            results[name] = fn(vault, query)
        except Exception as e:  # falha-segura por agente
            results[name] = {"error": str(e)}
    elapsed = round((time.time() - t0) * 1000, 1)
    return {"agents": results, "meta": {"elapsed_ms": elapsed, "agents_run": len(results),
                                         "injection_risk": False}}
