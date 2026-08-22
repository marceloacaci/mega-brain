---
tipo: ontologia
projeto: pentagon-mind
criado: 2026-08-21
tags: ["projeto/pentagon-mind", "ontologia", "relacional"]
---

# 🕸️ Ontologia Relacional — PENTAGON-MIND

> Espelho analítico de `data/ontology.json`. Modela relações Administração ↔ Doutrina ↔ Conflito ↔ Sistema de Armas.

## Administrações (7)
| ID | Presidente | Mandato | Postura-chave |
|----|-----------|---------|---------------|
| bush41 | George H. W. Bush | 1989–1993 | Multilateralismo / Nova Ordem |
| clinton | Bill Clinton | 1993–2001 | Internacionalismo liberal / RMA |
| bush43 | George W. Bush | 2001–2009 | Doutrina Bush / preventivo |
| obama | Barack Obama | 2009–2017 | Pivô Ásia / Guerra Remota |
| trump | Donald J. Trump | 2017–2021 | America First / USSF |
| biden | Joseph R. Biden | 2021–2025 | Dissuasão Integrada |
| trump2 | Donald J. Trump (2º) | 2025–2029 | America First 2.0 / Reindustrialização |

## Doutrinas (10)
- **doct-airland** — AirLand Battle (FM 100-5) · 1982–1993
- **doct-powell** — Doutrina Powell (força avassaladora, saída definida)
- **doct-rma** — Revolução nos Assuntos Militares (Clinton)
- **doct-bush** — Doutrina Bush / ataque preventivo (2002)
- **doct-coin** — Contrainsurreição (FM 3-24, Petraeus)
- **doct-gpc-precursor** — Rebalanceamento / Pivô Ásia
- **doct-gpc** — Competição de Grandes Potências (formal)
- **doct-mdo** — Operações Multidomínio (5 domínios)
- **doct-jadc2** — C2 Conjunto de Todos os Domínios
- **doct-pqc** — Criptografia Pós-Quântica (PQC)

## Conflitos (11)
Tempestade no Deserto (1991) · Bálcãs · Somália · Afeganistão · Iraque (2003) · Líbia · Síria/ISIS · Soleimani (2020) · Ucrânia (2022→) · Taiwan (dissuasão) · Irã (2025).

## Sistemas de Armas (20)
M1 Abrams · MQ-9 Reaper · MQ-1 Predator · F-15E · F-16 · F-22 · F-35 · B-2 · Minuteman III/Sentinel · Ohio/Columbia · Tomahawk · LRASM · Patriot · HIMARS · M777 · AUKUS · USSF · Replicator · GPS/NAVSTAR · ARPANET/TCP-IP.

## Cross-Refs (exemplos)
- **bush41 + doct-powell + Tempestade 1991 + M1/Tomahawk/F-15E**
- **bush43 + doct-bush/coin + Afeganistão/Iraque + M1/MQ-9**
- **obama + gpc-precursor + Líbia/Síria + MQ-9/F-22**
- **trump + gpc + Soleimani + F-35/USSF/LRASM**
- **biden + gpc/mdo + Ucrânia/Taiwan + HIMARS/AUKUS/Replicator**
- **trump2 + gpc/mdo + Irã 2025/Taiwan + F-35/USSF/Replicator/LRASM**

## Uso
O backend (futuro) mapeia quais sistemas/doutrinas foram empregados por presidente em conflito específico via `data/ontology.json`.
