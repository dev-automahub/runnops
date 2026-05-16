"""Smoke tests pra dash_today. Roda sem pytest: python test_dash.py"""
import sys

from dash_verdict import FCREP_BASELINE

# ===== Fixtures: linhas reais dos 4 dias coletados =====
ROW_05 = {"date": "2026-05-05", "hrv_avg_overnight": 29, "body_battery_max": 29,
          "resting_heart_rate": None, "sleep_score": None}
ROW_06 = {"date": "2026-05-06", "hrv_avg_overnight": 29, "body_battery_max": 69,
          "resting_heart_rate": 51, "sleep_score": 80}
ROW_07 = {"date": "2026-05-07", "hrv_avg_overnight": 34, "body_battery_max": 73,
          "resting_heart_rate": 51, "sleep_score": None}
ROW_08 = {"date": "2026-05-08", "hrv_avg_overnight": 27, "body_battery_max": 54,
          "resting_heart_rate": 53, "sleep_score": 78}

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
    # Baseline atual = 49 (recalibrado 16/05/2026)
    assert fcrep_rise_modifier(52, FCREP_BASELINE) == 1  # +3 vs baseline 49
    assert fcrep_rise_modifier(51, FCREP_BASELINE) == 0  # +2 (< 3)
    assert fcrep_rise_modifier(48, FCREP_BASELINE) == 0  # abaixo
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
    # Baseline FCrep=49 (recalibrado 16/05): fcrep 53 = +4 → +1 mod → score sobe pra 5 (vermelho)
    assert v08["score"] == 5, f"08/05 esperado 5, veio {v08['score']}"
    assert v08["color"] == "red"
    assert v08["headline"] == "Corte forçado"

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

# ===== Testes do dash_data =====
import sqlite3
import tempfile
import os
import json

def _create_test_db(rows):
    """Cria DB temporário usando o init_db do health_daily (mantém parity com schema real)."""
    from pathlib import Path
    from health_daily import init_db

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        conn = init_db(Path(tmp.name))
        try:
            for r in rows:
                cols = ",".join(r.keys())
                ph = ",".join(["?"] * len(r))
                conn.execute(f"INSERT INTO health_daily ({cols}) VALUES ({ph})", list(r.values()))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        os.unlink(tmp.name)
        raise
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
    # Baseline 49 (recalibrado 16/05/2026): 08/05 fcrep 53 dispara +1 mod → score 5 → red
    assert enriched[0]["verdict"]["color"] == "red"     # 08
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
            [sys.executable, "dash_today.py", "--db", db, "--output", "test_dash_empty.html", "--no-open", "--no-journal"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"
        from pathlib import Path
        html = Path("test_dash_empty.html").read_text(encoding="utf-8")
        assert "Sem dados ainda" in html
    finally:
        os.unlink(db)
        from pathlib import Path
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
            [sys.executable, "dash_today.py", "--db", db, "--output", "test_dash_stale.html", "--no-open", "--no-journal"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        from pathlib import Path
        html = Path("test_dash_stale.html").read_text(encoding="utf-8")
        assert "stale-banner" in html
        assert yesterday in html
    finally:
        os.unlink(db)
        from pathlib import Path
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
             "--no-open", "--no-journal", "--verdict", "LR7 RESERVADO", "--color", "amber"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"
        from pathlib import Path
        html = Path("test_dash_ov.html").read_text(encoding="utf-8")
        assert "LR7 RESERVADO" in html
        assert 'verdict amber' in html
    finally:
        os.unlink(db)
        from pathlib import Path
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
             "--no-open", "--no-journal", "--verdict", "Custom"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        from pathlib import Path
        html = Path("test_dash_ov2.html").read_text(encoding="utf-8")
        assert 'verdict amber' in html
    finally:
        os.unlink(db)
        from pathlib import Path
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
            [sys.executable, "dash_today.py", "--db", db, "--output", "test_dash_3d.html", "--no-open", "--no-journal"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        from pathlib import Path
        html = Path("test_dash_3d.html").read_text(encoding="utf-8")
        assert "Coletando dados" in html
    finally:
        os.unlink(db)
        from pathlib import Path
        Path("test_dash_3d.html").unlink(missing_ok=True)


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
