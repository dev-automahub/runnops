# RunTechOps — Pipeline Garmin / Dashboard publicado

Coleta + análise + publicação automática de dados fisiológicos e de treino. Serve a temporada 2026 (21K + 21K + Maratona). Live em **https://runnops.pages.dev**.

> 📘 **Documentação técnica completa:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arquitetura, modelo de dados (4 tabelas SQLite), pipelines, frontend, convenções, operações, limitações, roadmap, glossário.
>
> ⚙️ **Setup passo-a-passo:** [`SETUP.md`](SETUP.md)

## Estrutura

```
RunTechOps/
  │
  ├─ Coleta e ingestão
  │   ├─ health_daily.py          # Coleta diária Garmin → SQLite + hooks
  │   ├─ lastrun.py               # Baixa TCX da última atividade
  │   ├─ scheduled_workouts.py    # Baixa calendário Garmin (plano da semana)
  │   ├─ aggregate_activities.py  # Agrega TCX → session_summary + weekly_summary
  │   └─ conn.py                  # Teste de conexão
  │
  ├─ Renderização (dashboard)
  │   ├─ dash_today.py            # Orquestrador: gera index.html + activities.json
  │   ├─ dash_data.py             # Camada de queries SQLite + parsing MDs
  │   ├─ dash_verdict.py          # Lógica do veredito diário
  │   ├─ dash_render.py           # Jinja2 + sparklines SVG + curvas
  │   ├─ dash_journal.py          # Auto-update do AUTO section dos diários
  │   ├─ dash_glossary.py         # Termos do glossário
  │   ├─ dash_activities.py       # Manifest de TCX
  │   ├─ dash_template.html       # Template das 5 abas
  │   └─ dash_styles.css          # CSS (embutido no HTML final)
  │
  ├─ Publicação
  │   └─ publish.py               # git add/commit/push (Cloudflare republica)
  │
  ├─ Saídas
  │   ├─ index.html               # Dashboard 5 abas (serve em runnops.pages.dev)
  │   ├─ activity.html            # Página por treino (mapa Leaflet + Plotly)
  │   ├─ activities.json          # Manifest dos TCX
  │   └─ runtech.db               # SQLite (gitignored)
  │
  ├─ Conteúdo da temporada
  │   └─ 2026-05-04-protocolo-recuperacao-corrida-rua-amador/
  │       ├─ relatorio.md / .html
  │       ├─ macrociclo.md / .html
  │       ├─ checklist.md         # Lista executável + rotina semanal
  │       ├─ fontes.json / .md
  │       ├─ diario/YYYY-MM-DD.md          # Análises diárias publicadas
  │       └─ planos-semana/plano-semana-YYYY-Www.md  # Plano da semana
  │
  ├─ Dados
  │   ├─ Atividades Baixadas/*.tcx  # TCXs históricos
  │
  ├─ Documentação
  │   ├─ docs/ARCHITECTURE.md     # 📘 Referência técnica completa
  │   ├─ docs/superpowers/        # Specs antigas (artefato de design)
  │   ├─ SETUP.md                 # Guia de setup
  │   └─ README.md                # Este arquivo
  │
  ├─ Testes
  │   └─ test_dash.py             # 24 smoke tests
  │
  └─ Configuração
      ├─ .env                     # Credenciais (gitignored)
      ├─ .env.example             # Modelo
      ├─ .gitignore
      └─ requirements.txt
```

## Setup inicial (uma vez)

Veja `SETUP.md` para guia detalhado. Resumo:

```powershell
# Criar virtual environment
cd "C:\_Dados\OneDrive - GS Comercio Internacional\Jr\Pesq_Jr\RunTechOps"
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependências (use -m pip para evitar pegadinha do pip global)
python -m pip install -r requirements.txt

# Configurar credenciais
copy .env.example .env
# Edite .env com email e senha do Garmin
```

## Uso

### Testar conexão Garmin
```powershell
python conn.py
```

### Baixar atividades em TCX
```powershell
python lastrun.py
# Pede quantidade de atividades e baixa as mais recentes
```

### Dashboard Streamlit
```powershell
streamlit run dashboard.py
# Abre em http://localhost:8501
```

## Dashboard de saúde diário

`dash_today.py` gera um painel HTML estilo iOS Health a partir do `runtech.db`:

```bash
python dash_today.py                            # gera + abre no browser
python dash_today.py --no-open                  # so gera, nao abre
python dash_today.py --verdict "LR7" --color amber   # override veredito
python dash_today.py --archive                  # tambem salva em dash_archive/
python dash_today.py --db custom.db             # outro DB
```

3 abas: **Hoje** (veredito + métricas + breakdown), **Trends** (5 sparklines 7d), **Histórico** (tabela ordenável + export CSV).

Roda automaticamente no fim de `python health_daily.py` quando sem flags (default = dia de hoje).

### Lógica do veredito

Combina HRV overnight, BB max, FCrep e Sleep Score. Limiares:
- HRV ≥32 / 26-31 / <26
- BB max ≥65 / 50-64 / <50
- FCrep ≤52 / 53-54 / ≥55
- Sleep Score ≥75 / 60-74 / <60

Mais 2 modificadores: HRV caiu ≥5 ms vs ontem (+1) e FCrep subiu ≥3 bpm vs baseline 51 (+1). Soma vira veredito: 0=verde "Pronto", 1-2=amarelo "Atenção", 3-4=laranja "Descanso", 5+=vermelho "Corte". Métricas NULL são excluídas do score (gate degenerate em <2 métricas).

Detalhes completos em `docs/superpowers/specs/2026-05-08-health-dashboard-design.md`.

### Limitações conhecidas (v1)

- **Toggle 7D/30D/90D na aba Trends é visual apenas** — sempre mostra os últimos 7 dias. Implementação completa fica pra v2 quando o histórico passar de 14 dias e fizer sentido. Até lá, foque em interpretar os 7 mais recentes.

## Status do roadmap

| Componente | Status |
|---|---|
| Migração credenciais para .env | ✅ feito |
| Zonas Karvonen do atleta no dashboard | ✅ feito |
| `health_daily.py` (HRV, Sleep, Body Battery, RHR, stress, readiness, VO2) | ✅ feito |
| Storage SQLite (`runtech.db`) | ✅ feito |
| Dashboard publicado (Cloudflare Pages) | ✅ feito (09/05) |
| `activity.html` por treino (mapa + gráficos) | ✅ feito (10/05) |
| Coleta Training Status + ATL/CTL/ACWR + Race Predictor | ✅ feito (11/05) |
| `aggregate_activities.py` (session + weekly summary) | ✅ feito (11/05) |
| `scheduled_workouts.py` (plano da semana via calendário Garmin) | ✅ feito (12/05) |
| Próximo Treino + Plano da Semana no dashboard | ✅ feito (12/05) |
| `pmc.py` customizado | ❌ substituído — Garmin entrega ATL/CTL/ACWR via API |
| Match planejado vs executado | 🟡 pendente |
| Tag por tipo de treino (LR/FFR/HRR…) | 🟡 pendente |
| Race Predictor temporal | 🟡 após 22/05 |
| Trends 30d/90d toggle | 🟡 após 30+ dias coletados |
| `tp_import.py` (CSV TrainingPeaks) | 🟡 após 19/05 |
| Notificação Telegram | 🟡 após 24/05 |
| Windows Task Scheduler (auto-run 06:00) | 🟡 após 24/05 |
| Repo virar privado + Cloudflare Access | 🟡 quando dashboard estabilizar |

Razão de alguns prazos: o **HRV Status do Garmin precisa de ~19 dias 24/7 para baseline confiável** (uso 24/7 começou em 05/05/2026). Correlações Pearson reais só fazem sentido com 14+ dias.

## Atleta de referência (zonas hard-coded em `dashboard.py`)

- **FCmáx:** 170 bpm (Tanaka, 54 anos)
- **FCrep:** 51 bpm (medida)
- **FCR:** 119 bpm
- **Zonas Karvonen:** Z1 111-122 | Z2 122-134 | Z3 134-146 | Z4 146-158 | Z5 158-170

Se for trocar de atleta, ajustar constantes `FC_MAX` e `FC_REP` no `dashboard.py`.

## Segurança

- **Senha do Garmin foi rotacionada em 05/05/2026** após detecção de credenciais em texto plano no `conn.py` original. Trocar imediatamente se ainda não fez.
- Credenciais agora ficam em `.env` (ignorado pelo git via `.gitignore`).
- Nunca commit o `.env` em repositório público ou privado.
