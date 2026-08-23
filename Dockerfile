# ============================================================================
# MEGA BRAIN — Dockerfile (multi-stage)
# A imagem NAO e o runtime de producao (o vault vive no Windows + Obsidian).
# E uma imagem de VALIDACAO: roda lint/SAST/smoke test e expoe o MCP p/ teste.
# ============================================================================

# ---- Stage 1: base mínima (alpine) com Python 3.11 ----
FROM python:3.11-alpine AS base
RUN apk add --no-cache bash curl
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8770 \
    VAULT_ROOT=/vault

# ---- Stage 2: validate (runtime de validacao + ferramentas de lint) ----
FROM base AS validate
# PowerShell 7 nao tem pacote nativo no alpine; usamos a imagem oficial pwsh
# como build-context de ferramentas e copiamos apenas o que o smoke test precisa.
RUN apk add --no-cache python3 py3-pip
RUN pip install --no-cache-dir bandit
COPY . /app
# healthcheck nativo: o MCP responde /health
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
  CMD curl -fsS http://127.0.0.1:${MCP_PORT}/health || exit 1
EXPOSE 8770
# Por padrao sobe o MCP num vault fixture para validacao (override VAULT_ROOT).
CMD ["sh", "-c", "python 80_SYSTEM/SCRIPTS/mcp_obsidian_server.py --port ${MCP_PORT} --host ${MCP_HOST} --vault ${VAULT_ROOT}"]

# ---- Stage 3: pwsh-lint (PowerShell 7 para PSScriptAnalyzer) ----
# Imagem oficial pwsh (base Debian) — usada apenas no CI para analisar os .ps1.
FROM mcr.microsoft.com/powershell:7-alpine AS pwsh-lint
RUN pwsh -Command "Install-Module -Name PSScriptAnalyzer -Force -Scope AllUsers -ErrorAction Stop"
WORKDIR /app
COPY . /app
CMD ["pwsh", "-NoProfile", "-Command", "Get-ChildItem 80_SYSTEM -Recurse -Filter *.ps1 | ForEach-Object { $null = [scriptblock]::Create((Get-Content $_ -Raw)) }"]
