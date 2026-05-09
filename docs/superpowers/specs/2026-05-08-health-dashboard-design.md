# Health Dashboard — Design Spec

**Data:** 2026-05-08
**Autor:** Claude (Opus 4.7) + usuário (validação iterativa)
**Status:** approved by user · pronto para writing-plans
**Projeto:** RunTechOps
**Path-alvo:** `RunTechOps/dash_today.py` + `dash_template.html` + `dash_styles.css`

---

## 1. Propósito

Painel matinal pessoal que mostra os indicadores coletados pelo `health_daily.py` (Garmin Connect → SQLite `runtech.db`), com estética iOS Health refinada e um **veredito do dia** computado automaticamente a partir das métricas-chave do atleta.

**Caso de uso primário:** após reportagem matinal (~6h30-7h00), o atleta abre o dashboard, lê o veredito e métricas em ~10 segundos, decide a sessão de treino do dia.

**Não-objetivos:**
- Substituir `dashboard.py` existente (que renderiza atividades TCX com mapa, FC, splits)
- Editar/inserir dados (read-only sobre `runtech.db`)
- Análise estatística profunda (correlações são heurísticas leves, não modelos)

---

## 2. Decisões fechadas no brainstorming

| # | Decisão | Escolha |
|---|---|---|
| 1 | Estética visual | iOS Health (claro, hero metric grande, color cards) |
| 2 | Escopo de telas | C′ — 3 abas: **Hoje · Trends · Histórico** (sem aba Atividades — coexiste com `dashboard.py`) |
| 3 | Stack | Python gera HTML estático via Jinja2; abre no browser |
| 4 | Lógica de veredito | Auto-rule por threshold + override manual via flag |
| 5 | Limiar HRV crítico | < 26 ms (suavizado de < 28 após validação contra leitura humana) |

---

## 3. Arquitetura e fluxo de dados

```
┌─────────────────────┐
│  health_daily.py    │  já existe
│  Garmin → DB        │
└──────────┬──────────┘
           ↓ writes
      runtech.db
           ↑ reads
┌──────────┴──────────┐
│  dash_today.py      │  NOVO
│  • le ultimos 30d   │
│  • aplica regra     │
│    do veredito      │
│  • renderiza Jinja2 │
│  • abre no browser  │
└──────────┬──────────┘
           ↓ writes
       dash.html
```

### Fluxo de uso na manhã

```
python health_daily.py        # coleta Garmin
python dash_today.py          # gera + abre dash.html
# (ou ambos via 1 comando — ver Seção 8)
```

### Estrutura de arquivos novos

```
RunTechOps/
  dash_today.py            # script principal (gerador)
  dash_template.html       # template Jinja2 com placeholders
  dash_styles.css          # CSS extraído (mantém HTML legível)
  dash.html                # OUTPUT (gitignored)
  dash_archive/            # OPCIONAL: snapshots dash-YYYY-MM-DD.html
  test_dash.py             # smoke tests
```

### Dependência nova

`Jinja2 >= 3.1` — adicionar ao `requirements.txt`.

---

## 4. Lógica do veredito

### 4.1 Tabela de sinais

Cada métrica é classificada em 0/1/2 pontos:

| Métrica | 🟢 0 pts | 🟡 1 pt | 🔴 2 pts |
|---|---|---|---|
| **HRV overnight** | ≥ 32 ms | 26–31 ms | < 26 ms |
| **BB max** | ≥ 65 | 50–64 | < 50 |
| **FCrep** | ≤ 52 bpm | 53–54 | ≥ 55 |
| **Sleep Score** | ≥ 75 | 60–74 | < 60 |

**Tratamento de NULL:** se um valor é NULL, a métrica é **excluída do score** (não soma 0, não soma 2 — é ignorada). Isso evita falsos vermelhos quando o sensor não capturou (típico em dia 1 de coleta). Headline da sub-mensagem cita: "X de 4 métricas avaliadas" se houver gaps.

