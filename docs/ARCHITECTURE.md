# RunTechOps — Arquitetura do Sistema

> Documento de referência técnica do projeto RunTechOps. Descreve componentes, modelo de dados, fluxos, convenções e operações.

| Campo | Valor |
|---|---|
| Versão | 1.3 |
| Data | 2026-05-13 |
| Status | Em produção (público temporário) |
| Repositório | `dev-automahub/runnops` (GitHub) |
| URL produção | https://runnops.pages.dev |
| Mantenedor | Oswaldo Junior |
| Stack | Python 3 · SQLite · Cloudflare Pages · Garmin Connect API |

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Princípios de design](#2-princípios-de-design)
3. [Arquitetura de alto nível](#3-arquitetura-de-alto-nível)
4. [Modelo de dados](#4-modelo-de-dados)
5. [Componentes (scripts e responsabilidades)](#5-componentes-scripts-e-responsabilidades)
6. [Fluxos / Pipelines](#6-fluxos--pipelines)
7. [Frontend (dashboard estático)](#7-frontend-dashboard-estático)
8. [Convenções e padrões](#8-convenções-e-padrões)
9. [Operações](#9-operações)
10. [Segurança e privacidade](#10-segurança-e-privacidade)
11. [Limitações conhecidas](#11-limitações-conhecidas)
12. [Roadmap](#12-roadmap)
13. [Glossário](#13-glossário)
14. [Changelog](#14-changelog)

---

## 1. Visão Geral

### 1.1 Propósito

RunTechOps é um pipeline pessoal de coleta + análise + publicação de dados fisiológicos e de treino para acompanhamento do macrociclo de corrida 2026 do atleta. Substitui o uso ad-hoc de planilhas e telas do Garmin Connect / TrainingPeaks por um sistema reprodutível com persistência em SQLite e dashboard público em Cloudflare Pages.

### 1.2 Atleta-alvo (escopo atual)

| Atributo | Valor |
|---|---|
| Idade | 54 |
| Peso | 98 kg |
| FCrep baseline | 51 |
| FCmáx | 170 |
| HRR (FCmáx − FCrep) | 119 |
| Dispositivos | Garmin Forerunner 965 (uso 24/7) |
| Plataformas | Garmin Connect, TrainingPeaks Premium |
| Lesões | nenhuma |
| Carga de força | 3×/semana |

### 1.3 Metas da temporada 2026

| Prova | Data | Meta |
|---|---|---|
| 21K Meia do Rio | 2026-06-06 | conservador 2h13–2h17 |
| 21K race-rehearsal | 2026-07-26 | atacar 2h05–2h10 |
| **Maratona** | **2026-08-30** | **4h00:00 declarada** |

### 1.4 Tarefa principal

Manter um ciclo diário e semanal de: **coletar → analisar → reportar → ajustar**.

---

## 2. Princípios de design

| # | Princípio | Como se manifesta no código |
|---|---|---|
| P1 | **Idempotência** | `INSERT … ON CONFLICT DO UPDATE` em todos os upserts. Reprocessar não duplica nem corrompe. |
| P2 | **Tudo cru preservado** | Coluna `raw_json` em `health_daily` guarda response bruto da API. Extração pode evoluir sem perder dados antigos. |
| P3 | **Single-file dashboard** | `index.html` auto-contido (CSS embutido). Sem build step. Sem JS framework. Cloudflare serve estático. |
| P4 | **Markers preservam edição manual** | Diários têm `<!-- DASH_AUTO_START -->` / `<!-- DASH_AUTO_END -->`. Auto-update só toca entre markers. |
| P5 | **Migrações idempotentes** | `init_db` adiciona colunas faltantes via `ALTER TABLE` controlado. DBs antigos atualizam sem migration script separado. |
| P6 | **Separação dev × conteúdo publicado** | Diário publicado é só saúde/treino. Pendências de dev ficam em memória local, não vão pra `runnops.pages.dev`. |
| P7 | **1 comando rola tudo** | `python health_daily.py` é o entry-point único do pipeline diário. |
| P8 | **Pasta como sistema de log** | `diario/YYYY-MM-DD.md` e `planos-semana/plano-semana-YYYY-Www.md` viraram primary sources legíveis sem ferramenta. |

---

## 3. Arquitetura de alto nível

### 3.1 Diagrama de fluxo

```
┌────────────────────────── EXTERNAL ──────────────────────────┐
│                                                              │
│   Garmin Connect API                  Garmin Connect         │
│   ├── health metrics                  └── workout calendar   │
│   └── activity TCX                                           │
│                                                              │
└──────┬───────────────────────┬────────────────────────┬──────┘
       │                       │                        │
       ▼                       ▼                        ▼
┌──────────────┐      ┌──────────────────┐    ┌────────────────────┐
│ health_daily │      │   lastrun.py     │    │ scheduled_workouts │
│     .py      │      │ (download TCX)   │    │       .py          │
└──────┬───────┘      └────────┬─────────┘    └──────────┬─────────┘
       │                       │                         │
       │ upsert              save                      upsert
       ▼                       ▼                         ▼
┌──────────────┐    ┌──────────────────────┐   ┌────────────────────┐
│ health_daily │    │ Atividades Baixadas/ │   │ scheduled_workout  │
│   (table)    │    │      *.tcx          │    │      (table)       │
└──────┬───────┘    └──────────┬───────────┘   └─────────┬──────────┘
       │                       │                         │
       │              ┌────────┴──────────┐              │
       │              │ aggregate_        │              │
       │              │ activities.py     │              │
       │              └────────┬──────────┘              │
       │                       │                         │
       │              ┌────────┴──────────┐              │
       │              ▼                   ▼              │
       │   session_summary       weekly_summary          │
       │       (table)              (table)              │
       │              │                   │              │
       └──────────────┴─────────┬─────────┴──────────────┘
                                │
                                ▼
                       ┌────────────────┐
                       │ dash_today.py  │ ── lê todos os MDs em diario/
                       │ (Jinja2 render)│
                       └────────┬───────┘
                                │
                                ▼
                          ┌───────────┐
                          │ index.html│ ──┐
                          │activity   │   │
                          │ .html     │   ▼
                          └───────────┘  publish.py
                                          │
                                          ▼
                                    git push → GitHub
                                          │
                                          ▼
                                  Cloudflare Pages
                                          │
                                          ▼
                                runnops.pages.dev
```

### 3.2 Camadas

| Camada | Responsabilidade | Tecnologias |
|---|---|---|
| **Ingestão** | Buscar dados externos (Garmin) | `garminconnect` lib, Python |
| **Persistência** | Armazenar de forma consultável e versionada | SQLite (`runtech.db`) |
| **Agregação** | Derivar métricas de séries brutas | Python puro (sem ORM) |
| **Renderização** | Transformar dados em HTML | Jinja2 + CSS embutido |
| **Publicação** | Deploy estático automatizado | Git + Cloudflare Pages |
| **Conteúdo narrativo** | Análises manuais por dia | Markdown |

---

## 4. Modelo de dados

Persistência local em **`runtech.db`** (SQLite). Gitignored.

### 4.1 Tabela `health_daily`

**Granularidade:** 1 row por data. **PK:** `date` (texto ISO YYYY-MM-DD).
**Origem:** `health_daily.py` (1× por dia, idealmente manhã).

| Coluna | Tipo | Origem (API Garmin) | Descrição |
|---|---|---|---|
| `date` | TEXT PK | — | Data ISO YYYY-MM-DD |
| `sleep_score` | INTEGER | `get_sleep_data().dailySleepDTO.sleepScores.overall.value` | Score Garmin 0-100 |
| `sleep_duration_min` | INTEGER | `dailySleepDTO.sleepTimeSeconds / 60` | Sono total (em min). Não inclui pré-sono não detectado pelo Garmin |
| `sleep_rem_min` | INTEGER | `dailySleepDTO.remSleepSeconds / 60` | Tempo em REM |
| `sleep_deep_min` | INTEGER | `dailySleepDTO.deepSleepSeconds / 60` | Tempo em sono profundo |
| `sleep_light_min` | INTEGER | `dailySleepDTO.lightSleepSeconds / 60` | Tempo em sono leve |
| `sleep_awake_min` | INTEGER | `dailySleepDTO.awakeSleepSeconds / 60` | Tempo acordado durante a noite |
| `hrv_avg_overnight` | REAL | `get_hrv_data().hrvSummary.lastNightAvg` | HRV média noturna em ms |
| `hrv_status` | TEXT | `hrvSummary.status` | BALANCED / UNBALANCED / LOW / POOR |
| `body_battery_max` | INTEGER | derivado de `get_body_battery()` | Pico diário (0-100) |
| `body_battery_min` | INTEGER | derivado | Mínimo diário |
| `body_battery_charged` | INTEGER | `get_body_battery().charged` | Total recarregado no dia |
| `body_battery_drained` | INTEGER | `get_body_battery().drained` | Total consumido |
| `resting_heart_rate` | INTEGER | `get_user_summary().restingHeartRate` | FCrep do dia em bpm |
| `stress_avg` | INTEGER | `averageStressLevel` | Stress médio (0-100) |
| `stress_max` | INTEGER | `maxStressLevel` | Stress máximo |
| `training_readiness` | INTEGER | `get_training_readiness()[0].score` | Disposição Garmin (0-100) |
| `vo2_max` | REAL | `mostRecentVO2Max.generic.vo2MaxValue` | VO2 max running |
| `weight_kg` | REAL | `get_body_composition().totalAverage.weight / 1000` | Peso em kg |
| `steps` | INTEGER | `totalSteps` | Passos do dia |
| `active_calories` | INTEGER | `activeKilocalories` | Calorias ativas |
| **`training_status`** ⭐ | TEXT | `mostRecentTrainingStatus.latestTrainingStatusData.<deviceId>.trainingStatus` → mapeado | MAINTAINING / PRODUCTIVE / RECOVERY / OVERREACHING / UNPRODUCTIVE / DETRAINING |
| **`training_status_feedback`** ⭐ | TEXT | `acuteTrainingLoadDTO.acwrStatus` | OPTIMAL / HIGH / VERY_HIGH / LOW |
| **`acute_load`** ⭐ | REAL | `acuteTrainingLoadDTO.dailyTrainingLoadAcute` | ATL — carga aguda (7d) |
| **`chronic_load_low`** ⭐ | REAL | `acuteTrainingLoadDTO.minTrainingLoadChronic` | Faixa ótima de CTL (mín) |
| **`chronic_load_high`** ⭐ | REAL | `acuteTrainingLoadDTO.maxTrainingLoadChronic` | Faixa ótima de CTL (máx) |
| **`load_ratio`** ⭐ | REAL | `acuteTrainingLoadDTO.dailyAcuteChronicWorkloadRatio` | ACWR (ATL/CTL) |
| **`vo2_max_trend`** ⭐ | TEXT | `trainingStatusFeedbackPhrase` | MAINTAINING_2 / IMPROVING / etc |
| **`fitness_age`** ⭐ | REAL | `get_fitnessage_data().fitnessAge` | Idade fisiológica |
| **`recovery_time_hours`** ⭐ | REAL | `get_training_readiness()[0].recoveryTime / 60` | Horas até próximo treino-chave |
| **`race_predicted_5k_sec`** ⭐ | INTEGER | `get_race_predictions()[-1].time5K` | Predicted 5K (segundos) |
| **`race_predicted_10k_sec`** ⭐ | INTEGER | `get_race_predictions()[-1].time10K` | Predicted 10K |
| **`race_predicted_half_sec`** ⭐ | INTEGER | `timeHalfMarathon` | Predicted 21K |
| **`race_predicted_marathon_sec`** ⭐ | INTEGER | `timeMarathon` | Predicted maratona |
| `fetched_at` | TEXT | local | Timestamp da coleta |
| `raw_json` | TEXT | local | Response cru completo (JSON) |

⭐ = colunas adicionadas em 2026-05-11 (sessão de expansão Garmin).

### 4.2 Tabela `session_summary`

**Granularidade:** 1 row por treino (arquivo TCX). **PK:** `session_id` (texto, extraído do filename).
**Origem:** `aggregate_activities.py`, parseando todos os TCX em `Atividades Baixadas/`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `session_id` | TEXT PK | Garmin activity ID (ex: `22853346305`) |
| `filename` | TEXT | Path relativo do TCX |
| `date_iso` | TEXT | Início (ISO) |
| `week_id` | TEXT | Semana ISO YYYY-Www |
| `sport` | TEXT | Running / Cycling / etc |
| `distance_km` | REAL | Distância total |
| `duration_min` | REAL | Duração total em minutos |
| `avg_hr` | INTEGER | FC média |
| `max_hr` | INTEGER | FC máxima |
| `avg_cadence_spm` | REAL | Cadência média em **spm** (steps per minute) — RunCadence do TCX × 2 |
| `avg_pace_sec_per_km` | REAL | Pace médio em segundos por km |
| `time_z1_sec` … `time_z5_sec` | INTEGER | Tempo em cada zona Karvonen, em segundos |
| **`scheduled_id`** ⭐ | INTEGER | FK lógica pra `scheduled_workout.scheduled_id`. NULL quando não há match (treino sem agendamento ou date drift) |
| **`workout_code`** ⭐ | TEXT | Código extraído do título (LR7/FFR4/RRe5/HRR4/RHR6/RFF5/AEM/VO2/etc) |

⭐ = colunas adicionadas em 2026-05-13 (Gap #2: matching planejado vs executado).

**Karvonen zones** computadas com `FC_MAX=170`, `FC_REP=51`, `HRR=119`:

| Zona | Faixa (bpm) | Fórmula |
|---|---|---|
| Z1 | 51–122 | FCrep + (0-60% × HRR) |
| Z2 | 122–133 | FCrep + (60-70% × HRR) |
| Z3 | 134–145 | FCrep + (70-80% × HRR) |
| Z4 | 146–157 | FCrep + (80-90% × HRR) |
| Z5 | 158–170 | FCrep + (90-100% × HRR) |

### 4.3 Tabela `weekly_summary`

**Granularidade:** 1 row por semana ISO. **PK:** `week_id` (ex: `2026-W20`).
**Origem:** derivada de `session_summary` pelo `aggregate_activities.py`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `week_id` | TEXT PK | ISO YYYY-Www |
| `week_start_iso` | TEXT | Data da segunda-feira |
| `sessions_count` | INTEGER | Treinos da semana |
| `total_distance_km` | REAL | Volume |
| `total_duration_min` | REAL | Tempo total |
| `avg_hr` | INTEGER | FC média ponderada por duração |
| `avg_cadence_spm` | REAL | Cadência média ponderada por duração |
| `avg_pace_sec_per_km` | REAL | Pace médio |
| `time_z1_sec` … `time_z5_sec` | INTEGER | Total em cada zona |
| `pct_z2` | REAL | % do tempo total em Z2 (Z2_sec / sum(Z1..Z5)) |
| `longest_session_km` | REAL | Maior treino da semana |
| `longest_session_id` | TEXT | ID do maior |

### 4.4 Tabela `scheduled_workout` ⭐ (12/05/2026)

**Granularidade:** 1 row por treino agendado no calendário Garmin Connect. **PK:** `scheduled_id`.
**Origem:** `scheduled_workouts.py`, via `Garmin.get_scheduled_workouts(year, month)`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `scheduled_id` | INTEGER PK | ID do scheduling (não o workout) |
| `workout_id` | INTEGER | ID do template do workout |
| `date_iso` | TEXT | Data agendada (YYYY-MM-DD) |
| `week_id` | TEXT | ISO YYYY-Www da data |
| `title` | TEXT | Título do treino (ex: "FFR4 Corrida - 10' Z3") |
| `sport` | TEXT | running / cycling / etc |
| `fetched_at` | TEXT | Timestamp da coleta |

### 4.5 Relações conceituais (não FKs)

```
health_daily      1 ─── 1   diario/YYYY-MM-DD.md       (via date == ISO do nome)
weekly_summary    1 ─── 1   planos-semana/W<week>.md   (via week_id)
session_summary   N ──┬── 1   weekly_summary           (via week_id)
                      ├── 1   TCX file                 (via session_id)
                      └── 0..1 scheduled_workout       (via session_summary.scheduled_id)
```

> **Nota:** SQLite não tem FKs explícitas no schema atual. Relações são lógicas, mantidas em código.

### 4.6 Matching planejado vs executado (Gap #2 resolvido em 13/05/2026)

`aggregate_activities.py` faz um pass de matching após upsertar `session_summary`:

1. Para cada session, extrai `workout_code` do filename via regex (`LR7`, `FFR4`, `RRe5`, `HRR4`, `RHR6`, `RFF5`, `AEM`, `VO2`, etc.)
2. Busca `scheduled_workout` com `date_iso` == data da session (parte YYYY-MM-DD)
3. Se 1 candidato → match direto. Se N candidatos → match por `workout_code` igual. Fallback: primeiro candidato.
4. Persiste em `session_summary.scheduled_id`

**Limitação conhecida — date drift histórico:** treinos executados fora da data agendada (ex: coach replaneja, atleta desloca para o dia seguinte) ficam unmatched. Forward, quando o treino é executado na data agendada, o match é automático.

**Uso no dashboard:** o card "PLANO DA SEMANA" usa o match pra:
- Marcar treino como ✅ feito + mostrar métricas reais (km, FC, cadência, pace)
- Calcular **% Aderência** ((feito) / (feito + não executado))
- Diferenciar status: ✅ feito · 🔵 HOJE · ⚪ não executado (passado sem match) · ⏳ pendente (futuro)

---

## 5. Componentes (scripts e responsabilidades)

### 5.1 Coleta e ingestão

| Script | Função | Roda quando | Entrada | Saída |
|---|---|---|---|---|
| `health_daily.py` | Coleta diária Garmin → `health_daily` table + hook | manhã, 1×/dia | `.env` (creds) | `runtech.db`, dispara `dash_today.py` |
| `lastrun.py` | Baixa último(s) TCX da Garmin Connect | sob demanda (após cada treino) | `.env` | `Atividades Baixadas/*.tcx` |
| `scheduled_workouts.py` | Baixa calendário (workouts agendados) | terça-feira (rotina) | `.env`, `--weeks N` | `runtech.db` (`scheduled_workout`), `planos-semana/*.md` |
| `aggregate_activities.py` | Agrega TCX → `session_summary` + `weekly_summary` | automático no pipeline de `health_daily.py` | `Atividades Baixadas/*.tcx` | `runtech.db` |
| `conn.py` | Teste rápido de conexão | sob demanda (debugging) | `.env` | stdout |

### 5.2 Renderização

| Script | Função | Roda quando | Entrada | Saída |
|---|---|---|---|---|
| `dash_today.py` | Orquestra render do dashboard | automático após `health_daily.py` | `runtech.db`, MDs do diário | `index.html`, `activities.json`, opcionalmente atualiza diário |
| `dash_data.py` | Camada de queries SQLite + parsing | importado por `dash_render.py` | `runtech.db`, MDs | dicts |
| `dash_verdict.py` | Lógica do veredito (HRV/BB/FCrep/Sleep + modifiers) | importado | row do dia + dia anterior | dict {color, headline, subtitle} |
| `dash_render.py` | Jinja2 + sparklines SVG + BB curve | importado | contexto enriquecido | HTML string |
| `dash_journal.py` | Auto-update do AUTO section de `diario/*.md` | chamado por `dash_today.py` | row do dia | atualiza MD |
| `dash_glossary.py` | Lista de termos do glossário | importado | — | lista de dicts |
| `dash_activities.py` | Manifest de TCX disponíveis | chamado por `dash_today.py` | `Atividades Baixadas/*.tcx` | `activities.json` |
| `dash_template.html` | Template Jinja2 (5 abas) | renderizado | contexto | HTML |
| `dash_styles.css` | Estilos (embedded no HTML final) | lido pelo render | — | CSS |

### 5.3 Publicação

| Script | Função | Saída |
|---|---|---|
| `publish.py` | `git status --porcelain` → categoriza mudanças → commit + push | mensagem `auto: publish <scope> (timestamp)` |

### 5.4 Frontend standalone

| Arquivo | Função |
|---|---|
| `activity.html` | Página standalone que parseia TCX no browser e renderiza mapa (Leaflet) + gráficos (Plotly) |
| `activities.json` | Manifest consumido por `activity.html` (lista de atividades + paths) |

### 5.5 Testes

| Arquivo | Cobertura |
|---|---|
| `test_dash.py` | 24 smoke tests: verdict logic, deltas, sparklines, render empty state, stale banner, override flags |

---

## 6. Fluxos / Pipelines

### 6.1 Pipeline diário (manhã)

```
1× comando manual:
$ python health_daily.py
```

Sequência interna:
1. Login Garmin via `garminconnect` lib
2. Coleta endpoints do dia: sleep, hrv, bb, summary, readiness, max_metrics, body_comp, training_status, race_predictions, fitnessage
3. Upsert em `health_daily` (com `raw_json` cru preservado)
4. **Hook 1:** `aggregate_activities.py` → reagrega TCX (idempotente)
5. **Hook 2:** `dash_today.py` → atualiza diário MD (entre markers), regenera `index.html`, regenera `activities.json`
6. **Hook 3:** `publish.py` → commit + push se houver diff

Modos opcionais:
- `--no-publish`: pula hook 3
- `--quiet`: pula todos os hooks
- `--backfill N`: coleta últimos N dias (sem hooks)
- `--backfill-from YYYY-MM-DD`: coleta de data X até hoje

### 6.2 Pipeline semanal (terça-feira de manhã — rotina)

```
$ python scheduled_workouts.py
```

1. Login Garmin
2. Determina semana atual + próxima (configurável via `--weeks N`)
3. Chama `get_scheduled_workouts(year, month)` para cada mês envolvido
4. Filtra `itemType == "workout"` dentro da janela
5. Upsert em `scheduled_workout`
6. Gera MD por semana em `2026-05-04-protocolo.../planos-semana/plano-semana-YYYY-Www.md`
7. Imprime resumo no terminal

### 6.3 Pipeline pós-treino (sob demanda)

```
$ python lastrun.py
```

1. Baixa o TCX da última atividade da Garmin Connect
2. Salva em `Atividades Baixadas/<activityId>_<title>.tcx`

(Em rodadas futuras de `health_daily.py`, o aggregator pegará o TCX automaticamente.)

### 6.4 Pipeline de edição manual de diário

1. Usuário edita `diario/YYYY-MM-DD.md` fora dos markers
2. `$ python publish.py` (manual) ou aguarda próxima rodada de `health_daily.py`
3. Site atualiza

### 6.5 Estados do CI

Não há CI próprio. Cloudflare Pages observa o branch `main` no GitHub e republica em ~30s a cada push.

---

## 7. Frontend (dashboard estático)

### 7.1 Estrutura de abas

URL principal: `https://runnops.pages.dev` → `index.html`

| Aba | Mecanismo | Conteúdo |
|---|---|---|
| **HOJE** | radio button + CSS `:checked` (sem JS) | Reportagem matinal, Veredito, Próximo Treino, Pills, Plano da Semana, Sono por fase, HRV sparkline, Performance Garmin, Resumo Semanal |
| **TRENDS** | radio button | 5 sparklines (HRV/SONO/BB/FCREP/READY) + Correlações |
| **HISTÓRICO** | radio button | Tabela ordenável + Análises diárias (MDs renderizados) |
| **GLOSSÁRIO** | radio button | Definições dos termos |
| **TREINOS** | `<a href="activity.html">` | Página standalone com mapa + gráficos por TCX |

### 7.2 Componentes da aba HOJE (ordem visual)

1. **Veredito** — hero pill colorido (verde/amber/laranja/vermelho) com headline + subtitle
2. **Próximo treino** — banner pequeno com data + título (lê `scheduled_workout` onde `date_iso >= hoje`)
3. **Pills 2×2** — Sono / Body Battery / FCrep / Disposição (com delta vs ontem)
4. **Plano da semana** — lista com status ✅ feito / 🔵 HOJE / ⚪ não executado / ⏳ pendente; quando matched, mostra métricas reais (km · FC · cadência · pace); contador no topo + **% Aderência** quando há treinos avaliados
5. **Sono por fase** — barra estratificada REM/Deep/Light/Awake
6. **HRV hero** — número grande + sparkline 7d
7. **Performance Garmin** — 4 cards (Training Status, ACWR/ATL/CTL, VO2/Fitness Age, Recovery) + grid Race Predictor color-coded
8. **Resumo semanal** — tabela das últimas 8 semanas com deltas

### 7.3 `activity.html` (página standalone)

Parsing client-side via `DOMParser` nativo (sem build step):

| Lib | CDN | Função |
|---|---|---|
| Leaflet 1.9 | unpkg | Mapa com rota colorida por zona de FC |
| Plotly 2.35 | cdn.plot.ly | Elevação, FC + zonas, distribuição, cadência (banda alvo), pace (eixo invertido) |

Constantes Karvonen embutidas no JS:
```javascript
const FC_MAX = 170;
const FC_REP = 51;
```

### 7.4 Decisões técnicas de frontend

| Decisão | Motivação |
|---|---|
| HTML single-file | Cloudflare Pages serve estático puro. Sem build. Sem cache busting. |
| CSS embutido | Eliminar 1 round-trip de download. Render local funciona offline. |
| Sem JS framework | Dashboard simples não justifica overhead. JS é só vanilla para tabela sortable + hash navigation. |
| Tabs com radio + CSS `:checked` | Funciona em qualquer viewer (incl. OneDrive web). Sem JS necessário. |
| `<details>` para journals antigos | HTML nativo, sem JS, com fallback gracioso em viewers limitados. |
| `r` em SVG circles | Compatibilidade com viewers antigos (não confia só em CSS) |

---

## 8. Convenções e padrões

### 8.1 Datas e tempo

- **ISO 8601 em todo lugar:** `YYYY-MM-DD` para datas, `YYYY-MM-DDTHH:MM:SS` para timestamps.
- **Datas BR só na renderização** (`dd/mm/yyyy`).
- **Semana ISO:** `YYYY-Www` (ex: `2026-W20`). Segunda-feira = início da semana.
- **Timezone:** assume `America/Sao_Paulo`. Garmin retorna UTC para alguns endpoints.

### 8.2 Naming

| Tipo | Padrão | Exemplo |
|---|---|---|
| Tabela SQLite | snake_case | `health_daily`, `weekly_summary` |
| Colunas | snake_case com unidade no nome quando ambíguo | `sleep_duration_min`, `acute_load`, `race_predicted_marathon_sec` |
| Script Python | snake_case | `aggregate_activities.py`, `dash_today.py` |
| Arquivo MD | `<categoria>-<chave>.md` | `diario/2026-05-12.md`, `planos-semana/plano-semana-2026-W20.md` |
| Memory | `<type>_<assunto>.md` | `feedback_estilo_trabalho.md`, `project_runtechops.md` |
| Commits | `auto: publish <scope> (timestamp)` ou Conventional Commits | gerados pelo `publish.py` |

### 8.3 Cadência

⚠️ **Atenção crítica:** TCX armazena cadência como **strides/minute** (uma perna). Tanto `<tcx:Cadence>` quanto `<ns3:RunCadence>`. Para obter **spm (steps per minute)**, **multiplicar por 2**. Esquecer essa conversão é o bug mais provável ao adicionar nova análise de cadência.

### 8.4 Tipos de treino (prefixos no título)

Inferidos do título do `scheduled_workout`:

| Prefixo | Tipo |
|---|---|
| LR | Long Run |
| RR / RRe | Recovery Run |
| FFR | Fast Finish Run / Z3 |
| HRR | High HR Reps / sprints |
| RF | Recovery / Filler |
| AEM | Aerobic Endurance Maintenance |

### 8.5 Idempotência

- Todos os scripts de coleta usam upsert (`ON CONFLICT DO UPDATE`).
- `init_db` adiciona colunas faltantes via `ALTER TABLE ADD COLUMN` (ignorando "duplicate column").
- `aggregate_activities.py` reprocessa todos os TCX a cada run.
- Diário MD: re-rodar `dash_today.py` só atualiza entre markers.

### 8.6 Separação dev × conteúdo publicado

**Regra firmada em 11/05/2026:** o conteúdo publicado em `runnops.pages.dev` (diário, dashboard) é **só sobre saúde, fisiologia e treinos**. Pendências e história do desenvolvimento do RunTechOps ficam em memória local e em `docs/`, não vão pro diário do dia.

---

## 9. Operações

### 9.1 SOP — Fluxo diário do atleta

Este é o **procedimento operacional padrão** acordado em 13/05/2026. Define o ciclo de coleta + reportagem que o atleta executa todo dia, com variações conforme o tipo de dia.

#### 9.1.1 Dia sem treino

```powershell
# 1. Acordou → sincronizou relógio com Garmin Connect (auto no app)
# 2. Roda 1 comando:
python health_daily.py
# 3. Avisa no chat: "rodei o daily"
```

Internamente, o `health_daily.py` (em 1 comando) faz:
- coleta endpoints do Garmin → upsert em `health_daily`
- `aggregate_activities.py` (re-agrega TCX existentes, idempotente)
- `dash_today.py` (gera `index.html`, atualiza auto-section do diário)
- `publish.py` (commit + push → Cloudflare republica em ~30s)

#### 9.1.2 Dia com treino

```powershell
# 1. Sincronizou relógio + treino com Garmin Connect
# 2. Baixa o TCX:
python lastrun.py 1
# 3. DEPOIS roda o pipeline completo:
python health_daily.py
# 4. Avisa no chat: "rodei o daily e o lastrun, treino X feito"
```

⚠️ **A ordem `lastrun` → `health_daily` é crítica.** O aggregator dentro do `health_daily.py` só vê arquivos TCX que estão presentes na pasta `Atividades Baixadas/` no momento que ele roda. Se a ordem for invertida:
- O dado de health do dia entra normalmente
- Mas o TCX novo fica órfão até a próxima rodada de `health_daily.py`
- O Plano da Semana não marca o treino como ✅ feito até lá

**Workaround se inverter:** rodar `python aggregate_activities.py; python dash_today.py --no-open; python publish.py` separadamente.

#### 9.1.3 Terça-feira (rotina semanal — adicional)

```powershell
# Depois que o coach publicou o plano da semana no Garmin Connect
python scheduled_workouts.py
# Avisa no chat: "rodei o scheduled também"
```

Output: `runtech.db.scheduled_workout` atualizado + MD em `2026-05-04-protocolo.../planos-semana/plano-semana-YYYY-Www.md`.

Se o coach não publicou ainda → calendário vazio, cobrar antes do primeiro treino da semana.

#### 9.1.4 O que o assistente (Claude) faz quando recebe o aviso

**Procedimento detalhado:** ver `memory/feedback_analise_narrativa_sop.md` (10 pre-flight checks → decision tree PATH A treino / PATH B sem treino → templates das 3 seções narrativas → pipeline final).

Resumo:

1. **Pre-flight (10 checks):** dia da semana (força seg/qua/sex?), diário hoje, diário ontem, plano da semana, TCX novo(s), fator força do dia, tendência cadência, estado Garmin avançado (ACWR/Race Predictor), próximo treino, veredito auto
2. **Branch:**
   - **PATH A (tem TCX novo):** análise pós-treino — tabela alvo×real, distribuição Karvonen, estrutura por laps, espelho honesto (acertos + furos), veredito do dia
   - **PATH B (sem TCX):** análise de recuperação + leitura do calendário + **recomendação concreta** pro próximo treino baseada no quadro fisiológico atual
3. **Escreve 3 seções narrativas** do diário fora dos markers AUTO: `O que aconteceu`, `Decisão / Veredito`, `Pendências`
4. **Pipeline final:** `aggregate_activities.py` → `dash_today.py --no-open` → `publish.py`
5. **Responde no chat** com resumo (insight principal, próximo treino, alerta se merece atenção)

#### 9.1.5 Fator FORÇA (cruzamento obrigatório)

Atleta treina **força 3×/semana**:

| Dia | Sessão | Tipo |
|---|---|---|
| Seg | A | MMII pesado (agachamento, RDL, hip thrust, panturrilha, core) |
| Qua | B | Upper + core (NÃO MMII pesado) |
| Sex | C | Funcional unilateral |

A análise narrativa **sempre cruza com o fator força** quando o dia é seg/qua/sex. Atleta registra força no Garmin Connect (declarado 13/05/2026); se ele rodar `python lastrun.py 1` no dia, **só pega a corrida** (último TCX). Para baixar run + força: `python lastrun.py 2` (ou mais).

Até 13/05/2026, **38 TCXs no DB são todos `sport='Running'`** — força ainda não foi capturada. Quando surgir TCX `sport='StrengthTraining'` ou similar, aggregator não inclui em `weekly_summary` (filtra por `distance > 0`), mas o assistente pode ler o arquivo direto pra análise.

#### 9.1.6 Princípios de fronteira

- **Diário publicado é só saúde/treino.** Dev fica em memória local e chat (regra firmada em 11/05/2026 — ver `feedback_separacao_dev_vs_conteudo.md`).
- **Espelho, não cheerleader.** Contrato de coaching firmado em 06/05/2026: análises honestas, sem suavizar furos. Se for hora de cobrar cadência, cobra. Se a meta 4h00 começar a parecer inviável, falar abertamente.
- **Não pedir o que já está no diário.** Reportagem matinal completa vem no auto-section; análise narrativa parte daí.

### 9.2 Setup inicial

Detalhes em `SETUP.md`. Resumo:

```powershell
cd "C:\_Dados\OneDrive - GS Comercio Internacional\Jr\Pesq_Jr\RunTechOps"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# editar .env com GARMIN_EMAIL e GARMIN_PASSWORD
```

### 9.3 Operação diária

```powershell
.\.venv\Scripts\Activate.ps1
python health_daily.py
```

### 9.4 Operação semanal (terça)

```powershell
python scheduled_workouts.py
```

### 9.5 Pós-treino

```powershell
python lastrun.py            # baixa último TCX
python health_daily.py       # re-coleta + agrega + publica (ou só publish.py se daily já rodou)
```

### 9.6 Comandos úteis

| Comando | Função |
|---|---|
| `python health_daily.py --backfill 7` | Backfill 7 dias |
| `python health_daily.py --no-publish` | Só local, não publica |
| `python dash_today.py --no-open` | Regera HTML, não abre browser |
| `python dash_today.py --no-journal` | Não reescreve AUTO section do diário (mas continua lendo diários pro dashboard) |
| `python publish.py --dry-run` | Preview de mudanças sem committar |
| `python aggregate_activities.py` | Reagrega TCX manualmente |
| `python test_dash.py` | Roda 24 smoke tests |

### 9.7 Troubleshooting

| Sintoma | Causa provável | Resolução |
|---|---|---|
| `mobile+cffi returned 429: rate limited` | Login concorrente ou muitas requests | Aguardar 1-5 min e tentar de novo. Login eventualmente passa após retry interno da lib. |
| `no such column: training_status` | DB antigo sem migração | Rodar `python health_daily.py` (passa por `init_db` que adiciona colunas faltantes) |
| Diário do dia não aparece no dashboard | Cache do browser ou MD não está entre markers | Hard refresh (Ctrl+Shift+R); confirmar markers `<!-- DASH_AUTO_START -->` no MD |
| Cadência semanal vindo metade do esperado | Bug de conversão strides→spm | Verificar que extraction multiplica por 2 |
| Race Predictor sem valor | API retornou erro | Olhar `raw_json.get_race_predictions_error` no health_daily |

### 9.8 Limitações de rate

A `garminconnect` lib tem retry interno mas Garmin Connect aplica rate limit a IPs. Em sessões de dev intensivas, esperar ~30s entre runs.

---

## 10. Segurança e privacidade

### 10.1 Segredos

| Arquivo | Conteúdo | Status |
|---|---|---|
| `.env` | `GARMIN_EMAIL`, `GARMIN_PASSWORD` | gitignored |
| `runtech.db` | Métricas de saúde + raw JSON | gitignored |
| `lastrun_log.txt`, `garmin_activity_data.csv` | logs intermediários | gitignored |

### 10.2 Privacidade atual

**Status:** Repositório GitHub **público temporário**. Cloudflare Pages **público sem autenticação**.

| Dado | Visível publicamente? |
|---|---|
| Métricas health agregadas (HRV/Sono/BB/FCrep) | ✅ Sim (no dashboard) |
| Veredito + análises do diário | ✅ Sim |
| Race Predictor + gap pra meta | ✅ Sim |
| Cadência, pace, zonas de cada treino | ✅ Sim |
| **GPS routes dos TCX (rota da casa/trabalho)** | ⚠️ **SIM — visíveis em `activity.html`** |
| .env e runtech.db | ❌ Não (gitignored) |

### 10.3 Plano de migração pra privado

Quando dashboard estabilizar (~1 semana sem mudanças visuais):

1. GitHub repo → Settings → Change visibility → **Private**
2. Cloudflare Pages → projeto → Settings → Access policy → adicionar `dev@gsinternacional.com.br`
3. Opcional: `git filter-repo --path 'Atividades Baixadas' --invert-paths` para limpar TCXs do histórico do git
4. Site fica com proteção magic link / Google login

---

## 11. Limitações conhecidas

### 11.1 Garmin Connect API

- **Não-oficial:** `garminconnect` é client community-driven baseado em reverse engineering. Pode quebrar em mudanças na API.
- **Sem TLS de longo prazo:** OAuth token expira; lib renova automaticamente.
- **Rate limit:** ~429 ocasional.
- **Sleep tracking:** Garmin não conta primeiro ciclo de "pré-sono" (dormiu cedo → acordou → voltou a dormir). O `sleep_duration_min` reflete só o segundo bloco.

### 11.2 Pipeline

- **Sem trigger automático:** depende do usuário rodar `python health_daily.py` manualmente. Windows Task Scheduler está no roadmap.
- **Sem retry resiliente:** se 1 endpoint falha, o dado vai como `None`. O `raw_json` preserva o erro mas não há retry automatizado.
- **Aggregator full re-scan:** parseia todos os TCX a cada run (~10s pra 38 arquivos; OK até ~200).

### 11.3 Dashboard

- **Trends 30d/90d toggle não funcional:** só 7d funciona. Pendente.
- **Correlações:** placeholder até 14+ dias coletados.
- **`activity.html`** depende de CDN externo (Leaflet + Plotly). Offline parcial.

### 11.4 Tests

- Não há tests pra coleta (mockando Garmin API). Só smoke tests do render.
- `aggregate_activities.py` não tem tests.
- `scheduled_workouts.py` não tem tests.

---

## 12. Roadmap

### 12.1 Curto prazo (esta + próxima semana)

| Item | Status |
|---|---|
| Gap #2: matching planejado vs executado (`session_summary.scheduled_id`) | ✅ feito 13/05 (forward sempre, histórico parcial por date drift) |
| Gap #5: tag de tipo de treino — `workout_code` já extraído | 🟡 parcial — falta agregação por tipo em `weekly_summary` |
| Trends 30d/90d toggle funcional | Baixa-média |

### 12.2 Médio prazo (após 22/05 — 14+ dias coletados)

| Item | Prioridade |
|---|---|
| Gap #3: Race Predictor temporal (trend chart) | Alta |
| Correlações Pearson reais na aba TRENDS | Média |
| `tp_import.py` (TrainingPeaks CSV) | Média |

### 12.3 Longo prazo

| Item | Prioridade |
|---|---|
| Repo virar privado + Cloudflare Access | Alta quando estabilizar |
| Telegram daily notifications | Baixa |
| Windows Task Scheduler (auto-run 06:00) | Baixa |
| `git filter-repo` pra limpar TCXs do histórico | Alta se virar privado |

### 12.4 Decidido NÃO fazer

| Item | Motivo |
|---|---|
| `pmc.py` customizado (CTL/ATL/TSB) | Garmin já entrega via `acuteTrainingLoadDTO` |
| MCP server | Já temos pipeline mais completo |

---

## 13. Glossário

| Termo | Definição |
|---|---|
| **ACWR** | Acute:Chronic Workload Ratio. Razão ATL/CTL. Faixa ótima 0.8–1.3. Indica risco de lesão por sobrecarga. |
| **ATL** | Acute Training Load. Carga de treino dos últimos ~7 dias. Garmin computa. |
| **BB** | Body Battery (0-100). Estado de energia agregado do Garmin baseado em HRV, atividade, sono. |
| **Cadência** | Passos por minuto (spm). Alvo da temporada: 160-165. |
| **CTL** | Chronic Training Load. Carga acumulada de ~42 dias. Proxy de "fitness". |
| **FCrep** | Frequência cardíaca de repouso. Baseline do atleta: 51 bpm. |
| **FCmáx** | FC máxima. 170 bpm. |
| **FFR** | Fast Finish Run. Treino de tempo finalizando em Z3. |
| **HRR** | (1) Heart Rate Reserve = FCmáx − FCrep = 119. (2) High HR Reps (tipo de treino com sprints Z5). |
| **HRV** | Heart Rate Variability. Variação entre batimentos. Alvo: ≥32 ms (RMSSD overnight). |
| **Karvonen** | Fórmula de zonas: FCalvo = FCrep + %HRR. |
| **LR** | Long Run (longão). |
| **PMC** | Performance Management Chart (TrainingPeaks). Composta de CTL, ATL e TSB. |
| **RR** | Recovery Run. |
| **Race Predictor** | Garmin estima tempo de prova a partir de fitness atual (VO2 + lactate threshold). |
| **TSB** | Training Stress Balance = CTL − ATL. Indicador de forma. |
| **Z1-Z5** | Zonas Karvonen 1 a 5. Z2 = base aeróbico (alvo de 80% do volume). |

---

## 14. Changelog

### 1.3 (2026-05-13 — noite)

**Marco:** SOP da análise narrativa codificado (caminho pra virar skill).

- Memory `feedback_analise_narrativa_sop.md` v1: 10 pre-flight checks + decision tree PATH A/B + fator FORÇA + templates de output das 3 seções + princípios + roadmap pra skill formal
- Seção 9.1.4 da doc expandida com resumo do procedimento
- Nova seção 9.1.5 — Fator FORÇA (cruzamento obrigatório seg/qua/sex)
- Confirmado em 13/05 que **atleta registra força no Garmin** mas `lastrun.py 1` só pega o último TCX; recomendação: `lastrun.py 2` em dias com run + força
- Princípios de fronteira renumerados pra 9.1.6

### 1.2 (2026-05-13 — final do dia)

**Marco:** SOP diário formalizado.

- Nova seção `9.1 SOP — Fluxo diário do atleta` com sub-seções 9.1.1 a 9.1.5 cobrindo: dia sem treino, dia com treino (ordem `lastrun` → `health_daily` crítica), rotina de terça, contraparte do assistente, princípios de fronteira
- Memory `feedback_sop_diario_atleta.md` codificando o acordo entre atleta e assistente
- Renumeração: antiga `9.2-9.7` virou `9.3-9.8`

### 1.1 (2026-05-13)

**Marco:** Gap #2 resolvido — matching planejado vs executado.

- `session_summary` ganhou colunas `scheduled_id` (FK lógica) e `workout_code` (LR7/FFR4/etc extraído via regex)
- `aggregate_activities.py` faz pass de matching pós-upsert (mesma data, prefere match por código quando há ambiguidade)
- `scheduled_workouts.py` ganhou `--backfill-months N` pra puxar histórico
- Plano da Semana no dashboard agora mostra: status enriquecido (✅/🔵/⚪/⏳), métricas reais quando match (km · FC · cadência · pace), e **% Aderência**
- Limitação documentada: matching histórico parcial por date drift; forward funciona limpo

### 1.0 (2026-05-12)

**Marco:** Documento criado.

Snapshot consolidado da arquitetura após:
- 11/05: expansão Garmin (Training Status, ATL/CTL/ACWR, Race Predictor, Recovery)
- 12/05: `scheduled_workouts.py` + Próximo Treino + Plano da Semana no dashboard
- Bug fix: `--no-journal` no `dash_today.py`

**Componentes em produção:**
- 5 scripts de coleta/agregação (`health_daily`, `lastrun`, `scheduled_workouts`, `aggregate_activities`, `conn`)
- 8 módulos de renderização (`dash_*.py`)
- 4 tabelas SQLite (`health_daily`, `session_summary`, `weekly_summary`, `scheduled_workout`)
- Frontend de 5 abas + página standalone `activity.html`
- 38 TCX agregados, 13 semanas
- 24 smoke tests passando

---

*Documento mantido em sincronia com o código. Atualizar a cada mudança estrutural.*
