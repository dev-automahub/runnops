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
        # Garantir que raw_json e JSON valido (Garmin pode mandar None ou string mal formada)
        raw = r.get("raw_json") or "{}"
        try:
            json.loads(raw)  # valida
            item["raw_json_escaped"] = raw  # autoescape do Jinja cuida da atribuicao HTML
        except (ValueError, TypeError):
            item["raw_json_escaped"] = "{}"
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
    }


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
