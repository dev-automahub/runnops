# Health Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Painel matinal HTML estático estilo iOS Health que lê `runtech.db`, computa veredito automático do dia (com override manual via flag), e renderiza 3 abas: Hoje, Trends, Histórico.

**Architecture:** Python script (`dash_today.py`) lê SQLite, computa via `dash_verdict.py`, modela dados via `dash_data.py`, renderiza Jinja2 via `dash_render.py`, escreve `dash.html` e abre no browser. JS no template gerencia troca de abas, ordenação de tabela e export CSV — tudo client-side, sem servidor.

**Tech Stack:** Python 3.13, SQLite stdlib, Jinja2 3.1+, JS vanilla (no framework), CSS puro.

**Não-git:** Este projeto não é um repositório git. Steps `git commit` foram substituídos por checkpoints de verificação manual (rodar script, conferir output). Se o usuário quiser versionar, sugerir `git init` em momento posterior.

---

## File Structure

```
RunTechOps/
  dash_today.py          # NOVO · CLI + orquestração (~80 linhas)
  dash_verdict.py        # NOVO · regras do veredito + modificadores (~120 linhas)
  dash_data.py           # NOVO · queries DB + shaping (~150 linhas)
  dash_render.py         # NOVO · Jinja2 + escrita HTML + abrir browser (~80 linhas)
  dash_template.html     # NOVO · template Jinja2 com 3 abas (~250 linhas)
  dash_styles.css        # NOVO · CSS estilo iOS Health (~280 linhas)
  test_dash.py           # NOVO · smoke tests (~220 linhas)

  health_daily.py        # MODIFICAR · adicionar hook no fim
  requirements.txt       # MODIFICAR · adicionar Jinja2
  .gitignore             # MODIFICAR · adicionar dash.html, dash_archive/, .superpowers/
  README.md              # MODIFICAR · mencionar dash_today.py
```

Decomposição justificada: `dash_verdict.py` é o coração da lógica e merece isolamento pra testes (regras + modificadores + casos NULL). `dash_data.py` lida com SQLite e formato dos dados. `dash_render.py` é o "boundary" do Jinja2. `dash_today.py` fica pequeno (só CLI + wiring).

---

## Task 1: Setup de dependências

**Files:**
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Adicionar Jinja2 ao requirements.txt**

Abrir `requirements.txt` e adicionar a linha (mantendo ordem alfabética se já existir):

```
Jinja2>=3.1
```

- [ ] **Step 2: Adicionar entradas ao .gitignore**

Abrir `.gitignore` e adicionar (sem duplicar se já existirem):

```
dash.html
dash_archive/
.superpowers/
```

- [ ] **Step 3: Instalar Jinja2 no venv**

Ativar venv e instalar:

```powershell
cd "C:\_Dados\OneDrive - GS Comercio Internacional\Jr\Pesq_Jr\RunTechOps"
.\.venv\Scripts\Activate.ps1
python -m pip install Jinja2
```

Esperado: `Successfully installed Jinja2-3.x.x` (ou "already satisfied").

- [ ] **Step 4: Verificar instalação**

```powershell
python -c "import jinja2; print(jinja2.__version__)"
```

Esperado: número de versão imprime sem erro (ex: `3.1.4`).

---

## Task 2: Módulo `dash_verdict.py` (TDD)

**Files:**
- Create: `dash_verdict.py`
- Create: `test_dash.py` (parcial — só testes de verdict)

- [ ] **Step 1: Criar test_dash.py com fixtures e testes do verdict**

Criar `test_dash.py` com este conteúdo inicial:

```python
"""Smoke tests pra dash_today. Roda sem pytest: python test_dash.py"""
import sys

# ===== Fixtures: linhas reais dos 4 dias coletados =====
ROW_05 = {"date": "2026-05-05", "hrv_avg_overnight": 29, "body_battery_max": 29,
          "resting_heart_rate": None, "sleep_score": None}
ROW_06 = {"date": "2026-05-06", "hrv_avg_overnight": 29, "body_battery_max": 69,
          "resting_heart_rate": 51, "sleep_score": 80}
ROW_07 = {"date": "2026-05-07", "hrv_avg_overnight": 34, "body_battery_max": 73,
          "resting_heart_rate": 51, "sleep_score": None}
ROW_08 = {"date": "2026-05-08", "hrv_avg_overnight": 27, "body_battery_max": 54,
          "resting_heart_rate": 53, "sleep_score": 78}

FCREP_BASELINE = 51

# ===== Testes do dash_verdict =====
def test_score_hrv():
    from dash_verdict import score_hrv
    assert score_hrv(35) == 0
    assert score_hrv(32) == 0
    assert score_hrv(31) == 1
    assert score_hrv(28) == 1
    assert score_hrv(26) == 1
    assert score_hrv(25) == 2
    assert score_hrv(None) is None  # NULL = skip

def test_score_bb():
    from dash_verdict import score_bb
    assert score_bb(70) == 0
    assert score_bb(65) == 0
    assert score_bb(60) == 1
    assert score_bb(50) == 1
    assert score_bb(49) == 2
    assert score_bb(None) is None

def test_score_fcrep():
    from dash_verdict import score_fcrep
    assert score_fcrep(50) == 0
    assert score_fcrep(52) == 0
    assert score_fcrep(53) == 1
    assert score_fcrep(54) == 1
    assert score_fcrep(55) == 2
    assert score_fcrep(None) is None

def test_score_sleep():
    from dash_verdict import score_sleep
    assert score_sleep(85) == 0
    assert score_sleep(75) == 0
    assert score_sleep(70) == 1
    assert score_sleep(60) == 1
    assert score_sleep(59) == 2
    assert score_sleep(None) is None

def test_modifier_hrv_drop():
    from dash_verdict import hrv_drop_modifier
    assert hrv_drop_modifier(27, 34) == 1  # caiu 7 (>= 5)
    assert hrv_drop_modifier(30, 34) == 0  # caiu 4 (< 5)
    assert hrv_drop_modifier(34, 27) == 0  # subiu, não dispara
    assert hrv_drop_modifier(27, None) == 0  # sem ontem
    assert hrv_drop_modifier(None, 34) == 0  # hoje null

def test_modifier_fcrep_rise():
    from dash_verdict import fcrep_rise_modifier
    assert fcrep_rise_modifier(54, FCREP_BASELINE) == 1  # +3 vs baseline 51
    assert fcrep_rise_modifier(53, FCREP_BASELINE) == 0  # +2 (< 3)
    assert fcrep_rise_modifier(50, FCREP_BASELINE) == 0  # abaixo
    assert fcrep_rise_modifier(None, FCREP_BASELINE) == 0  # null

def test_compute_verdict_replay_4_days():
    """Replay exato dos 4 dias coletados — bate com Seção 4.5 do spec."""
    from dash_verdict import compute_verdict
    v05 = compute_verdict(ROW_05, prev_row=None)
    assert v05["score"] == 3, f"05/05 esperado 3, veio {v05['score']}"
    assert v05["color"] == "orange"
    assert v05["headline"] == "Descanso recomendado"

    v06 = compute_verdict(ROW_06, prev_row=ROW_05)
    assert v06["score"] == 1, f"06/05 esperado 1, veio {v06['score']}"
    assert v06["color"] == "amber"
    assert v06["headline"].startswith("Atenção")

    v07 = compute_verdict(ROW_07, prev_row=ROW_06)
    assert v07["score"] == 0, f"07/05 esperado 0, veio {v07['score']}"
    assert v07["color"] == "green"
    assert v07["headline"] == "Pronto pra treinar"

    v08 = compute_verdict(ROW_08, prev_row=ROW_07)
    assert v08["score"] == 4, f"08/05 esperado 4, veio {v08['score']}"
    assert v08["color"] == "orange"
    assert v08["headline"] == "Descanso recomendado"

def test_compute_verdict_critical_red():
    """5+ pontos → vermelho corte."""
    from dash_verdict import compute_verdict
    row = {"hrv_avg_overnight": 25, "body_battery_max": 45,
           "resting_heart_rate": 56, "sleep_score": 55}
    prev = {"hrv_avg_overnight": 32, "body_battery_max": 70,
            "resting_heart_rate": 51, "sleep_score": 80}
    v = compute_verdict(row, prev_row=prev)
    # HRV<26 (2) + BB<50 (2) + FCrep>=55 (2) + Sleep<60 (2) + HRV-7 mod (1) + FCrep+5 mod (1) = 10
    assert v["score"] >= 5
    assert v["color"] == "red"
    assert v["headline"] == "Corte forçado"

def test_compute_verdict_all_null_degenerate():
    """0 metricas avaliáveis → cinza, dados insuficientes."""
    from dash_verdict import compute_verdict
    row = {"hrv_avg_overnight": None, "body_battery_max": None,
           "resting_heart_rate": None, "sleep_score": None}
    v = compute_verdict(row, prev_row=None)
    assert v["color"] == "gray"
    assert v["headline"] == "Dados insuficientes"
    assert "0 de 4" in v["subtitle"]

def test_compute_verdict_partial_null():
    """2 metricas NULL → score só sobre as 2 válidas."""
    from dash_verdict import compute_verdict
    row = {"hrv_avg_overnight": 33, "body_battery_max": 70,
           "resting_heart_rate": None, "sleep_score": None}
    v = compute_verdict(row, prev_row=None)
    assert v["score"] == 0
    assert v["color"] == "green"
    assert v["evaluated_count"] == 2

# ===== Runner manual =====
def run_all():
    tests = [name for name in globals() if name.startswith("test_")]
    failed = []
    for name in tests:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed.append(name)
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            failed.append(name)
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passou")
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(run_all())
```