### 4.2 Modificadores contextuais

Somam ao total se condição satisfeita:

- **HRV caiu ≥ 5 ms vs ontem** → +1 ponto
- **FCrep subiu ≥ 3 bpm vs baseline 51** → +1 ponto

### 4.3 Mapa pontos → veredito

| Total | Cor | Headline | Sub-mensagem |
|---|---|---|---|
| **0** | 🟢 verde | Pronto pra treinar | "Sinais coerentes. Executa o plano." |
| **1–2** | 🟡 amarelo | Atenção: prioriza Z2 | Aponta a métrica pior (ex: "BB 54 abaixo do ideal") |
| **3–4** | 🟠 laranja | Descanso recomendado | Aponta as 2 piores métricas |
| **5+** | 🔴 vermelho | Corte forçado | "Múltiplos sinais críticos. Off hoje." |

**Caso degenerate (< 2 métricas avaliáveis):** se NULL deixa menos de 2 métricas no score, veredito vira ⚪ cinza com headline "Dados insuficientes" e sub-mensagem "X de 4 métricas coletadas. Reporta amanhã pra avaliação." Não força verde nem vermelho — apenas reconhece a falta de sinal.

### 4.4 Validação contra dados reais (08/05)

| Métrica | Valor | Pontos |
|---|---|---|
| HRV 27 ms | 26-31 → 🟡 | 1 |
| BB max 54 | 50-64 → 🟡 | 1 |
| FCrep 53 | 53-54 → 🟡 | 1 |
| Sleep Score 78 | ≥ 75 → 🟢 | 0 |
| HRV caiu 7 ms (34→27) | modifier | +1 |
| FCrep subiu 2 bpm | < 3 → não dispara | 0 |
| **TOTAL** | | **4** |

→ **🟠 Descanso recomendado** — coincide com leitura humana feita de manhã.

### 4.5 Replay de validação obrigatório (parte de testing)

Antes de declarar pronto, rodar veredito sobre os 4 dias coletados (05–08/05) e comparar com leitura humana documentada nos diários:

| Data | HRV | BB | FCrep | Sleep | HRV-Δ | Score | Veredito esperado |
|---|---|---|---|---|---|---|---|
| 05/05 | 29 (1) | 29 (2) | NULL skip | NULL skip | sem ontem | **3** | 🟠 Descanso |
| 06/05 | 29 (1) | 69 (0) | 51 (0) | 80 (0) | 0 vs 29 | **1** | 🟡 Atenção |
| 07/05 | 34 (0) | 73 (0) | 51 (0) | NULL skip | +5 vs 29 | **0** | 🟢 Pronto |
| 08/05 | 27 (1) | 54 (1) | 53 (1) | 78 (0) | −7 → +1 | **4** | 🟠 Descanso |

Qualquer divergência → recalibrar limiares antes de deploy.

### 4.6 Override manual

Flags CLI:
```bash
python dash_today.py --verdict "LR7 reservado" --color amber
python dash_today.py --verdict "Off por gripe" --color red --subtitle "Foco em hidratação"
```

- `--verdict TEXT` substitui headline (auto-rule pulada inteiramente)
- `--color {green,amber,orange,red}` substitui cor. Se `--verdict` foi fornecida sem `--color`, default é **amber** (neutro/atenção). Não tenta inferir cor a partir de dados quando o headline foi forçado.
- `--subtitle TEXT` substitui sub-mensagem

Override é total: quando usado, NÃO computa pontuação. Sub-mensagem fica vazia se não fornecida.

---

## 5. Componentes por aba

### 5.1 Aba HOJE

| Bloco | Conteúdo | Fonte (DB) |
|---|---|---|
| Veredito hero | Headline + sub-mensagem + cor | computado (Seção 4) |
| HRV + sparkline | Número grande, ↓ delta vs ontem, faixa 7d, alvo ≥32 tracejado | `hrv_avg_overnight` últimos 7 dias |
| 4 pills | Sono · BB max · FCrep · Readiness com delta | `sleep_duration_min`, `body_battery_max`, `resting_heart_rate`, `training_readiness` |
| Sono por fase | Barra horizontal estratificada REM/Deep/Light/Awake | `sleep_*_min` |
| BB curve do dia | Sparkline curva 24h | `raw_json` → `bodyBatteryValuesArray` |

