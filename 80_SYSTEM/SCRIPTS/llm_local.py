#!/usr/bin/env python3
"""llm_local.py — LLM local do MEGA BRAIN (v2.0).

Objetivo (brainstorm 1.1): raciocínio via modelo de código aberto local (Ollama)
para eliminar custo de API e manter dados no disco (mitiga LLM06).
SEMPRE há fallback heurístico: se OLLAMA_URL não estiver setado ou indisponível,
retorna um resumo estruturado determinístico em vez de quebrar.

Uso:
  from llm_local import reason
  reason("Explique o padrão de parcelas no MeuBolso")
"""
import os
import re

_OLLAMA_URL = os.environ.get("OLLAMA_URL", "").rstrip("/")
_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")


def _ollama_generate(prompt):
    """Chama Ollama /api/generate; retorna texto ou None se indisponível."""
    if not _OLLAMA_URL:
        return None
    try:
        import urllib.request
        import json
        req = urllib.request.Request(
            _OLLAMA_URL + "/api/generate",
            data=json.dumps({"model": _MODEL, "prompt": prompt, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode()).get("response", "")
    except Exception:
        return None


def _heuristic(prompt, vault=None):
    """Resposta heurística determinística (sem IA externa)."""
    out = []
    out.append(f"Tarefa recebida: {prompt}")
    # extrai palavras-chave do prompt
    kws = re.findall(r"[a-z0-9áàâãéèêíïóôõúüç]{4,}", prompt.lower())
    if kws:
        out.append("Palavras-chave detectadas: " + ", ".join(sorted(set(kws))[:8]))
    if vault:
        try:
            from semantic import suggest
            sug = suggest(vault, prompt, k=3)
            if sug:
                out.append("Notas sugeridas: " + ", ".join(s["path"] for s in sug))
        except Exception:
            pass
    out.append("Recomendação: usar /swarm para coordenar os agentes especializados.")
    return "\n".join(out)


def reason(prompt, vault=None):
    """Raciocínio local. Usa Ollama se disponível; senão fallback heurístico.

    Governance (S10-C): mascaramos PII do prompt ANTES de qualquer envio a
    modelo externo/local, e também antes do eco heurístico (evita vazamento).
    """
    try:
        from governance import mask_pii
        clean_prompt, pii_count = mask_pii(prompt or "")
    except Exception:
        clean_prompt, pii_count = (prompt or ""), 0
    resp = _ollama_generate(clean_prompt)
    if resp:
        return {"source": "ollama", "model": _MODEL, "response": resp.strip(),
                "pii_masked": pii_count}
    return {"source": "heuristic", "model": None,
            "response": _heuristic(clean_prompt, vault), "pii_masked": pii_count}
