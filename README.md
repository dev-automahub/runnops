# RunTechOps — Pipeline Garmin/TrainingPeaks

Conjunto de scripts Python para coletar, processar e visualizar dados do Garmin Connect e do TrainingPeaks Premium. Pipeline genérico — serve a temporada 2026 (21K + 21K + Maratona) e temporadas futuras.

## Estrutura

```
RunTechOps/
  ├─ conn.py                   # Teste rápido de conexão Garmin (refatorado para .env)
  ├─ lastrun.py                # Baixador de atividades em formato TCX
  ├─ dashboard.py              # Dashboard Streamlit — análise de TCX
  ├─ garmin_activity_data.csv  # Histórico de atividades (já populado)
  ├─ lastrun_log.txt           # Log de downloads do lastrun.py
  ├─ Atividades Baixadas/      # Pasta com TCXs históricos
  ├─ .env                      # Credenciais (NÃO commitar — ver .env.example)
  ├─ .env.example              # Modelo de credenciais
  ├─ .gitignore                # Proteção de credenciais e artefatos
  ├─ requirements.txt          # Dependências Python
  ├─ SETUP.md                  # Guia passo a passo de setup
  └─ README.md                 # Este arquivo
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

## Roadmap (a implementar)

| Componente | Status | Prazo |
|---|---|---|
| Migração credenciais para .env | ✅ feito | — |
| Zonas Karvonen do atleta no dashboard | ✅ feito | — |
| `health_daily.py` (HRV, Sleep, Body Battery) | 🟡 a fazer | após 12/05/2026 |
| `pmc.py` (CTL/ATL/TSB) | 🟡 a fazer | após 19/05/2026 |
| `tp_import.py` (CSV TrainingPeaks) | 🟡 a fazer | após 19/05/2026 |
| `scoring.py` (decisão diária composta) | 🟡 a fazer | após 24/05/2026 |
| Storage SQLite | 🟡 a fazer | após 24/05/2026 |
| Schedule Windows (Task Scheduler) | 🟡 a fazer | após 24/05/2026 |
| Notificação Telegram | 🟡 a fazer | após 24/05/2026 |

Razão dos prazos: o **HRV Status do Garmin precisa de ~19 dias 24/7 para baseline confiável** (uso 24/7 começou em 05/05/2026). Antes disso, não vale automatizar a decisão composta.

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
