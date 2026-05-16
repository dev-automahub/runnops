"""Lógica do veredito do dashboard. Pure functions, sem I/O."""

FCREP_BASELINE = 49  # recalibrado 16/05/2026 (era 51, agora confirmado pelo Garmin)

# Score thresholds (named to avoid magic numbers in scoring functions)
HRV_GREEN_MIN = 32      # >= 32 → 0 pts
HRV_AMBER_MIN = 26      # 26-31 → 1 pt; <26 → 2 pts
BB_GREEN_MIN = 65
BB_AMBER_MIN = 50
FCREP_GREEN_MAX = 52    # <=52 → 0 pts
FCREP_AMBER_MAX = 54    # 53-54 → 1 pt; >=55 → 2 pts
SLEEP_GREEN_MIN = 75
SLEEP_AMBER_MIN = 60

# Modifier magnitudes
HRV_DROP_THRESHOLD_MS = 5
FCREP_RISE_THRESHOLD_BPM = 3


def score_hrv(value):
    if value is None:
        return None
    if value >= HRV_GREEN_MIN:
        return 0
    if value >= HRV_AMBER_MIN:
        return 1
    return 2


def score_bb(value):
    if value is None:
        return None
    if value >= BB_GREEN_MIN:
        return 0
    if value >= BB_AMBER_MIN:
        return 1
    return 2


def score_fcrep(value):
    if value is None:
        return None
    if value <= FCREP_GREEN_MAX:
        return 0
    if value <= FCREP_AMBER_MAX:
        return 1
    return 2


def score_sleep(value):
    if value is None:
        return None
    if value >= SLEEP_GREEN_MIN:
        return 0
    if value >= SLEEP_AMBER_MIN:
        return 1
    return 2


def hrv_drop_modifier(today_hrv, yesterday_hrv):
    """Soma 1 se HRV caiu >= 5 ms vs ontem."""
    if today_hrv is None or yesterday_hrv is None:
        return 0
    if (yesterday_hrv - today_hrv) >= HRV_DROP_THRESHOLD_MS:
        return 1
    return 0


def fcrep_rise_modifier(today_fcrep, baseline=FCREP_BASELINE):
    """Soma 1 se FCrep subiu >= 3 bpm vs baseline."""
    if today_fcrep is None:
        return 0
    if (today_fcrep - baseline) >= FCREP_RISE_THRESHOLD_BPM:
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
        headline = "Atenção: Prioriza Z2"
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
