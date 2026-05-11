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
    "training_status", "training_status_feedback",
    "acute_load", "chronic_load_low", "chronic_load_high", "load_ratio",
    "vo2_max_trend", "fitness_age", "recovery_time_hours",
    "race_predicted_5k_sec", "race_predicted_10k_sec",
    "race_predicted_half_sec", "race_predicted_marathon_sec",
    "raw_json",
]


def load_weekly_summary(db_path, n=8):
    """Le ultimas N semanas da tabela weekly_summary. Vazio se tabela nao existir."""
    if not Path(db_path).exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT * FROM weekly_summary ORDER BY week_id DESC LIMIT ?", (n,)
            )
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.OperationalError:
            return []
    finally:
        conn.close()


def load_history(db_path, days=30):
    """Le ate N dias mais recentes da tabela health_daily, ordenados desc por date."""
    if not Path(db_path).exists():
        raise FileNotFoundError(f"DB nao encontrado: {db_path}")
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            f"SELECT {','.join(HISTORY_COLS)} FROM health_daily "
            f"ORDER BY date DESC LIMIT ?",
            (days,),
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
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


def load_journal_html(diario_dir, date_iso):
    """Le o arquivo diario/YYYY-MM-DD.md e retorna HTML renderizado.

    Retorna None se o arquivo nao existir.
    """
    if not diario_dir:
        return None
    path = Path(diario_dir) / f"{date_iso}.md"
    if not path.exists():
        return None
    try:
        import markdown as md_lib
    except ImportError:
        return None
    md_text = path.read_text(encoding="utf-8")
    html = md_lib.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])
    # Wrappa tabelas em div com scroll horizontal para mobile portrait
    html = html.replace("<table>", '<div class="md-table-wrap"><table>')
    html = html.replace("</table>", "</table></div>")
    return html


def load_journals_for_dates(diario_dir, dates):
    """Carrega diarios de varias datas. Retorna lista de dicts ordenada DESC.

    Cada item: {date: 'YYYY-MM-DD', html: '...' ou None}
    Datas sem MD recebem html=None.
    """
    journals = []
    for date_iso in dates:
        journals.append({
            "date": date_iso,
            "html": load_journal_html(diario_dir, date_iso),
        })
    return journals


def trend_series(rows, metric, n=7, skip_nulls=True):
    """Extrai serie temporal pra sparkline. Retorna [(date, value), ...] mais antigo->recente.

    skip_nulls=True: dias sem dado pra essa metrica sao filtrados (evita gaps no grafico).
    skip_nulls=False: dias com null incluidos (rendererrespeita posicao calendarica).
    """
    sliced = rows[:n]
    sliced = list(reversed(sliced))  # antigo->recente
    pairs = [(r["date"], r.get(metric)) for r in sliced]
    if skip_nulls:
        pairs = [(d, v) for d, v in pairs if v is not None]
    return pairs