- [ ] **Step 2: Rodar testes — todos devem falhar com ImportError**

```powershell
python test_dash.py
```

Esperado: `ERROR test_score_hrv: ModuleNotFoundError: No module named 'dash_verdict'` (e similar pros outros).

- [ ] **Step 3: Criar dash_verdict.py com a implementação mínima**

Criar `dash_verdict.py`:

```python
"""Lógica do veredito do dashboard. Pure functions, sem I/O."""

FCREP_BASELINE = 51


def score_hrv(value):
    if value is None:
        return None
    if value >= 32:
        return 0
    if value >= 26:
        return 1
    return 2


def score_bb(value):
    if value is None:
        return None
    if value >= 65:
        return 0
    if value >= 50:
        return 1
    return 2


def score_fcrep(value):
    if value is None:
        return None
    if value <= 52:
        return 0
    if value <= 54:
        return 1
    return 2


def score_sleep(value):
    if value is None:
        return None
    if value >= 75:
        return 0
    if value >= 60:
        return 1
    return 2


def hrv_drop_modifier(today_hrv, yesterday_hrv):
    """Soma 1 se HRV caiu >= 5 ms vs ontem."""
    if today_hrv is None or yesterday_hrv is None:
        return 0
    if (yesterday_hrv - today_hrv) >= 5:
        return 1
    return 0


def fcrep_rise_modifier(today_fcrep, baseline=FCREP_BASELINE):
    """Soma 1 se FCrep subiu >= 3 bpm vs baseline."""
    if today_fcrep is None:
        return 0
    if (today_fcrep - baseline) >= 3:
        return 1
    return 0


def _worst_metrics(scores_named, n=2):
    """Retorna nomes das n piores metricas (maior score)."""
    valid = [(name, s) for name, s in scores_named.items() if s is not None]
    valid.sort(key=lambda x: -x[1])
    return [name for name, s in valid[:n] if s > 0]


def compute_verdict(row, prev_row=None):
    """Aplica regra completa do veredito.

    Args:
        row: dict com hrv_avg_overnight, body_battery_max, resting_heart_rate, sleep_score
        prev_row: mesmo formato, dia anterior (ou None)

    Returns:
        dict com score, color, headline, subtitle, evaluated_count
    """
    s_hrv = score_hrv(row.get("hrv_avg_overnight"))
    s_bb = score_bb(row.get("body_battery_max"))
    s_fcrep = score_fcrep(row.get("resting_heart_rate"))
    s_sleep = score_sleep(row.get("sleep_score"))

    scores = {"HRV": s_hrv, "BB": s_bb, "FCrep": s_fcrep, "Sono": s_sleep}
    valid_scores = [s for s in scores.values() if s is not None]
    evaluated = len(valid_scores)

    if evaluated < 2:
        return {
            "score": 0,
            "color": "gray",
            "headline": "Dados insuficientes",
            "subtitle": f"{evaluated} de 4 métricas coletadas. Reporta amanhã pra avaliação.",
            "evaluated_count": evaluated,
        }

    base_score = sum(valid_scores)

    prev_hrv = prev_row.get("hrv_avg_overnight") if prev_row else None
    mod_hrv = hrv_drop_modifier(row.get("hrv_avg_overnight"), prev_hrv)
    mod_fcrep = fcrep_rise_modifier(row.get("resting_heart_rate"))
    total = base_score + mod_hrv + mod_fcrep

    if total == 0:
        color = "green"
        headline = "Pronto pra treinar"
        subtitle = "Sinais coerentes. Executa o plano."
    elif total <= 2:
        color = "amber"
        headline = "Atenção: prioriza Z2"
        worst = _worst_metrics(scores, n=1)
        subtitle = f"{worst[0]} fora do ideal." if worst else "Sinais mistos."
    elif total <= 4:
        color = "orange"
        headline = "Descanso recomendado"
        worst = _worst_metrics(scores, n=2)
        subtitle = f"Sinais fracos: {', '.join(worst)}." if worst else "Cargas acumuladas."
    else:
        color = "red"
        headline = "Corte forçado"
        subtitle = "Múltiplos sinais críticos. Off hoje."

    return {
        "score": total,
        "color": color,
        "headline": headline,
        "subtitle": subtitle,
        "evaluated_count": evaluated,
    }
```

- [ ] **Step 4: Rodar testes — agora todos devem passar**

```powershell
python test_dash.py
```

Esperado: `9/9 passou` (sem FAIL nem ERROR).

Se algum teste falhar: o output mostra `FAIL test_X: assertion details`. Ajustar `dash_verdict.py` ou recalibrar limiares e iterar até verde.

- [ ] **Step 5: Verificação manual**

```powershell
python -c "from dash_verdict import compute_verdict; print(compute_verdict({'hrv_avg_overnight':27,'body_battery_max':54,'resting_heart_rate':53,'sleep_score':78}, prev_row={'hrv_avg_overnight':34}))"
```

Esperado: dict com `score=4`, `color='orange'`, `headline='Descanso recomendado'`. Igual ao seu dia 08/05 real.

---

## Task 3: Módulo `dash_data.py` (TDD)

**Files:**
- Create: `dash_data.py`
- Modify: `test_dash.py` (adicionar testes do data)

- [ ] **Step 1: Adicionar testes de `dash_data` ao test_dash.py**

Append ao final de `test_dash.py` (antes do `if __name__`):

```python
# ===== Testes do dash_data =====
import sqlite3
import tempfile
import os
import json

def _create_test_db(rows):
    """Cria DB temporário com schema da health_daily e popula com rows fornecidas."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    conn = sqlite3.connect(tmp.name)
    conn.execute("""
        CREATE TABLE health_daily (
            date TEXT PRIMARY KEY,
            sleep_score INTEGER, sleep_duration_min INTEGER,
            sleep_rem_min INTEGER, sleep_deep_min INTEGER,
            sleep_light_min INTEGER, sleep_awake_min INTEGER,
            hrv_avg_overnight REAL, hrv_status TEXT,
            body_battery_max INTEGER, body_battery_min INTEGER,
            body_battery_charged INTEGER, body_battery_drained INTEGER,
            resting_heart_rate INTEGER,
            stress_avg INTEGER, stress_max INTEGER,
            training_readiness INTEGER,
            vo2_max REAL, weight_kg REAL,
            steps INTEGER, active_calories INTEGER,
            fetched_at TEXT, raw_json TEXT
        )
    """)
    for r in rows:
        cols = ",".join(r.keys())
        ph = ",".join(["?"] * len(r))
        conn.execute(f"INSERT INTO health_daily ({cols}) VALUES ({ph})", list(r.values()))
    conn.commit()
    conn.close()
    return tmp.name


def test_load_history_returns_rows_in_order():
    from dash_data import load_history
    db = _create_test_db([
        {"date": "2026-05-05", "hrv_avg_overnight": 29, "body_battery_max": 29},
        {"date": "2026-05-08", "hrv_avg_overnight": 27, "body_battery_max": 54},
        {"date": "2026-05-06", "hrv_avg_overnight": 29, "body_battery_max": 69},
    ])
    try:
        rows = load_history(db, days=30)
        assert len(rows) == 3
        # Ordem decrescente por data
        assert rows[0]["date"] == "2026-05-08"
        assert rows[2]["date"] == "2026-05-05"
    finally:
        os.unlink(db)


def test_load_history_empty_db():
    from dash_data import load_history
    db = _create_test_db([])
    try:
        rows = load_history(db, days=30)
        assert rows == []
    finally:
        os.unlink(db)


def test_load_history_db_not_exists():
    from dash_data import load_history
    try:
        load_history("/nonexistent/path/no.db", days=30)
        assert False, "deveria ter falhado"
    except FileNotFoundError:
        pass


def test_get_today_row_present():
    from dash_data import get_today_row
    today = "2026-05-08"
    db = _create_test_db([
        {"date": "2026-05-07", "hrv_avg_overnight": 34},
        {"date": today, "hrv_avg_overnight": 27},
    ])
    try:
        row, is_stale = get_today_row(db, today)
        assert row["date"] == today
        assert is_stale is False
    finally:
        os.unlink(db)


def test_get_today_row_stale():
    from dash_data import get_today_row
    today = "2026-05-08"
    db = _create_test_db([
        {"date": "2026-05-07", "hrv_avg_overnight": 34},
    ])
    try:
        row, is_stale = get_today_row(db, today)
        assert row["date"] == "2026-05-07"
        assert is_stale is True
    finally:
        os.unlink(db)


def test_compute_history_with_verdicts():
    """history rows enriquecidas com veredito por linha."""
    from dash_data import enrich_with_verdicts
    rows = [
        {"date": "2026-05-08", "hrv_avg_overnight": 27, "body_battery_max": 54,
         "resting_heart_rate": 53, "sleep_score": 78},
        {"date": "2026-05-07", "hrv_avg_overnight": 34, "body_battery_max": 73,
         "resting_heart_rate": 51, "sleep_score": None},
        {"date": "2026-05-06", "hrv_avg_overnight": 29, "body_battery_max": 69,
         "resting_heart_rate": 51, "sleep_score": 80},
    ]
    enriched = enrich_with_verdicts(rows)
    assert enriched[0]["verdict"]["color"] == "orange"  # 08
    assert enriched[1]["verdict"]["color"] == "green"   # 07
    assert enriched[2]["verdict"]["color"] == "amber"   # 06


def test_parse_bb_curve_from_raw_json():
    from dash_data import parse_bb_curve
    raw = json.dumps({
        "get_body_battery": [{
            "bodyBatteryValuesArray": [
                [1715000000000, 30],
                [1715003600000, 35],
                [1715007200000, 50],
            ]
        }]
    })
    points = parse_bb_curve(raw)
    assert len(points) == 3
    assert points[0] == (1715000000000, 30)


def test_parse_bb_curve_missing_returns_empty():
    from dash_data import parse_bb_curve
    assert parse_bb_curve(None) == []
    assert parse_bb_curve('{"foo": "bar"}') == []
    assert parse_bb_curve('not valid json') == []
```

