# Brainstorm — Ideias e Viabilidade (MEGA BRAIN)

## Features Potenciais (diferenciais)
1. **Correlação Semântica com IA** — usar embeddings para sugerir notas relacionadas
   (além de heurística de palavras-chave atual).
2. **Modo Preditivo Avançado** — prever próxima tarefa com base em padrões de horário.
3. **Integração com Calendário** — sincronizar daily notes com Google Calendar/Outlook.
4. **Captura por Voz** — transcrever áudio do Hermes e criar nota no INBOX.
5. **Dashboard Web** — além do Obsidian, um painel HTML vivo lendo o MCP.
6. **Alertas Proativos** — `90_ALERTS` dispara notificação quando métrica cai.
7. **Exportação para Publish** — publicar MOCs selecionadas como site estático.

## Features Técnicas
- **Caching de consultas MCP** (TTL) para reduzir I/O em `/search`.
- **Otimização de queries** — índice invertido em memória das notas.
- **Testes E2E automatizados** do pipeline (hooks + reindex) via CI.
- **Failover de backup** — espelho em segundo destino se o primário falhar.
- **Validação de integridade** — checar frontmatter das notas `50_METRICS`.

## Análise de Viabilidade
| Ideia | Risco Técnico | Alternativa |
|-------|---------------|-------------|
| Correlação semântica (IA) | Médio — custo de API, latência | Heurística de tags + links primeiro |
| Integração calendário | Médio — OAuth, rate limits | Exportar daily note como `.ics` |
| Dashboard web | Baixo — já temos MCP HTTP | Reuso das rotas existentes |
| Captura por voz | Alto — depende de STT local | Usar transcrição do Hermes (já existe) |
| Failover backup | Baixo — robocopy suporta | Segundo destino no `config.json` |

## Riscos
- **Rate limit de API externa** (se IA) → mitigar com cache e fallback heurístico.
- **Corrupção do `.last_light.txt`** → já tratado com try/catch falha-segura.
- **Dataview não instalado** → dashboard aparece como código bruto até instalar plugin.
- **Lock de reindex** → watcher respeita `.reindex.lock` < 30min.

## Recomendação PO
Priorizar **Dashboard Web** (baixo risco, alto valor) e **Testes E2E** (reduz
regressões). IA semântica só após consolidar a base heurística.
