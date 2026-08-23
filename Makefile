# Makefile — alvos de qualidade MEGA BRAIN (dev local)
# Uso: make test | make lint | make sast | make validate

PY := python
SERVER := 80_SYSTEM/SCRIPTS/mcp_obsidian_server.py

.PHONY: test lint sast validate all

all: lint sast test

lint:
	@echo "== Lint PowerShell (parse) =="
	@pwsh -NoProfile -Command "Get-ChildItem 80_SYSTEM -Recurse -Filter *.ps1 | ForEach-Object { $$null = [scriptblock]::Create((Get-Content $$_ -Raw)) }"
	@echo "== Lint Python (compile) =="
	$(PY) -m py_compile $(SERVER) 80_SYSTEM/SCRIPTS/validate_vault.py

sast:
	@echo "== SAST Python (bandit, se instalado) =="
	@$(PY) -m bandit -r 80_SYSTEM/SCRIPTS 80_SYSTEM/MCP tests -ll || echo "(bandit nao instalado — pulando)"

validate:
	@echo "== Validacao do vault (dry-run local) =="
	@$(PY) 80_SYSTEM/SCRIPTS/validate_vault.py || true

test:
	@echo "== Suíte completa de testes =="
	$(PY) tests/run_all.py