- [ ] **Step 2: Rodar testes — falham por ImportError**

```powershell
python test_dash.py
```

Esperado: testes do `dash_data` ainda erram com `ModuleNotFoundError`. Os do `dash_verdict` continuam passando.

- [ ] **Step 3: Criar dash_data.py**

Criar `dash_data.py`:

```python
"""Camada de dados: queries SQLite + parsing + enrichment com verdict."""
import json
import sqlite3
from pathlib import Path

from dash_verdict import compute_verdict


HISTORY_COLS = [
    "date", "sleep_score", "sleep_duration_min",
    "sleep_rem_min", "sleep_deep_min", "sleep_light_min", "sleep_awake_min",
    "hrv_avg_overnight", "hrv_status",
    "body_battery_max", "body_battery_min",
    "body_battery_charged", "body_battery_drained",
    "resting_heart_rate",
    "stress_avg", "stress_max",
    "training_readiness",
    "vo2_max", "weight_kg",
    "steps", "active_calories",
    "raw_json",
]


def load_history(db_path, days=30):
    """Le ate N dias mais recentes da tabela health_daily, ordenados desc por date."""
    if not Path(db_path).exists():
        raise FileNotFoundError(f"DB nao encontrado: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        f"SELECT {','.join(HISTORY_COLS)} FROM health_daily "
        f"ORDER BY date DESC LIMIT ?",
        (days,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_today_row(db_path, today_iso):
    """Retorna (row, is_stale).

    is_stale=True quando o ultimo dado nao e de hoje.
    Se DB vazio, row=None.
    """
    rows = load_history(db_path, days=2)
    if not rows:
        return None, False
    latest = rows[0]
    is_stale = latest["date"] != today_iso
    return latest, is_stale


def enrich_with_verdicts(rows):
    """Para cada row do historico, computa o verdict usando a linha do dia anterior.

    rows: lista ordenada DESC por data (resultado de load_history).
    Retorna nova lista com 'verdict' adicionado em cada row.
    """
    enriched = []
    for i, row in enumerate(rows):
        prev = rows[i + 1] if i + 1 < len(rows) else None
        verdict = compute_verdict(row, prev_row=prev)
        new_row = dict(row)
        new_row["verdict"] = verdict
        enriched.append(new_row)
    return enriched


def parse_bb_curve(raw_json_str):
    """Extrai bodyBatteryValuesArray do raw_json. Retorna lista de (timestamp_ms, value)."""
    if not raw_json_str:
        return []
    try:
        raw = json.loads(raw_json_str)
    except (json.JSONDecodeError, TypeError):
        return []
    bb = raw.get("get_body_battery") if isinstance(raw, dict) else None
    if not bb:
        return []
    entry = bb[0] if isinstance(bb, list) and bb else (bb if isinstance(bb, dict) else None)
    if not entry:
        return []
    values = entry.get("bodyBatteryValuesArray") or []
    points = []
    for v in values:
        if isinstance(v, (list, tuple)) and len(v) >= 2 and v[1] is not None:
            points.append((v[0], v[1]))
    return points


def compute_deltas(today_row, yesterday_row):
    """Computa deltas de cada metrica vs ontem. Usado pelas pills do HOJE."""
    if not yesterday_row:
        return {}
    metrics = ["hrv_avg_overnight", "body_battery_max", "resting_heart_rate",
               "training_readiness", "sleep_duration_min", "sleep_score"]
    deltas = {}
    for m in metrics:
        t = today_row.get(m)
        y = yesterday_row.get(m)
        if t is None or y is None:
            deltas[m] = None
        else:
            deltas[m] = t - y
    return deltas


def trend_series(rows, metric, n=7):
    """Extrai serie temporal pra sparkline. Retorna [(date, value), ...] mais antigo→recente."""
    sliced = rows[:n]
    sliced = list(reversed(sliced))  # antigo→recente
    return [(r["date"], r.get(metric)) for r in sliced]
```

- [ ] **Step 4: Rodar testes — todos devem passar**

```powershell
python test_dash.py
```

Esperado: `17/17 passou` (9 verdict + 8 data).

---

## Task 4: CSS — `dash_styles.css`

**Files:**
- Create: `dash_styles.css`

- [ ] **Step 1: Criar dash_styles.css com estilo iOS Health**

Criar `dash_styles.css`. Baseado fielmente no mockup `synthesis.html` aprovado:

```css
/* === Reset minimo === */
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, "SF Pro Display", "Helvetica Neue", system-ui, sans-serif;
  background: #f2f2f7;
  color: #1c1c1e;
  -webkit-font-smoothing: antialiased;
  padding: 32px 24px 64px;
}

/* === Container === */
.dash {
  max-width: 760px;
  margin: 0 auto;
}

/* === Header com data e tabs === */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}
.title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.date {
  font-size: 13px;
  opacity: 0.55;
}
.tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 22px;
}
.tab {
  padding: 7px 14px;
  font-size: 12px;
  letter-spacing: 0.05em;
  border-radius: 999px;
  background: white;
  cursor: pointer;
  font-weight: 600;
  border: none;
  color: #1c1c1e;
  opacity: 0.55;
  transition: opacity .15s, background .15s;
}
.tab:hover { opacity: 0.85; }
.tab.active {
  background: #1c1c1e;
  color: white;
  opacity: 1;
}

/* === Verdict block (HOJE) === */
.verdict {
  border-radius: 20px;
  padding: 26px 28px;
  margin-bottom: 22px;
  color: white;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}
.verdict.green   { background: linear-gradient(135deg, #34c759, #28a745); box-shadow-color: rgba(52,199,89,0.25); }
.verdict.amber   { background: linear-gradient(135deg, #ffcc00, #ff9500); box-shadow-color: rgba(255,204,0,0.25); }
.verdict.orange  { background: linear-gradient(135deg, #ff9500, #ff5e3a); box-shadow-color: rgba(255,94,58,0.25); }
.verdict.red     { background: linear-gradient(135deg, #ff453a, #c0142b); box-shadow-color: rgba(255,69,58,0.25); }
.verdict.gray    { background: linear-gradient(135deg, #aeaeb2, #8e8e93); box-shadow-color: rgba(142,142,147,0.2); }
.verdict-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.verdict-label {
  font-size: 11px;
  letter-spacing: 0.14em;
  opacity: 0.85;
  font-weight: 700;
}
.verdict-headline {
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.05;
  margin-top: 6px;
}
.verdict-sub {
  font-size: 14px;
  opacity: 0.92;
  margin-top: 10px;
  line-height: 1.4;
  max-width: 480px;
}
.verdict-badge {
  background: rgba(255,255,255,0.22);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  white-space: nowrap;
}

/* === Stale banner === */
.stale-banner {
  background: #fff8e1;
  border-left: 4px solid #ffcc00;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 18px;
}

/* === Hero card (HRV + sparkline) === */
.hero-card {
  background: white;
  border-radius: 18px;
  padding: 22px 24px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}
.label-tiny {
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.55;
  font-weight: 700;
}
.hero-num-block { display: flex; align-items: baseline; gap: 4px; margin-top: 6px; }
.hero-num { font-size: 64px; font-weight: 700; letter-spacing: -0.035em; line-height: 0.9; color: #ff3b30; }
.hero-unit { font-size: 22px; font-weight: 500; opacity: 0.55; }
.hero-meta { font-size: 13px; opacity: 0.6; margin-top: 6px; }

/* === Sparkline SVGs === */
.spark-line { fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.spark-area { opacity: 0.10; }
.spark-target { stroke: #8e8e93; stroke-width: 1; stroke-dasharray: 3 3; }
.spark-dot { r: 4; }
.spark-hrv .spark-line, .spark-hrv .spark-dot { stroke: #ff3b30; fill: #ff3b30; }
.spark-hrv .spark-area { fill: #ff3b30; }
.spark-sleep .spark-line, .spark-sleep .spark-dot { stroke: #0a84ff; fill: #0a84ff; }
.spark-sleep .spark-area { fill: #0a84ff; }
.spark-bb .spark-line, .spark-bb .spark-dot { stroke: #bf5af2; fill: #bf5af2; }
.spark-bb .spark-area { fill: #bf5af2; }
.spark-fcrep .spark-line, .spark-fcrep .spark-dot { stroke: #30d158; fill: #30d158; }
.spark-fcrep .spark-area { fill: #30d158; }
.spark-ready .spark-line, .spark-ready .spark-dot { stroke: #ff9500; fill: #ff9500; }
.spark-ready .spark-area { fill: #ff9500; }

/* === Pills row === */
.pills {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}
.pill {
  background: white;
  border-radius: 14px;
  padding: 14px;
}
.pill-label {
  font-size: 10px;
  letter-spacing: 0.1em;
  opacity: 0.5;
  font-weight: 700;
}
.pill-value {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-top: 4px;
}
.pill-delta { font-size: 11px; font-weight: 600; margin-top: 2px; }
.delta-up      { color: #30d158; }
.delta-down    { color: #ff453a; }
.delta-warn    { color: #ff9500; }
.delta-neutral { color: #8e8e93; }

/* === Sleep breakdown === */
.sleep-card {
  background: white;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 12px;
}
.sleep-bar {
  display: flex;
  height: 14px;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 8px;
}
.sleep-rem   { background: #5e5ce6; }
.sleep-deep  { background: #bf5af2; }
.sleep-light { background: #0a84ff; }
.sleep-awake { background: #ff9f0a; }
.sleep-legend {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 6px;
  display: flex;
  gap: 14px;
}
.sleep-legend span::before {
  content: "";
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 2px;
  margin-right: 4px;
  vertical-align: middle;
}
.sleep-legend .lg-rem::before   { background: #5e5ce6; }
.sleep-legend .lg-deep::before  { background: #bf5af2; }
.sleep-legend .lg-light::before { background: #0a84ff; }
.sleep-legend .lg-awake::before { background: #ff9f0a; }

/* === BB curve do dia === */
.bb-curve-card {
  background: white;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 12px;
}

/* === Trends === */
.trends-period {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
}
.trends-period button {
  padding: 6px 12px;
  font-size: 11px;
  border-radius: 999px;
  background: white;
  border: none;
  cursor: pointer;
  opacity: 0.55;
  font-weight: 600;
}
.trends-period button.active { background: #1c1c1e; color: white; opacity: 1; }

.trend-card {
  background: white;
  border-radius: 14px;
  padding: 16px 20px;
  margin-bottom: 10px;
}
.trend-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.trend-meta {
  font-size: 11px;
  opacity: 0.55;
}

/* === Histórico === */
.history-card {
  background: white;
  border-radius: 14px;
  padding: 16px;
}
.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.history-table th {
  text-align: left;
  padding: 8px 10px;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.08em;
  opacity: 0.55;
  border-bottom: 2px solid #c7c7cc;
  cursor: pointer;
  user-select: none;
}
.history-table th:hover { opacity: 0.85; }
.history-table td {
  padding: 10px;
  border-bottom: 1px solid #f2f2f7;
}
.history-table tr:hover td { background: #fafafa; cursor: pointer; }
.cell-green  { color: #30d158; font-weight: 600; }
.cell-amber  { color: #ff9500; font-weight: 600; }
.cell-orange { color: #ff5e3a; font-weight: 600; }
.cell-red    { color: #ff3b30; font-weight: 700; }
.cell-gray   { color: #8e8e93; }
.export-btn {
  background: #1c1c1e;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 12px;
}

/* === Modal raw_json === */
.modal-bg {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal-bg.show { display: flex; }
.modal {
  background: white;
  border-radius: 14px;
  padding: 22px;
  max-width: 800px;
  max-height: 80vh;
  overflow: auto;
  width: 90%;
}
.modal pre {
  font-family: "SF Mono", Menlo, monospace;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-all;
}
.modal-close {
  float: right;
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  opacity: 0.5;
}

/* === Empty state === */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: white;
  border-radius: 14px;
}
.empty-state h2 { margin-bottom: 8px; }
.empty-state p { opacity: 0.6; }
.empty-state code {
  background: #f2f2f7;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "SF Mono", Menlo, monospace;
  font-size: 13px;
}

/* === Footer === */
.footer {
  text-align: center;
  font-size: 11px;
  opacity: 0.4;
  margin-top: 32px;
}

/* === Hide non-active tab content === */
.tab-content { display: none; }
.tab-content.active { display: block; }

/* === Responsive (mobile fallback) === */
@media (max-width: 600px) {
  .pills { grid-template-columns: repeat(2, 1fr); }
  .verdict-headline { font-size: 28px; }
  .hero-num { font-size: 48px; }
}
```

- [ ] **Step 2: Verificação visual rápida**

Não há teste automatizado pra CSS — só visual. Pula direto pra Task 5; o CSS será validado quando carregar o template no Step final do Task 9.

---

## Task 5: Template HTML — estrutura base + aba HOJE

**Files:**
- Create: `dash_template.html`

- [ ] **Step 1: Criar dash_template.html com estrutura base + aba HOJE**

Criar `dash_template.html`:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title|default("Health Dashboard") }} — {{ today_pretty }}</title>
<style>{{ css|safe }}</style>
</head>
<body>
<div class="dash">

  <div class="header">
    <div class="title">Health Dashboard</div>
    <div class="date">{{ today_pretty }} · gerado {{ generated_at }}</div>
  </div>

  <div class="tabs" role="tablist">
    <button class="tab active" data-tab="hoje" onclick="switchTab(this)">HOJE</button>
    <button class="tab" data-tab="trends" onclick="switchTab(this)">TRENDS</button>
    <button class="tab" data-tab="historico" onclick="switchTab(this)">HISTÓRICO</button>
  </div>

  {% if empty_state %}
  <div class="empty-state">
    <h2>Sem dados ainda</h2>
    <p>Rode <code>python health_daily.py --backfill 7</code> pra coletar a primeira semana.</p>
  </div>
  {% else %}

  {% if is_stale %}
  <div class="stale-banner">
    Dados de <strong>{{ today.date }}</strong> (não de hoje). Rode <code>python health_daily.py</code> pra atualizar.
  </div>
  {% endif %}

  <!-- ============ ABA HOJE ============ -->
  <div class="tab-content active" id="tab-hoje">

    <div class="verdict {{ verdict.color }}">
      <div class="verdict-row">
        <div>
          <div class="verdict-label">VEREDITO · {{ today_pretty_upper }}</div>
          <div class="verdict-headline">{{ verdict.headline }}</div>
        </div>
        <div class="verdict-badge">{{ verdict.headline.upper().split(" ")[0] }}</div>
      </div>
      {% if verdict.subtitle %}
      <div class="verdict-sub">{{ verdict.subtitle }}</div>
      {% endif %}
    </div>

    <!-- HRV hero com sparkline -->
    <div class="hero-card">
      <div>
        <div class="label-tiny">HRV — ÚLTIMA NOITE</div>
        <div class="hero-num-block">
          <span class="hero-num">{{ today.hrv_avg_overnight|default("—") }}</span>
          <span class="hero-unit">ms</span>
        </div>
        <div class="hero-meta">
          {% if hrv_delta is not none %}
            {% if hrv_delta < 0 %}↓ {{ hrv_delta|abs }} ms vs ontem{% else %}↑ {{ hrv_delta }} ms vs ontem{% endif %}
            ·
          {% endif %}
          alvo ≥32
        </div>
      </div>
      {% if hrv_spark_points %}
      <svg viewBox="0 0 200 90" style="width:200px;height:90px" class="spark-hrv">
        <line class="spark-target" x1="0" y1="{{ hrv_target_y }}" x2="200" y2="{{ hrv_target_y }}"/>
        <path class="spark-area" d="{{ hrv_area_path }}"/>
        <path class="spark-line" d="{{ hrv_line_path }}"/>
        <circle class="spark-dot" cx="{{ hrv_last_x }}" cy="{{ hrv_last_y }}"/>
      </svg>
      {% endif %}
    </div>

    <!-- 4 pills com delta -->
    <div class="pills">
      <div class="pill">
        <div class="pill-label">SONO</div>
        <div class="pill-value">{{ today.sleep_pretty|default("—") }}</div>
        {% if sleep_delta_pretty %}<div class="pill-delta {{ sleep_delta_class }}">{{ sleep_delta_pretty }}</div>{% endif %}
      </div>
      <div class="pill">
        <div class="pill-label">BB MAX</div>
        <div class="pill-value">{{ today.body_battery_max|default("—") }}</div>
        {% if bb_delta_pretty %}<div class="pill-delta {{ bb_delta_class }}">{{ bb_delta_pretty }}</div>{% endif %}
      </div>
      <div class="pill">
        <div class="pill-label">FCREP</div>
        <div class="pill-value">{{ today.resting_heart_rate|default("—") }}</div>
        {% if fcrep_delta_pretty %}<div class="pill-delta {{ fcrep_delta_class }}">{{ fcrep_delta_pretty }}</div>{% endif %}
      </div>
      <div class="pill">
        <div class="pill-label">READINESS</div>
        <div class="pill-value">{{ today.training_readiness|default("—") }}</div>
        {% if ready_delta_pretty %}<div class="pill-delta {{ ready_delta_class }}">{{ ready_delta_pretty }}</div>{% endif %}
      </div>
    </div>

    <!-- Sono por fase -->
    {% if today.sleep_duration_min %}
    <div class="sleep-card">
      <div class="label-tiny">SONO POR FASE</div>
      <div class="sleep-bar">
        <div class="sleep-rem" style="width:{{ sleep_pct.rem }}%"></div>
        <div class="sleep-deep" style="width:{{ sleep_pct.deep }}%"></div>
        <div class="sleep-light" style="width:{{ sleep_pct.light }}%"></div>
        <div class="sleep-awake" style="width:{{ sleep_pct.awake }}%"></div>
      </div>
      <div class="sleep-legend">
        <span class="lg-rem">REM {{ today.sleep_rem_min|default("—") }}</span>
        <span class="lg-deep">Deep {{ today.sleep_deep_min|default("—") }}</span>
        <span class="lg-light">Light {{ today.sleep_light_min|default("—") }}</span>
        <span class="lg-awake">Awake {{ today.sleep_awake_min|default("—") }}</span>
      </div>
    </div>
    {% endif %}

    <!-- BB curve do dia -->
    {% if bb_curve_path %}
    <div class="bb-curve-card">
      <div class="label-tiny">BODY BATTERY · 24H</div>
      <svg viewBox="0 0 800 80" style="width:100%;height:80px;margin-top:8px" class="spark-bb">
        <path class="spark-area" d="{{ bb_curve_area }}"/>
        <path class="spark-line" d="{{ bb_curve_path }}"/>
      </svg>
    </div>
    {% endif %}

  </div>

  <!-- TRENDS e HISTÓRICO virão nos próximos tasks -->
  <div class="tab-content" id="tab-trends"><p style="text-align:center;opacity:0.4;padding:40px">[Trends — Task 6]</p></div>
  <div class="tab-content" id="tab-historico"><p style="text-align:center;opacity:0.4;padding:40px">[Histórico — Task 7]</p></div>

  {% endif %}

  <div class="footer">RunTechOps · {{ generated_at }}</div>
