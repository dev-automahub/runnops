"""Renderiza dash_template.html com dados shaped + escreve dash.html + abre browser."""
import json
import shutil
import webbrowser
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from dash_data import parse_bb_curve, trend_series
from dash_verdict import (
    HRV_GREEN_MIN, HRV_AMBER_MIN,
    BB_GREEN_MIN, BB_AMBER_MIN,
    FCREP_GREEN_MAX, FCREP_AMBER_MAX,
    FCREP_BASELINE,
)


PT_BR_DAY = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
PT_BR_MONTH = ["jan", "fev", "mar", "abr", "mai", "jun",
               "jul", "ago", "set", "out", "nov", "dez"]


def _pretty_date(iso_date):
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{PT_BR_DAY[d.weekday()]} {d.day} {PT_BR_MONTH[d.month - 1]}"


def _int_str(v):
    """Formata int ou float-com-parte-decimal-zero como int. 31.0 → '31', 31.5 → '31.5'."""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


def _short_date(iso_date, compact=False):
    """Retorna 'qua 06' ou (se compact) '06'."""
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    if compact:
        return f"{d.day:02d}"
    return f"{PT_BR_DAY[d.weekday()]} {d.day:02d}"


def _date_brazilian(iso_date):
    """2026-05-09 → 09/05/2026"""
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return d.strftime("%d/%m/%Y")


def _sleep_pretty(minutes):
    if minutes is None:
        return None
    h = minutes // 60
    m = minutes % 60
    if h == 0:
        return f"{m} min"
    return f"{h}h{m:02d}"


def _seconds_to_time(sec):
    """Segundos -> 'h:mm:ss' (ex: 8078 -> '2h14:38'). Retorna None se sec inválido."""
    if sec is None:
        return None
    try:
        sec = int(sec)
    except (TypeError, ValueError):
        return None
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _seconds_to_pace_per_km(sec, distance_km):
    """Tempo total + distância -> 'mm:ss/km' (pace medio)."""
    if sec is None or not distance_km:
        return None
    try:
        pace_sec = int(sec) / distance_km
        m, s = divmod(int(round(pace_sec)), 60)
        return f"{m}:{s:02d}/km"
    except (TypeError, ValueError, ZeroDivisionError):
        return None


# Metas do macrociclo 2026 — usadas pra comparar com Race Predictor
RACE_TARGETS = {
    "5k":  None,             # sem meta dura
    "10k": None,
    "half": (7980, 8220),    # 2h13:00 - 2h17:00 (Meia do Rio 06/06)
    "marathon": (14400,),    # 4h00:00 declarada (30/08)
}


def _race_status(predicted_sec, target):
    """Compara predicao com meta. Retorna ('green'|'amber'|'red', delta_pretty)."""
    if predicted_sec is None or target is None:
        return ("gray", None)
    try:
        pred = int(predicted_sec)
    except (TypeError, ValueError):
        return ("gray", None)

    if len(target) == 2:
        lo, hi = target
        if pred <= hi:
            return ("green", "dentro da meta")
        gap = pred - hi
        return ("amber" if gap < 600 else "red", f"+{_seconds_to_time(gap)} vs alvo {_seconds_to_time(hi)}")
    else:
        meta = target[0]
        if pred <= meta:
            return ("green", "dentro da meta")
        gap = pred - meta
        if gap < 1800:
            color = "amber"
        else:
            color = "red"
        return (color, f"+{_seconds_to_time(gap)} vs meta {_seconds_to_time(meta)}")