### 5.2 Aba TRENDS

5 sparklines empilhadas. Toggle 7d / 30d / 90d (default 7d).

| # | Métrica | Cor | Linha de alvo |
|---|---|---|---|
| 1 | HRV overnight | #ff3b30 | 32 ms |
| 2 | Sono total | #0a84ff | 480 min (8h) |
| 3 | BB max | #bf5af2 | 70 |
| 4 | FCrep | #30d158 | 51 (baseline) |
| 5 | Training Readiness | #ff9500 | 65 |

Cada sparkline mostra: média do período, valor atual, delta vs período anterior.

**Bloco de correlações:** texto auto-detectado via heurística simples (Pearson sobre pares óbvios, ex: sleep_duration vs hrv_next_day). Útil só com ≥ 14 dias. Antes disso: "Coletando dados (X/14)".

### 5.3 Aba HISTÓRICO

Tabela ordenável + filtros, 1 linha por dia:

| DATA | HRV | SONO | BB | FCREP | READY | VEREDITO |
|---|---|---|---|---|---|---|

Recursos:
- Click em cabeçalho ordena (asc/desc, JS puro client-side)
- Botão "Export CSV" gera download client-side via Blob API
- Click numa linha mostra modal com `raw_json` daquele dia (debug)

**Coluna VEREDITO é computada em Python no momento da geração do dash**, não armazenada no DB. Para cada linha do histórico, aplica-se o mesmo algoritmo da Seção 4 (com `HRV-Δ` calculado contra a linha do dia anterior, se existir). Isso permite recalibrar limiares no futuro e ver retroativamente como ficaria.

---

## 6. Edge cases e error handling

| Cenário | Comportamento |
|---|---|
| `runtech.db` não existe | Exit 1 com mensagem: `"DB não encontrado em <path>. Rode python health_daily.py primeiro."` |
| DB existe mas vazio | HTML de única tela: "Sem dados ainda. Rode `health_daily.py --backfill 7`" |
| Linha de hoje não existe (ainda não rodou) | Mostra última data disponível + banner amarelo "Dados de ontem. Rode `health_daily.py` pra atualizar." |
| Algum campo NULL | Renderiza "—" em vez de 0. Pontuação **exclui métrica NULL do score** (Seção 4.1). |
| HRV status = "NONE" (Garmin sem baseline) | Valor é mostrado normalmente + tag cinza "baseline insuficiente" abaixo. Não invalida pontuação. |
| < 7 dias de dados | Sparkline desenha só pontos existentes (não pad com zeros). Label: "X de 7 dias". |
| < 14 dias de dados | Correlações: "Coletando dados (X/14)" — sem regressões. |
| `raw_json` sem `bodyBatteryValuesArray` | Bloco "BB curve do dia" oculto inteiramente. Outros blocos seguem. |
| `--verdict` flag usada | Auto-rule pulada. Texto/cor vem do flag. |
| Múltiplos runs no mesmo dia | Idempotente. `dash.html` sobrescrito. |
| `--archive` flag | Salva também `dash_archive/dash-YYYY-MM-DD.html`. Default off. |

**Princípio:** dashboard prefere ficar **mudo** a mostrar valor errado. Bloco que não consegue popular **some**, não imita.

---

## 7. Testing

### 7.1 Smoke tests (`test_dash.py`)

Script Python simples (não pytest), usa DB sintético em-memória/tempfile. Roda em < 2s. Sem rede, sem mocks externos.