</div>

<script>
function switchTab(btn) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
}
</script>
</body>
</html>
```

- [ ] **Step 2: Verificação — sintaxe Jinja2**

```powershell
python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('.')); env.get_template('dash_template.html'); print('Template syntax OK')"
```

Esperado: `Template syntax OK`. Se houver erro de sintaxe Jinja2, vai mostrar mensagem clara apontando linha.

---

## Task 6: Template HTML — aba TRENDS

**Files:**
- Modify: `dash_template.html` (substituir placeholder do tab-trends)

- [ ] **Step 1: Substituir placeholder do tab-trends**

Em `dash_template.html`, encontrar a linha `<div class="tab-content" id="tab-trends">` e substituir o placeholder pelo conteúdo:

```html
  <div class="tab-content" id="tab-trends">

    <div class="trends-period">
      <button class="active" data-period="7">7D</button>
      <button data-period="30">30D</button>
      <button data-period="90">90D</button>
    </div>

    {% for trend in trends %}
    <div class="trend-card">
      <div class="trend-card-head">
        <div class="label-tiny" style="color:{{ trend.color }}">{{ trend.label }}</div>
        <div class="trend-meta">média {{ trend.avg }} · alvo {{ trend.target_label }} · atual {{ trend.current }}</div>
      </div>
      {% if trend.points %}
      <svg viewBox="0 0 600 60" style="width:100%;height:60px" class="spark-{{ trend.css_class }}">
        <line class="spark-target" x1="0" y1="{{ trend.target_y }}" x2="600" y2="{{ trend.target_y }}"/>
        <path class="spark-area" d="{{ trend.area_path }}"/>
        <path class="spark-line" d="{{ trend.line_path }}"/>
        <circle class="spark-dot" cx="{{ trend.last_x }}" cy="{{ trend.last_y }}"/>
      </svg>
      {% else %}
      <p style="opacity:0.4;font-size:12px;text-align:center;padding:20px">Sem dados</p>
      {% endif %}
    </div>
    {% endfor %}

    <div class="trend-card">
      <div class="label-tiny">CORRELAÇÕES</div>
      {% if correlations_available %}
      <ul style="font-size:13px;margin-top:8px;line-height:1.6;padding-left:18px">
        {% for c in correlations %}<li>{{ c }}</li>{% endfor %}
      </ul>
      {% else %}
      <p style="opacity:0.55;font-size:13px;margin-top:6px">Coletando dados ({{ days_collected }}/14)</p>
      {% endif %}
    </div>

  </div>