def _build_sparkline(points, target=None, target_label=None,
                     value_formatter=lambda v: str(v),
                     width=600, height=100,
                     pad_top=20, pad_bottom=22, pad_left=8, pad_right=8,
                     compact_dates=False):
    """points: lista [(date_iso, value), ...] mais antigo→recente. value pode ser None.

    Retorna dict ou None:
        line_path:    str (SVG path d)
        target_y:     str (y coord da linha tracejada) ou None
        target_label: str (ex: "≥32") ou None
        plot_points:  lista de dict, um por ponto válido, contendo:
            x, y           (coords no viewBox)
            value          (numero)
            value_label    (str formatado, ex: "27" ou "7h27")
            date_label     (str ex: "06" se compact_dates, senao "qua 06")
            is_last        (bool — true so pra o ultimo ponto)
    """
    valid = [(i, date, v) for i, (date, v) in enumerate(points) if v is not None]
    if not valid:
        return None
    values = [v for _, _, v in valid]
    vmin = min(values)
    vmax = max(values)
    if target is not None:
        vmin = min(vmin, target)
        vmax = max(vmax, target)
    if vmin == vmax:
        vmax = vmin + 1
    n = len(points)

    def x_of(idx):
        return pad_left + (idx * (width - pad_left - pad_right) / max(n - 1, 1))

    def y_of(val):
        return height - pad_bottom - ((val - vmin) / (vmax - vmin)) * (height - pad_top - pad_bottom)

    pts = [(x_of(i), y_of(v), date, v) for i, date, v in valid]
    line = " ".join(
        f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"
        for i, (x, y, _, _) in enumerate(pts)
    )

    last_idx = len(pts) - 1
    plot_points = []
    for i, (x, y, date, v) in enumerate(pts):
        plot_points.append({
            "x": f"{x:.1f}",
            "y": f"{y:.1f}",
            "value": v,
            "value_label": value_formatter(v),
            "date_label": _short_date(date, compact=compact_dates),
            "is_last": (i == last_idx),
        })

    if target_label is None and target is not None:
        target_label = f"≥{target}"

    return {
        "line_path": line,
        "target_y": f"{y_of(target):.1f}" if target is not None else None,
        "target_label": target_label,
        "plot_points": plot_points,
    }


def _build_bb_curve(points, width=800, height=200, pad_top=46, pad_bottom=38, pad_lr=30):
    """BB curve do dia 24h. points: [(timestamp_ms, value)].
    Retorna line_path + 3 marcadores: max, min, atual (com valor + posicao)."""
    if not points:
        return None
    ts_min = min(p[0] for p in points)
    ts_max = max(p[0] for p in points)
    if ts_max == ts_min:
        ts_max = ts_min + 1
    vmin = 0
    vmax = 100
    def x_of(ts): return pad_lr + (ts - ts_min) / (ts_max - ts_min) * (width - 2 * pad_lr)
    def y_of(v): return height - pad_bottom - (v - vmin) / (vmax - vmin) * (height - pad_top - pad_bottom)
    pts = [(x_of(ts), y_of(v), v) for ts, v in points]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y, _) in enumerate(pts))

    max_pt = max(points, key=lambda p: p[1])
    min_pt = min(points, key=lambda p: p[1])
    cur_pt = points[-1]

    def marker(p, label_pos="above"):
        """label_pos: 'above' (y-18) ou 'below' (y+30)."""
        x, y = x_of(p[0]), y_of(p[1])
        # Clamp x para que label não saia das bordas (assumindo largura do label ~30px)
        label_x = max(30, min(width - 30, x))
        return {
            "x": f"{x:.1f}",
            "y": f"{y:.1f}",
            "label_x": f"{label_x:.1f}",
            "value": int(p[1]),
            "label_y": f"{y - 18:.1f}" if label_pos == "above" else f"{y + 30:.1f}",
        }

    # Estratégia: max e current "above"; min "below" (porque já está embaixo da curva)
    return {
        "line_path": line,
        "max": marker(max_pt, "above"),
        "min": marker(min_pt, "below"),
        "current": marker(cur_pt, "above"),
    }


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
    if v >= HRV_GREEN_MIN: return "green"
    if v >= HRV_AMBER_MIN: return "amber"
    return "red"


def _bb_class(v):
    if v is None: return "gray"
    if v >= BB_GREEN_MIN: return "green"
    if v >= BB_AMBER_MIN: return "amber"
    return "red"


def _fcrep_class(v):
    if v is None: return "gray"
    if v <= FCREP_GREEN_MAX: return "green"
    if v <= FCREP_AMBER_MAX: return "amber"
    return "red"