```python
test_today_full_data()       # caso normal — 4 dias coletados
test_no_db()                 # DB ausente → exit 1 + msg
test_db_empty()              # DB sem linhas → tela "sem dados"
test_today_missing()         # só ontem existe → banner stale
test_all_null_metrics()      # linha existe, tudo NULL → veredito "indefinido (0/4 métricas)"
test_partial_null()          # 2 metricas NULL → score só sobre as 2 válidas
test_verdict_override()      # --verdict X --color amber → HTML contém X + classe amber
test_verdict_override_no_color()  # --verdict sem --color → default amber
test_under_7_days()          # 3 dias → sparkline com 3 pontos
test_replay_real_4_days()    # 05-08/05 → vereditos esperados (Seção 4.5)
```

Total estimado: ~8 testes, ~180 linhas.

### 7.2 Validação visual

1. Gerar `dash.html` com dados reais (4 dias atuais).
2. Abrir em Chrome (principal) e Firefox (secundário).
3. Conferir que renderiza idêntico aos mockups aprovados em `.superpowers/brainstorm/.../content/synthesis.html`.
4. Usuário confirma fidelidade visual antes do done.

---

## 8. Integração com fluxo existente

### 8.1 Atalho de comando único (recomendado)

Modificar `health_daily.py`: ao final de uma run bem-sucedida (não em erro, não em backfill), chamar `dash_today.py` se ele existir.

Pseudo:
```python
# no fim de health_daily.py main():
if args.date is None and not args.backfill and not args.backfill_from:
    # caso default (hoje) — gera dash automaticamente
    try:
        subprocess.run([sys.executable, "dash_today.py"], check=False)
    except FileNotFoundError:
        pass  # dash_today.py opcional, silent skip
```

Justificativa: 99% das vezes o atleta roda `health_daily.py` SEM args (= dia de hoje). Backfill é evento raro e não deve gerar dash.

### 8.2 Comando standalone

`dash_today.py` continua funcionando isolado para regenerar sem nova coleta:
```bash
python dash_today.py                              # gera com últimos dados
python dash_today.py --no-open                    # gera mas não abre browser
python dash_today.py --verdict "LR7" --color amber
python dash_today.py --archive                    # salva snapshot em dash_archive/
```

### 8.3 Coexistência com dashboard.py

Sem conflito:
- `dashboard.py` (existente) — Streamlit, foco em atividades TCX (mapa, FC, splits, watts) — porta 8501
- `dash_today.py` (novo) — HTML estático, foco em métricas de saúde diárias — `file://`

Atleta mantém os dois. Cada um pra um propósito.

---

## 9. .gitignore

Adicionar ao `.gitignore` da pasta:
```
dash.html
dash_archive/
.superpowers/
```

---

## 10. Definition of done

- [ ] `dash_today.py` gera `dash.html` com 3 abas funcionais (HOJE, TRENDS, HISTÓRICO)
- [ ] Veredito da Seção 4 implementado e validado contra os 4 dias atuais (Seção 4.5)
- [ ] Override `--verdict / --color / --subtitle` funciona
- [ ] CSS gera fidelidade visual com mockup `synthesis.html`
- [ ] Smoke tests da Seção 7.1 passam
- [ ] Validação visual em Chrome aprovada pelo usuário
- [ ] Hook em `health_daily.py` chama `dash_today.py` ao final do run default
- [ ] `.gitignore` atualizado
- [ ] `requirements.txt` inclui `Jinja2`
- [ ] README ou SETUP atualizado mencionando `dash_today.py`

---

## 11. Fora de escopo (parking lot)

Itens que apareceram na conversa mas **NÃO** entram nesta entrega:

- Aba Atividades (continua em `dashboard.py`)
- Modelos estatísticos profundos (correlações são heurística simples)
- Dashboard mobile (file:// no Chrome desktop é o uso)
- Push notifications (vem em fase posterior do roadmap, com Telegram)
- Integração TrainingPeaks (vem com `tp_import.py`, após 19/05)
- PMC trends (CTL/ATL/TSB) — vem com `pmc.py`, após LR7 sábado 09/05