```

- [ ] **Step 2: Verificar sintaxe Jinja2 novamente**

```powershell
python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('.')); env.get_template('dash_template.html'); print('Template OK')"
```

Esperado: `Template OK`.

---

## Task 7: Template HTML — aba HISTÓRICO

**Files:**
- Modify: `dash_template.html` (substituir placeholder do tab-historico + adicionar JS)

- [ ] **Step 1: Substituir placeholder do tab-historico**

Encontrar `<div class="tab-content" id="tab-historico">` e substituir:

```html
  <div class="tab-content" id="tab-historico">
    <div class="history-card">
      <table class="history-table" id="history-table">
        <thead>
          <tr>
            <th data-key="date" data-type="text">DATA</th>
            <th data-key="hrv_avg_overnight" data-type="num">HRV</th>
            <th data-key="sleep_pretty" data-type="text">SONO</th>
            <th data-key="body_battery_max" data-type="num">BB</th>
            <th data-key="resting_heart_rate" data-type="num">FCREP</th>
            <th data-key="training_readiness" data-type="num">READY</th>
            <th data-key="verdict_color" data-type="text">VEREDITO</th>
          </tr>
        </thead>
        <tbody>
          {% for r in history %}
          <tr data-raw="{{ r.raw_json_escaped|default('{}') }}" onclick="showRaw(this)">
            <td>{{ r.date }}</td>
            <td class="cell-{{ r.hrv_class|default('gray') }}">{{ r.hrv_avg_overnight|default("—") }}</td>
            <td>{{ r.sleep_pretty|default("—") }}</td>
            <td class="cell-{{ r.bb_class|default('gray') }}">{{ r.body_battery_max|default("—") }}</td>
            <td class="cell-{{ r.fcrep_class|default('gray') }}">{{ r.resting_heart_rate|default("—") }}</td>
            <td>{{ r.training_readiness|default("—") }}</td>
            <td class="cell-{{ r.verdict.color }}">{{ r.verdict.headline }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      <button class="export-btn" onclick="exportCSV()">↓ Export CSV</button>
    </div>

    <div class="modal-bg" id="modal-bg" onclick="if(event.target===this)hideModal()">
      <div class="modal">
        <button class="modal-close" onclick="hideModal()">×</button>
        <h3 style="margin-bottom:12px">raw_json do dia</h3>
        <pre id="modal-content"></pre>
      </div>
    </div>
  </div>
```

- [ ] **Step 2: Adicionar JS de ordenação, CSV e modal**

No bloco `<script>` no fim do template (após a função `switchTab`), adicionar:

```javascript
function sortTable(th) {
  const table = th.closest('table');
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const colIdx = Array.from(th.parentNode.children).indexOf(th);
  const type = th.dataset.type;
  const asc = th.dataset.dir !== 'asc';
  th.parentNode.querySelectorAll('th').forEach(t => delete t.dataset.dir);
  th.dataset.dir = asc ? 'asc' : 'desc';
  rows.sort((a, b) => {
    let av = a.children[colIdx].textContent.trim();
    let bv = b.children[colIdx].textContent.trim();
    if (type === 'num') {
      av = parseFloat(av) || -Infinity;
      bv = parseFloat(bv) || -Infinity;
    }
    return asc ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
  });
  rows.forEach(r => tbody.appendChild(r));
}
document.querySelectorAll('#history-table th').forEach(th => th.onclick = () => sortTable(th));

function exportCSV() {
  const table = document.getElementById('history-table');
  const rows = Array.from(table.querySelectorAll('tr'));
  const csv = rows.map(r => Array.from(r.querySelectorAll('th,td'))
    .map(c => '"' + c.textContent.replace(/"/g, '""').trim() + '"').join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'health_history_' + new Date().toISOString().slice(0, 10) + '.csv';
  a.click();
  URL.revokeObjectURL(url);
}

function showRaw(tr) {
  const raw = tr.dataset.raw || '{}';
  let pretty;
  try { pretty = JSON.stringify(JSON.parse(raw), null, 2); }
  catch { pretty = raw; }
  document.getElementById('modal-content').textContent = pretty;
  document.getElementById('modal-bg').classList.add('show');
}
function hideModal() {
  document.getElementById('modal-bg').classList.remove('show');
}

// Period toggle (placeholder — re-render via Python; client-side só destaca o botão)
document.querySelectorAll('.trends-period button').forEach(b => {
  b.onclick = () => {
    document.querySelectorAll('.trends-period button').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    // Future: requisitar re-render. Por enquanto só visual.
  };
});
```

- [ ] **Step 3: Verificar sintaxe**

```powershell
python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('.')); env.get_template('dash_template.html'); print('Template OK')"
```

Esperado: `Template OK`.

---

## Task 8: Módulo `dash_render.py` (rendering)

**Files:**
- Create: `dash_render.py`

- [ ] **Step 1: Criar dash_render.py**

```python
"""Renderiza dash_template.html com dados shaped + escreve dash.html + abre browser."""
import json
import shutil
import webbrowser
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


PT_BR_DAY = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
PT_BR_MONTH = ["jan", "fev", "mar", "abr", "mai", "jun",
               "jul", "ago", "set", "out", "nov", "dez"]


def _pretty_date(iso_date):
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{PT_BR_DAY[d.weekday()]} {d.day} {PT_BR_MONTH[d.month - 1]}"


def _sleep_pretty(minutes):
    if minutes is None:
        return None
    h = minutes // 60
    m = minutes % 60
    return f"{h}h{m:02d}"


def _build_sparkline(points, target=None, width=200, height=60, padding=5):
    """points: lista [(date, value), ...] mais antigo→recente. value pode ser None.
    Retorna dict com line_path, area_path, last_x, last_y, target_y (se target setado).
    """
    valid = [(i, v) for i, (_, v) in enumerate(points) if v is not None]
    if not valid:
        return None
    values = [v for _, v in valid]
    vmin = min(values)
    vmax = max(values)
    if target is not None:
        vmin = min(vmin, target)
        vmax = max(vmax, target)
    if vmin == vmax:
        vmax = vmin + 1
    n = len(points)
    def x_of(idx): return padding + (idx * (width - 2 * padding) / max(n - 1, 1))
    def y_of(val): return height - padding - ((val - vmin) / (vmax - vmin)) * (height - 2 * padding)
    pts = [(x_of(i), y_of(v)) for i, v in valid]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    area = line + f" L{pts[-1][0]:.1f},{height} L{pts[0][0]:.1f},{height} Z"
    return {
        "line_path": line,
        "area_path": area,
        "last_x": f"{pts[-1][0]:.1f}",
        "last_y": f"{pts[-1][1]:.1f}",
        "target_y": f"{y_of(target):.1f}" if target is not None else None,
        "min": vmin, "max": vmax,
    }


def _build_bb_curve(points, width=800, height=80, padding=4):
    """BB curve do dia 24h. points: [(timestamp_ms, value)]."""
    if not points:
        return None
    ts_min = min(p[0] for p in points)
    ts_max = max(p[0] for p in points)
    if ts_max == ts_min:
        ts_max = ts_min + 1
    vmin = 0
    vmax = 100
    def x_of(ts): return padding + (ts - ts_min) / (ts_max - ts_min) * (width - 2 * padding)
    def y_of(v): return height - padding - (v - vmin) / (vmax - vmin) * (height - 2 * padding)
    pts = [(x_of(ts), y_of(v)) for ts, v in points]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    area = line + f" L{pts[-1][0]:.1f},{height} L{pts[0][0]:.1f},{height} Z"
    return {"line_path": line, "area_path": area}


def _delta_class(value, lower_better=False):
    if value is None or value == 0:
        return "delta-neutral"
    positive_good = (value > 0) ^ lower_better
    return "delta-up" if positive_good else "delta-down"


def _delta_pretty(value, suffix=""):
    if value is None:
        return None
    sign = "+" if value > 0 else ""
    return f"{sign}{value}{suffix}"


def _hrv_class(v):
    if v is None: return "gray"
    if v >= 32: return "green"
    if v >= 26: return "amber"
    return "red"


def _bb_class(v):
    if v is None: return "gray"
    if v >= 65: return "green"
    if v >= 50: return "amber"
    return "red"


def _fcrep_class(v):
    if v is None: return "gray"
    if v <= 52: return "green"
    if v <= 54: return "amber"
    return "red"


def build_context(today_row, history_with_verdicts, deltas, override=None):
    """Monta o dict que vai pra Jinja2.

    Args:
        today_row: linha de hoje (ou ultima disponivel)
        history_with_verdicts: lista de rows enriquecidas (DESC), incluindo today
        deltas: dict de deltas vs ontem
        override: dict opcional {headline, color, subtitle} (CLI flags)

    Returns:
        dict pronto pra render.
    """
    from dash_data import parse_bb_curve, trend_series

    today_iso = today_row["date"]
    today_pretty = _pretty_date(today_iso)

    # Verdict — usa o ja computado no enrichment (primeira posicao do history) ou override
    verdict = history_with_verdicts[0]["verdict"]
    if override:
        verdict = {
            "color": override.get("color", "amber"),
            "headline": override["headline"],
            "subtitle": override.get("subtitle", ""),
        }

    today_with_extras = dict(today_row)
    today_with_extras["sleep_pretty"] = _sleep_pretty(today_row.get("sleep_duration_min"))

    # Sleep breakdown percentages
    total = today_row.get("sleep_duration_min") or 0
    sleep_pct = {"rem": 0, "deep": 0, "light": 0, "awake": 0}
    if total > 0:
        sleep_pct = {
            "rem":   round((today_row.get("sleep_rem_min")   or 0) / total * 100, 1),
            "deep":  round((today_row.get("sleep_deep_min")  or 0) / total * 100, 1),
            "light": round((today_row.get("sleep_light_min") or 0) / total * 100, 1),
            "awake": round((today_row.get("sleep_awake_min") or 0) / total * 100, 1),
        }

    # HRV sparkline 7d
    hrv_points = trend_series(history_with_verdicts, "hrv_avg_overnight", n=7)
    hrv_spark = _build_sparkline([p for p in hrv_points], target=32, width=200, height=90, padding=10)

    # BB curve do dia
    bb_curve = _build_bb_curve(parse_bb_curve(today_row.get("raw_json")))

    # Trends: 5 sparklines
    trend_specs = [
        ("HRV OVERNIGHT", "hrv_avg_overnight", "#ff3b30", "hrv",   32,  " 32"),
        ("SONO TOTAL",    "sleep_duration_min", "#0a84ff", "sleep", 480, " 8h"),
        ("BB MAX",        "body_battery_max", "#bf5af2", "bb",    70,  " 70"),
        ("FC REPOUSO",    "resting_heart_rate", "#30d158", "fcrep", 51,  " 51"),
        ("READINESS",     "training_readiness", "#ff9500", "ready", 65,  " 65"),
    ]
    trends = []
    for label, col, color, css, target, target_label in trend_specs:
        pts = trend_series(history_with_verdicts, col, n=7)
        spark = _build_sparkline(pts, target=target, width=600, height=60, padding=8)
        valid_vals = [v for _, v in pts if v is not None]
        avg = round(sum(valid_vals) / len(valid_vals), 1) if valid_vals else "—"
        current = valid_vals[-1] if valid_vals else "—"
        trend = {
            "label": label, "color": color, "css_class": css,
            "target_label": target_label, "avg": avg, "current": current,
            "points": pts,
        }
        if spark:
            trend.update({
                "line_path": spark["line_path"],
                "area_path": spark["area_path"],
                "last_x": spark["last_x"],
                "last_y": spark["last_y"],
                "target_y": spark["target_y"],
            })
        trends.append(trend)

    # História para tabela
    history_render = []
    for r in history_with_verdicts:
        item = dict(r)
        item["sleep_pretty"] = _sleep_pretty(r.get("sleep_duration_min"))
        item["hrv_class"] = _hrv_class(r.get("hrv_avg_overnight"))
        item["bb_class"] = _bb_class(r.get("body_battery_max"))
        item["fcrep_class"] = _fcrep_class(r.get("resting_heart_rate"))
        item["raw_json_escaped"] = (r.get("raw_json") or "{}").replace('"', '&quot;')
        history_render.append(item)

    days_collected = len(history_with_verdicts)
    correlations_available = days_collected >= 14

    return {
        "today": today_with_extras,
        "today_pretty": today_pretty,
        "today_pretty_upper": today_pretty.upper(),
        "verdict": verdict,
        "is_stale": False,  # caller seta
        "empty_state": False,
        "generated_at": datetime.now().strftime("%H:%M:%S"),
        # HRV sparkline
        "hrv_spark_points": bool(hrv_spark),
        "hrv_line_path": hrv_spark["line_path"] if hrv_spark else "",
        "hrv_area_path": hrv_spark["area_path"] if hrv_spark else "",
        "hrv_last_x": hrv_spark["last_x"] if hrv_spark else "0",
        "hrv_last_y": hrv_spark["last_y"] if hrv_spark else "0",
        "hrv_target_y": hrv_spark["target_y"] if hrv_spark and hrv_spark["target_y"] else "0",
        "hrv_delta": deltas.get("hrv_avg_overnight"),
        # Pills deltas
        "sleep_delta_pretty": _delta_pretty(deltas.get("sleep_duration_min"), " min"),
        "sleep_delta_class": _delta_class(deltas.get("sleep_duration_min")),
        "bb_delta_pretty": _delta_pretty(deltas.get("body_battery_max")),
        "bb_delta_class": _delta_class(deltas.get("body_battery_max")),
        "fcrep_delta_pretty": _delta_pretty(deltas.get("resting_heart_rate"), " bpm"),
        "fcrep_delta_class": _delta_class(deltas.get("resting_heart_rate"), lower_better=True),
        "ready_delta_pretty": _delta_pretty(deltas.get("training_readiness")),
        "ready_delta_class": _delta_class(deltas.get("training_readiness")),
        # Sleep breakdown
        "sleep_pct": sleep_pct,
        # BB curve
        "bb_curve_path": bb_curve["line_path"] if bb_curve else "",
        "bb_curve_area": bb_curve["area_path"] if bb_curve else "",
        # Trends
        "trends": trends,
        "correlations": [],
        "correlations_available": correlations_available,
        "days_collected": days_collected,
        # Histórico
        "history": history_render,
    }


def render_html(context, template_path="dash_template.html", css_path="dash_styles.css"):
    """Renderiza HTML completo com CSS embutido."""
    base = Path(template_path).parent
    env = Environment(
        loader=FileSystemLoader(str(base) if str(base) else "."),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(Path(template_path).name)
    css = Path(css_path).read_text(encoding="utf-8")
    return template.render(css=css, **context)


def write_and_open(html, output_path="dash.html", archive=False, open_browser=True):
    """Escreve HTML, opcionalmente arquiva, opcionalmente abre no browser."""
    out = Path(output_path)
    out.write_text(html, encoding="utf-8")
    if archive:
        archive_dir = out.parent / "dash_archive"
        archive_dir.mkdir(exist_ok=True)
        archive_path = archive_dir / f"dash-{datetime.now().strftime('%Y-%m-%d')}.html"
        shutil.copy(out, archive_path)
    if open_browser:
        webbrowser.open(out.resolve().as_uri())
    return out


def render_empty_state(template_path="dash_template.html", css_path="dash_styles.css"):
    """Renderiza tela 'sem dados' quando DB existe mas vazio."""
    context = {
        "empty_state": True,
        "today_pretty": datetime.now().strftime("%a %d %b").lower(),
        "today_pretty_upper": "",
        "generated_at": datetime.now().strftime("%H:%M:%S"),
    }
    return render_html(context, template_path, css_path)
```

- [ ] **Step 2: Smoke test rápido — renderizar com 4 dias reais**

```powershell
python -c "
from dash_data import load_history, get_today_row, enrich_with_verdicts, compute_deltas
from dash_render import build_context, render_html, write_and_open
rows = load_history('runtech.db', days=30)
enriched = enrich_with_verdicts(rows)
today_row = enriched[0]
prev_row = enriched[1] if len(enriched) > 1 else None
deltas = compute_deltas(today_row, prev_row) if prev_row else {}
ctx = build_context(today_row, enriched, deltas)
html = render_html(ctx)
print(f'HTML length: {len(html)}')
print('OK' if 'Descanso' in html else 'FAIL: veredito esperado')
"
```

Esperado: `HTML length: ~25000` (ou similar) e `OK`. Se falhar com KeyError ou TemplateError, revisar nome de variável Jinja2 vs Python context.

---

## Task 9: CLI — `dash_today.py`

**Files:**
- Create: `dash_today.py`

- [ ] **Step 1: Criar dash_today.py com argparse e orquestração**

```python
"""dash_today.py — gera dash.html a partir de runtech.db e abre no browser.

Uso:
    python dash_today.py                                    # default
    python dash_today.py --no-open                          # nao abre browser
    python dash_today.py --verdict "LR7 reservado" --color amber
    python dash_today.py --archive                          # salva snapshot dash-YYYY-MM-DD.html
    python dash_today.py --db custom.db
"""
import argparse
import sys
from datetime import date
from pathlib import Path

from dash_data import load_history, enrich_with_verdicts, compute_deltas
from dash_render import build_context, render_html, write_and_open, render_empty_state


def main():
    p = argparse.ArgumentParser(description="Gera dash.html dos dados de saude diarios")
    p.add_argument("--db", default="runtech.db", help="Path do SQLite")
    p.add_argument("--output", default="dash.html", help="Path do HTML de saida")
    p.add_argument("--no-open", action="store_true", help="Nao abrir no browser apos gerar")
    p.add_argument("--archive", action="store_true", help="Tambem salvar em dash_archive/")
    p.add_argument("--verdict", help="Override headline do veredito")
    p.add_argument("--color", choices=["green", "amber", "orange", "red"], help="Override cor do veredito")
    p.add_argument("--subtitle", help="Override sub-mensagem do veredito")
    args = p.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERRO: DB nao encontrado em {db_path}.", file=sys.stderr)
        print(f"      Rode 'python health_daily.py' primeiro pra criar.", file=sys.stderr)
        return 1

    try:
        rows = load_history(str(db_path), days=30)
    except FileNotFoundError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1

    if not rows:
        # DB vazio
        html = render_empty_state()
        write_and_open(html, output_path=args.output, archive=False, open_browser=not args.no_open)
        print(f"[OK] {args.output} (empty state)")
        return 0

    enriched = enrich_with_verdicts(rows)
    today_iso = date.today().isoformat()
    today_row = enriched[0]
    is_stale = today_row["date"] != today_iso
    prev_row = enriched[1] if len(enriched) > 1 else None
    deltas = compute_deltas(today_row, prev_row) if prev_row else {}

    override = None
    if args.verdict:
        override = {
            "headline": args.verdict,
            "color": args.color or "amber",
            "subtitle": args.subtitle or "",
        }

    ctx = build_context(today_row, enriched, deltas, override=override)
    ctx["is_stale"] = is_stale

    html = render_html(ctx)
    out_path = write_and_open(
        html,
        output_path=args.output,
        archive=args.archive,
        open_browser=not args.no_open,
    )
    print(f"[OK] {out_path} gerado.")
    if is_stale:
        print(f"     Aviso: ultimo dado e de {today_row['date']} (nao de hoje).")
    if args.archive:
        print(f"     Snapshot tambem em dash_archive/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Rodar — primeira execução real**

```powershell
python dash_today.py --no-open
```

Esperado: `[OK] dash.html gerado.` Se erro, ler stack trace e corrigir.

- [ ] **Step 3: Verificar que dash.html foi escrito**

```powershell
Test-Path dash.html
Get-Item dash.html | Select-Object Length
```

Esperado: `True` e Length > 20000 bytes (HTML grande com CSS embutido).

- [ ] **Step 4: Abrir dash.html no Chrome manualmente**

```powershell
Start-Process chrome dash.html
```

Esperado: visualmente o HTML carrega, 3 abas aparecem, aba HOJE mostra:
- Veredito laranja "Descanso recomendado"
- HRV 27 com sparkline
- 4 pills com valores
- Sono por fase com barra colorida
- BB curve do dia (se raw_json tem dados)

Click nas abas TRENDS e HISTÓRICO — devem trocar de conteúdo.

---

## Task 10: Testes de edge cases (continuação)

**Files:**
- Modify: `test_dash.py` (adicionar testes de edge cases)

- [ ] **Step 1: Adicionar testes de edge cases ao test_dash.py**

Append antes do `if __name__`:

```python
# ===== Edge cases ponta-a-ponta =====
def test_no_db_exits_with_error():
    import subprocess
    r = subprocess.run(
        [sys.executable, "dash_today.py", "--db", "/nonexistent/none.db", "--no-open"],
        capture_output=True, text=True,
    )
    assert r.returncode == 1
    assert "DB nao encontrado" in r.stderr or "DB não encontrado" in r.stderr


def test_empty_db_renders_empty_state():
    """DB existe mas vazio — vai pra empty_state."""
    db = _create_test_db([])
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, "dash_today.py", "--db", db, "--output", "test_dash_empty.html", "--no-open"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"
        html = Path("test_dash_empty.html").read_text(encoding="utf-8")
        assert "Sem dados ainda" in html
    finally:
        os.unlink(db)
        Path("test_dash_empty.html").unlink(missing_ok=True)


def test_today_missing_shows_stale_banner():
    """Apenas dado de ontem — banner stale aparece."""
    from datetime import date, timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    db = _create_test_db([
        {"date": yesterday, "hrv_avg_overnight": 30, "body_battery_max": 65,
         "resting_heart_rate": 52, "sleep_score": 75},
    ])
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, "dash_today.py", "--db", db, "--output", "test_dash_stale.html", "--no-open"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        html = Path("test_dash_stale.html").read_text(encoding="utf-8")
        assert "stale-banner" in html
        assert yesterday in html
    finally:
        os.unlink(db)
        Path("test_dash_stale.html").unlink(missing_ok=True)


def test_verdict_override_with_color():
    db = _create_test_db([
        {"date": "2026-05-08", "hrv_avg_overnight": 27, "body_battery_max": 54,
         "resting_heart_rate": 53, "sleep_score": 78},
    ])
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, "dash_today.py", "--db", db, "--output", "test_dash_ov.html",
             "--no-open", "--verdict", "LR7 RESERVADO", "--color", "amber"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"
        html = Path("test_dash_ov.html").read_text(encoding="utf-8")
        assert "LR7 RESERVADO" in html
        assert 'class="verdict amber"' in html
    finally:
        os.unlink(db)
        Path("test_dash_ov.html").unlink(missing_ok=True)


def test_verdict_override_default_color_amber():
    db = _create_test_db([
        {"date": "2026-05-08", "hrv_avg_overnight": 27, "body_battery_max": 54,
         "resting_heart_rate": 53, "sleep_score": 78},
    ])
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, "dash_today.py", "--db", db, "--output", "test_dash_ov2.html",
             "--no-open", "--verdict", "Custom"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        html = Path("test_dash_ov2.html").read_text(encoding="utf-8")
        assert 'class="verdict amber"' in html
    finally:
        os.unlink(db)
        Path("test_dash_ov2.html").unlink(missing_ok=True)


def test_under_7_days_renders_with_partial_data():
    """3 dias só — sparkline desenha sem padding."""
    db = _create_test_db([
        {"date": "2026-05-06", "hrv_avg_overnight": 29, "body_battery_max": 69,
         "resting_heart_rate": 51, "sleep_score": 80},
        {"date": "2026-05-07", "hrv_avg_overnight": 34, "body_battery_max": 73,
         "resting_heart_rate": 51, "sleep_score": 78},
        {"date": "2026-05-08", "hrv_avg_overnight": 27, "body_battery_max": 54,
         "resting_heart_rate": 53, "sleep_score": 78},
    ])
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, "dash_today.py", "--db", db, "--output", "test_dash_3d.html", "--no-open"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        html = Path("test_dash_3d.html").read_text(encoding="utf-8")
        # Spark exists but with 3 points, plus correlations placeholder
        assert "Coletando dados" in html
    finally:
        os.unlink(db)
        Path("test_dash_3d.html").unlink(missing_ok=True)
```

- [ ] **Step 2: Rodar todos os testes**

```powershell
python test_dash.py
```

Esperado: todos passando — total ~23 testes (9 verdict + 8 data + 6 edge cases).

Se algum falhar, ler mensagem e ajustar. Edge cases tendem a expor problemas reais no `dash_today.py` ou render.

---

## Task 11: Validação visual com dados reais

**Files:** nenhum a modificar — só validação humana.

- [ ] **Step 1: Gerar dash.html com seus dados de hoje**

```powershell
python dash_today.py
```

Browser abre automaticamente no `dash.html`.

- [ ] **Step 2: Conferir aba HOJE contra mockup `synthesis.html`**

Abrir lado-a-lado:
- `dash.html` (gerado)
- `.superpowers/brainstorm/1404-1778243114/content/synthesis.html` (mockup)

Confirmar visualmente:
- [ ] Veredito laranja com mesma cor de gradiente
- [ ] Headline "Descanso recomendado" com mesmo peso/tamanho
- [ ] Badge no canto direito ("DESCANSO")
- [ ] HRV "27 ms" enorme em vermelho
- [ ] Sparkline 7d com linha tracejada do alvo
- [ ] 4 pills brancas com mesmas tipografias
- [ ] Sono por fase com barra estratificada (REM violeta, Deep magenta, Light azul, Awake laranja)
- [ ] BB curve do dia carregou

- [ ] **Step 3: Conferir aba TRENDS**

Click em "TRENDS":
- [ ] Toggle 7D/30D/90D aparece (botão 7D destacado)
- [ ] 5 trend cards com sparklines coloridos
- [ ] Bloco de correlações mostra "Coletando dados (4/14)"

- [ ] **Step 4: Conferir aba HISTÓRICO**

Click em "HISTÓRICO":
- [ ] Tabela com 4 linhas (datas 05/05 - 08/05)
- [ ] Coluna VEREDITO mostra cores corretas (Descanso/Atenção/Pronto/Descanso)
- [ ] Click no cabeçalho "DATA" ordena
- [ ] Click numa linha abre modal com raw_json
- [ ] Click em "Export CSV" baixa um .csv

- [ ] **Step 5: Documentar approval**

Se tudo OK, anotar em `diario/2026-05-08.md` (append):

```markdown
## Health Dashboard v1 entregue
Dashboard `dash_today.py` em produção. Lê `runtech.db`, renderiza HTML estilo iOS Health, abre no browser.
3 abas: Hoje (veredito + métricas), Trends (sparklines 7d), Histórico (tabela ordenável + CSV).
Validação visual aprovada.
```

Se algo desalinha do mockup, listar os deltas e ajustar CSS/template antes de seguir.

---

## Task 12: Hook em `health_daily.py`

**Files:**
- Modify: `health_daily.py`

- [ ] **Step 1: Adicionar chain call ao final do main()**

Em `health_daily.py`, encontrar o final da função `main()` (próximo ao `print(f"[OK] Gravado em {args.db}")`). Adicionar **antes** do return/fim da função:

```python
    # Hook: gera dash automaticamente apos run default (hoje, sem backfill)
    if (
        not args.backfill
        and not args.backfill_from
        and not args.date
        and not args.quiet
        and success_count > 0
    ):
        dash_script = Path(__file__).parent / "dash_today.py"
        if dash_script.exists():
            try:
                import subprocess
                print(f"\n[+] Gerando dashboard...")
                subprocess.run([sys.executable, str(dash_script)], check=False)
            except Exception as e:
                print(f"     (dash skipped: {e})")
```

- [ ] **Step 2: Testar fluxo end-to-end**

```powershell
python health_daily.py --quiet 2026-05-08
```

Esperado: roda fetch (talvez "[OK] Gravado") **sem** chamar dash (porque `--quiet` ou `args.date` setados desabilitam o hook).

```powershell
python health_daily.py
```

Esperado: roda fetch normal **+** mensagem `[+] Gerando dashboard...` **+** browser abre com `dash.html`. Se o browser não abrir (ex: porque já tem janela aberta), pelo menos `dash.html` foi regerado.

---

## Task 13: Documentação

**Files:**
- Modify: `README.md`
- Modify: `SETUP.md` (se existir)

- [ ] **Step 1: Atualizar README.md**

Adicionar seção sobre o dashboard. Exemplo de patch (adapta ao formato existente do README):

```markdown
## Dashboard de saúde diário

`dash_today.py` gera um painel HTML estilo iOS Health a partir de `runtech.db`:

```bash
python dash_today.py                       # gera + abre browser
python dash_today.py --no-open             # so gera
python dash_today.py --verdict "LR7" --color amber   # override veredito
python dash_today.py --archive             # tambem salva em dash_archive/
```

3 abas: **Hoje** (veredito + métricas + breakdown), **Trends** (5 sparklines 7d), **Histórico** (tabela ordenável + export CSV).

Roda automaticamente no fim de `python health_daily.py` quando sem flags.
```

- [ ] **Step 2: Atualizar SETUP.md (se existir e for relevante)**

Se há seção "Como usar no dia-a-dia" no SETUP.md, mencionar dash_today.py.

- [ ] **Step 3: Verificação final do checklist do spec**

Abrir `docs/superpowers/specs/2026-05-08-health-dashboard-design.md` Seção 10 (Definition of done) e confirmar que cada item está check:
- [x] dash_today.py gera dash.html com 3 abas funcionais
- [x] Veredito implementado e validado contra 4 dias
- [x] Override --verdict / --color / --subtitle funciona
- [x] CSS gera fidelidade visual com mockup synthesis.html
- [x] Smoke tests passam
- [x] Validação visual em Chrome aprovada
- [x] Hook em health_daily.py
- [x] .gitignore atualizado
- [x] requirements.txt inclui Jinja2
- [x] README atualizado

Se tudo check → entrega completa.

---

## Self-Review (post-write)

**Spec coverage:** Seção 1 (propósito) → coberta no architecture do plan. Seção 2 (decisões) → todas no plan. Seção 3 (arquitetura) → Tasks 8-9. Seção 4 (verdict) → Task 2. Seção 5 (componentes/abas) → Tasks 5-7. Seção 6 (edge cases) → Task 10. Seção 7 (testing) → tasks têm passos de teste. Seção 8 (integração health_daily) → Task 12. Seção 9 (.gitignore) → Task 1. Seção 10 (DoD) → Task 13. Seção 11 (parking lot) → respeitado.

**Placeholder scan:** Sem TBDs/TODOs. Cada step tem código completo. Visual fidelity check em Task 11 tem checklist explícita.

**Type consistency:** `compute_verdict` retorna dict `{score, color, headline, subtitle, evaluated_count}` consistente entre Task 2 (definição) e Tasks 8-10 (consumo). `enrich_with_verdicts` mantém shape dos rows + adiciona `verdict`. `_build_sparkline` retorna dict `{line_path, area_path, last_x, last_y, target_y, min, max}` ou `None` — consistentes.