def build_context(today_row, history_with_verdicts, deltas, override=None, diario_dir=None):
    """Monta o dict que vai pra Jinja2.

    Args:
        today_row: linha de hoje (ou ultima disponivel)
        history_with_verdicts: lista de rows enriquecidas (DESC), incluindo today
        deltas: dict de deltas vs ontem
        override: dict opcional {headline, color, subtitle} (CLI flags)

    Returns:
        dict pronto pra render.
    """
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
    today_with_extras["sleep_rem_pretty"] = _sleep_pretty(today_row.get("sleep_rem_min"))
    today_with_extras["sleep_deep_pretty"] = _sleep_pretty(today_row.get("sleep_deep_min"))
    today_with_extras["sleep_light_pretty"] = _sleep_pretty(today_row.get("sleep_light_min"))
    today_with_extras["sleep_awake_pretty"] = _sleep_pretty(today_row.get("sleep_awake_min"))

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

    # HRV sparkline 7d (hero card — 280×140, datas compactas)
    hrv_points = trend_series(history_with_verdicts, "hrv_avg_overnight", n=7)
    hrv_spark = _build_sparkline(
        hrv_points,
        target=HRV_GREEN_MIN,
        target_label=f"≥{HRV_GREEN_MIN}",
        value_formatter=_int_str,
        width=280, height=140,
        pad_top=30, pad_bottom=28, pad_left=30, pad_right=30,
        compact_dates=True,
    )

    # BB curve do dia
    bb_curve = _build_bb_curve(parse_bb_curve(today_row.get("raw_json")))

    # Trends: 5 sparklines (600×100, datas verbosas)
    trend_specs = [
        ("HRV OVERNIGHT",     "hrv_avg_overnight",   "#ff3b30", "hrv",   HRV_GREEN_MIN,  f"≥{HRV_GREEN_MIN}",  _int_str),
        ("SONO",              "sleep_duration_min",  "#0a84ff", "sleep", 480,            "≥8h",                _sleep_pretty),
        ("BODY BATTERY MAX",  "body_battery_max",    "#bf5af2", "bb",    70,             "≥70",                _int_str),
        ("FC REPOUSO",        "resting_heart_rate",  "#30d158", "fcrep", FCREP_BASELINE, f"~{FCREP_BASELINE}", _int_str),
        ("DISPOSIÇÃO",        "training_readiness",  "#ff9500", "ready", 65,             "≥65",                _int_str),
    ]
    trends = []
    for label, col, color, css, target, target_label, fmt in trend_specs:
        pts = trend_series(history_with_verdicts, col, n=7)
        spark = _build_sparkline(
            pts,
            target=target,
            target_label=target_label,
            value_formatter=fmt,
            width=600, height=220,
            pad_top=58, pad_bottom=52, pad_left=44, pad_right=44,
            compact_dates=False,
        )
        valid_vals = [v for _, v in pts if v is not None]
        if valid_vals:
            avg_int = round(sum(valid_vals) / len(valid_vals))
            avg = fmt(avg_int)
            current = fmt(valid_vals[-1])
        else:
            avg = "—"
            current = "—"
        trend = {
            "label": label, "color": color, "css_class": css,
            "target_label": target_label, "avg": avg, "current": current,
            "points": pts,
        }
        if spark:
            trend.update({
                "line_path": spark["line_path"],
                "target_y": spark["target_y"],
                "plot_points": spark["plot_points"],
            })
        else:
            trend.update({
                "line_path": "",
                "target_y": None,
                "plot_points": [],
            })
        trends.append(trend)

    # Diários (carrega MD de cada dia do histórico, se existir)
    from dash_data import load_journals_for_dates
    journal_dates = [r["date"] for r in history_with_verdicts]
    journals_raw = load_journals_for_dates(diario_dir, journal_dates)
    journals = []
    for j in journals_raw:
        journals.append({
            "date": j["date"],
            "date_pretty": _date_brazilian(j["date"]),
            "date_long": _pretty_date(j["date"]),
            "html": j["html"],
            "has_content": j["html"] is not None,
        })

    # História para tabela
    def _or_dash(v):
        return "—" if v is None else v

    history_render = []
    for r in history_with_verdicts:
        item = dict(r)
        item["date_pretty"] = _date_brazilian(r["date"])
        sleep_p = _sleep_pretty(r.get("sleep_duration_min"))
        item["sleep_pretty"] = sleep_p if sleep_p is not None else "—"
        item["hrv_pretty"] = _int_str(r["hrv_avg_overnight"]) if r.get("hrv_avg_overnight") is not None else "—"
        item["bb_pretty"] = _or_dash(r.get("body_battery_max"))
        item["fcrep_pretty"] = _or_dash(r.get("resting_heart_rate"))
        item["ready_pretty"] = _or_dash(r.get("training_readiness"))
        item["hrv_class"] = _hrv_class(r.get("hrv_avg_overnight"))
        item["bb_class"] = _bb_class(r.get("body_battery_max"))
        item["fcrep_class"] = _fcrep_class(r.get("resting_heart_rate"))
        history_render.append(item)

    days_collected = len(history_with_verdicts)
    correlations_available = days_collected >= 14

    # ============ Plano da semana + Próximo treino (scheduled_workout) ============
    from dash_data import load_scheduled_workouts, load_sessions_for_week
    from datetime import date as date_cls
    today_iso_str = date_cls.today().isoformat()
    iso = date_cls.today().isocalendar()
    current_week_id = f"{iso[0]}-W{iso[1]:02d}"

    week_scheduled = load_scheduled_workouts("runtech.db", week_id=current_week_id)
    week_sessions = load_sessions_for_week("runtech.db", current_week_id)
    # Index sessions por scheduled_id (match preferido) e por data (fallback)
    sessions_by_scheduled = {s["scheduled_id"]: s for s in week_sessions if s.get("scheduled_id")}
    sessions_by_date = {(s["date_iso"] or "")[:10]: s for s in week_sessions}

    def _pace_pretty(sec_per_km):
        if sec_per_km is None:
            return None
        m = int(sec_per_km // 60)
        s = int(sec_per_km % 60)
        return f"{m}:{s:02d}/km"

    def _build_session_real(sess):
        """Monta string de métricas reais ('15.0km · FC 132 · cad 158 spm · pace 7:28/km')."""
        if not sess:
            return None
        parts = []
        if sess.get("distance_km"):
            parts.append(f"{sess['distance_km']:.1f}km")
        if sess.get("avg_hr"):
            parts.append(f"FC {sess['avg_hr']}")
        if sess.get("avg_cadence_spm"):
            parts.append(f"cad {sess['avg_cadence_spm']:.0f}")
        pace = _pace_pretty(sess.get("avg_pace_sec_per_km"))
        if pace:
            parts.append(pace)
        return " · ".join(parts) if parts else None

    week_plan = []
    next_workout = None
    for w in week_scheduled:
        d_iso = w["date_iso"]
        d_obj = date_cls.fromisoformat(d_iso)
        day_short = PT_BR_DAY[d_obj.weekday()]

        # Match preferencial: scheduled_id; fallback: data
        matched_session = (
            sessions_by_scheduled.get(w["scheduled_id"])
            or sessions_by_date.get(d_iso)
        )

        if matched_session:
            status = "done"
            status_icon = "✅"
            status_label = "feito"
        elif d_iso < today_iso_str:
            status = "missed"
            status_icon = "⚪"
            status_label = "não executado"
        elif d_iso == today_iso_str:
            status = "today"
            status_icon = "🔵"
            status_label = "HOJE"
        else:
            status = "pending"
            status_icon = "⏳"
            status_label = "pendente"
            if next_workout is None:
                next_workout = {
                    "date_iso": d_iso,
                    "date_pretty": f"{day_short} {d_obj.strftime('%d/%m')}",
                    "title": w["title"],
                    "days_until": (d_obj - date_cls.today()).days,
                }
        week_plan.append({
            "date_iso": d_iso,
            "date_pretty": f"{day_short} {d_obj.strftime('%d/%m')}",
            "title": w["title"],
            "status": status,
            "status_icon": status_icon,
            "status_label": status_label,
            "session_real": _build_session_real(matched_session),
        })

    # Stats do plano da semana
    plan_total = len(week_plan)
    plan_done = sum(1 for p in week_plan if p["status"] == "done")
    plan_today = sum(1 for p in week_plan if p["status"] == "today")
    plan_pending = sum(1 for p in week_plan if p["status"] == "pending")
    plan_missed = sum(1 for p in week_plan if p["status"] == "missed")
    # Aderencia (so faz sentido quando ja ha treinos passados ou de hoje)
    plan_evaluated = plan_done + plan_missed
    plan_adherence_pct = round(plan_done / plan_evaluated * 100, 0) if plan_evaluated else None

    has_week_plan = bool(week_plan)

    # ============ Weekly Summary (aggregate_activities.py) ============
    from dash_data import load_weekly_summary
    weekly_rows_raw = load_weekly_summary("runtech.db", n=8)
    weekly_rows = list(reversed(weekly_rows_raw))  # ASC: mais antigo -> recente

    def _pace_pretty(sec_per_km):
        if sec_per_km is None:
            return "—"
        m = int(sec_per_km // 60)
        s = int(sec_per_km % 60)
        return f"{m}:{s:02d}/km"

    weekly_render = []
    for i, w in enumerate(weekly_rows):
        prev = weekly_rows[i - 1] if i > 0 else None
        def delta(field, lower_better=False):
            if not prev or w.get(field) is None or prev.get(field) is None:
                return None
            d = w[field] - prev[field]
            if d == 0:
                return None
            sign = "+" if d > 0 else ""
            return f"{sign}{d:.1f}" if isinstance(d, float) else f"{sign}{d}"

        weekly_render.append({
            "week_id": w["week_id"],
            "week_start_iso": w.get("week_start_iso"),
            "sessions_count": w["sessions_count"],
            "total_km": f"{w['total_distance_km']:.1f}",
            "total_km_delta": delta("total_distance_km"),
            "avg_cad": f"{w['avg_cadence_spm']:.1f}" if w.get("avg_cadence_spm") else "—",
            "avg_cad_delta": delta("avg_cadence_spm"),
            "pct_aerobico": f"{w['pct_aerobico']:.1f}%" if w.get("pct_aerobico") is not None else "—",
            "pct_aerobico_delta": delta("pct_aerobico"),
            "pace_pretty": _pace_pretty(w.get("avg_pace_sec_per_km")),
            "longest_km": f"{w['longest_session_km']:.1f}" if w.get("longest_session_km") else "—",
            "is_current": (i == len(weekly_rows) - 1),
        })
    # Reverte de volta — DESC pra exibir mais recente no topo
    weekly_render = list(reversed(weekly_render))

    # ============ Performance Garmin (Training Status + Load + Race Predictor) ============
    race_preds = []
    for key, label, col in [
        ("5k",       "5K",       "race_predicted_5k_sec"),
        ("10k",      "10K",      "race_predicted_10k_sec"),
        ("half",     "21K",      "race_predicted_half_sec"),
        ("marathon", "MARATONA", "race_predicted_marathon_sec"),
    ]:
        sec = today_row.get(col)
        color, delta_label = _race_status(sec, RACE_TARGETS.get(key))
        target = RACE_TARGETS.get(key)
        target_label = None
        if target:
            target_label = _seconds_to_time(target[0]) if len(target) == 1 else f"{_seconds_to_time(target[0])}–{_seconds_to_time(target[1])}"
        race_preds.append({
            "label": label,
            "time": _seconds_to_time(sec) or "—",
            "pace": _seconds_to_pace_per_km(sec, {"5k": 5, "10k": 10, "half": 21.0975, "marathon": 42.195}[key]),
            "target_label": target_label,
            "delta_label": delta_label,
            "color": color,
        })

    # ACWR badge color
    acwr = today_row.get("load_ratio")
    if acwr is None:
        acwr_color = "gray"
        acwr_status = "—"
    elif 0.8 <= acwr <= 1.3:
        acwr_color = "green"
        acwr_status = "Optimal"
    elif acwr < 0.8:
        acwr_color = "amber"
        acwr_status = "Baixo"
    elif acwr <= 1.5:
        acwr_color = "amber"
        acwr_status = "Alto"
    else:
        acwr_color = "red"
        acwr_status = "Muito alto"

    perf = {
        "training_status": today_row.get("training_status") or "—",
        "training_status_feedback": today_row.get("training_status_feedback") or "",
        "vo2_max_trend": today_row.get("vo2_max_trend") or "",
        "vo2_max": today_row.get("vo2_max"),
        "fitness_age": today_row.get("fitness_age"),
        "fitness_age_pretty": (f"{float(today_row['fitness_age']):.1f}"
                               if today_row.get("fitness_age") is not None else "—"),
        "acute_load": today_row.get("acute_load"),
        "chronic_load_low": today_row.get("chronic_load_low"),
        "chronic_load_high": today_row.get("chronic_load_high"),
        "chronic_load_range_pretty": (
            f"{int(today_row['chronic_load_low'])}–{int(today_row['chronic_load_high'])}"
            if today_row.get("chronic_load_low") is not None
            and today_row.get("chronic_load_high") is not None else "—"
        ),
        "acwr": acwr,
        "acwr_pretty": (f"{acwr:.2f}" if acwr is not None else "—"),
        "acwr_color": acwr_color,
        "acwr_status": acwr_status,
        "recovery_time_hours": today_row.get("recovery_time_hours"),
        "recovery_time_pretty": (
            f"{today_row['recovery_time_hours']:.1f}h" if today_row.get("recovery_time_hours") is not None else "—"
        ),
        "race_preds": race_preds,
    }
    has_perf = any([
        today_row.get("training_status"),
        today_row.get("acute_load") is not None,
        any(today_row.get(c) for c in
            ("race_predicted_5k_sec", "race_predicted_10k_sec",
             "race_predicted_half_sec", "race_predicted_marathon_sec")),
    ])

    return {
        "today": today_with_extras,
        "today_pretty": today_pretty,
        "today_pretty_upper": today_pretty.upper(),
        "verdict": verdict,
        "is_stale": False,  # caller seta
        "empty_state": False,
        "generated_at": datetime.now().strftime("%H:%M:%S"),
        # HRV sparkline (Opcao B)
        "hrv_line_path": hrv_spark["line_path"] if hrv_spark else "",
        "hrv_target_y": hrv_spark["target_y"] if hrv_spark and hrv_spark["target_y"] else None,
        "hrv_target_label": hrv_spark["target_label"] if hrv_spark else None,
        "hrv_plot_points": hrv_spark["plot_points"] if hrv_spark else [],
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
        "bb_curve_max": bb_curve["max"] if bb_curve else None,
        "bb_curve_min": bb_curve["min"] if bb_curve else None,
        "bb_curve_current": bb_curve["current"] if bb_curve else None,
        # Trends
        "trends": trends,
        "correlations": [],
        "correlations_available": correlations_available,
        "days_collected": days_collected,
        # Histórico
        "history": history_render,
        # Diarios diarios (analises por dia em MD)
        "journals": journals,
        # Glossário (carregado tardiamente abaixo)
        "glossary": _load_glossary(),
        # Performance Garmin (Training Status + ATL/CTL/ACWR + Race Predictor)
        "perf": perf,
        "has_perf": has_perf,
        # Weekly summary (aggregate_activities.py)
        "weekly": weekly_render,
        "has_weekly": bool(weekly_render),
        # Plano da semana + proximo treino (scheduled_workout)
        "week_plan": week_plan,
        "current_week_id": current_week_id,
        "has_week_plan": has_week_plan,
        "plan_total": plan_total,
        "plan_done": plan_done,
        "plan_today": plan_today,
        "plan_pending": plan_pending,
        "plan_missed": plan_missed,
        "plan_adherence_pct": plan_adherence_pct,
        "next_workout": next_workout,
    }


def _load_glossary():
    """Carrega entradas do glossário com HTML renderizado."""
    try:
        from dash_glossary import get_glossary
        return get_glossary()
    except ImportError:
        return []


def render_html(context, template_path="dash_template.html", css_path="dash_styles.css"):
    """Renderiza HTML completo com CSS embutido (single-file, todas as abas)."""
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
