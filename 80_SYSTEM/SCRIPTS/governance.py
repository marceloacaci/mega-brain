#!/usr/bin/env python3
"""governance.py — Guardrails de IA do MEGA BRAIN (v2.0 / S10-C).

Objetivo (architecture.md + brainstorm): mitigar riscos de LLM (OWASP Top 10 LLM):
  1. Prompt Injection: detectar tentativas de sobrescrever instrucoes do sistema.
  2. Exposicao de PII: mascarar dados sensiveis (e-mail, CPF, telefone, API keys)
     ANTES de qualquer envio a modelo externo/LLM local.
Sem dependencias externas (regex stdlib). Falha-seguro: em caso de duvida, bloqueia.
"""
import re

# Padroes de Prompt Injection (case-insensitive). Combina delimitadores de sistema
# e frases de sobreposicao de instrucao.
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above|preceding)\s+instructions?",
    r"ignore\s+(your\s+)?(system\s+)?prompt",
    r"desconsidere\s+(todas\s+as\s+)?(instru(coes|ções)|anteriores|acima)",
    r"voc(e|ê)\s+(é|e)\s+(um\s+)?(llm|modelo|ia|assistente)\s+diferente",
    r"you\s+are\s+now\s+a",
    r"system\s*:\s*",
    r"\[system\]",
    r"\[\[system",
    r"new\s+instructions?\s*:",
    r"override\s+(your\s+)?(guidelines|rules|instructions)",
    r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions)",
    r"do\s+whatever\s+it\s+takes",
    r"jailbreak",
]

_PI = re.compile("|".join(f"(?:{p})" for p in INJECTION_PATTERNS), re.IGNORECASE)

# PII: e-mail, CPF (xxx.xxx.xxx-xx), telefone BR, chaves de API comuns.
_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
_PHONE = re.compile(r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}-?\d{4}\b")
_APIKEY = re.compile(r"\b(?:sk|pk|api[_-]?key|token|bearer)[-_ ]?[A-Za-z0-9]{16,}\b", re.IGNORECASE)

_MASK = "[PII]"


def guardrails_injection(text):
    """Retorna (risk:bool, reasons:list[str]). True => bloquear a entrada do agente."""
    if not text:
        return False, []
    reasons = []
    for m in _PI.finditer(text):
        reasons.append(m.group(0)[:60])
    return (len(reasons) > 0), reasons


def mask_pii(text):
    """Substitui PII por [PII]. Retorna (clean_text, count)."""
    if not text:
        return text, 0
    count = 0
    out = text
    for pat in (_EMAIL, _CPF, _PHONE, _APIKEY):
        found = pat.findall(out)
        count += len(found)
        out = pat.sub(_MASK, out)
    return out, count


def sanitize_input(text):
    """Aplica governance numa entrada de agente/LLM: levanta se houver injection."""
    risk, reasons = guardrails_injection(text)
    if risk:
        raise ValueError(f"Prompt injection detectado: {reasons}")
    return mask_pii(text)[0]
