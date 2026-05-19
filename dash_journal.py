"""dash_journal.py - Escreve/atualiza o diario MD com a reportagem matinal auto-gerada.

Usa marcadores DASH_AUTO_START/END para preservar conteudo manual ao re-rodar.

Uso programatico:
    from dash_journal import update_journal
    update_journal(diario_dir, today_row, prev_row, verdict)
"""
from datetime import datetime
from pathlib import Path

AUTO_START = "<!-- DASH_AUTO_START -->"
AUTO_END = "<!-- DASH_AUTO_END -->"

PT_BR_DAY = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
PT_BR_MONTH = ["jan", "fev", "mar", "abr", "mai", "jun",
               "jul", "ago", "set", "out", "nov", "dez"]


def _pretty_date(iso_date):
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{PT_BR_DAY[d.weekday()]} {d.day} {PT_BR_MONTH[d.month - 1]}"


def _sleep_pretty(minutes):
    if minutes is None:
        return "—"
    h = minutes // 60
    m = minutes % 60
    if h == 0:
        return f"{m} min"
    return f"{h}h{m:02d}"


def _int_or_dash(v):
    if v is None:
        return "—"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


def _delta_arrow(today, yesterday, lower_better=False):
    """Retorna string formatada do delta com seta. Ex: '+4 ⬆' ou '−2 ⬇'."""
    if today is None or yesterday is None:
        return "—"
    diff = today - yesterday
    if isinstance(diff, float) and diff == int(diff):
        diff = int(diff)
    if diff == 0:
        return "0 (igual)"
    arrow = "⬆" if diff > 0 else "⬇"
    sign = "+" if diff > 0 else "−"
    val = abs(diff)
    # Inverter sentido do "good" para metricas onde menor e melhor (FCrep)
    return f"{sign}{val} {arrow}"


def _build_auto_section(today_row, prev_row, verdict):
    """Gera o bloco markdown da reportagem matinal."""
    today_iso = today_row["date"]
    today_pretty = _pretty_date(today_iso)

    hrv = today_row.get("hrv_avg_overnight")
    bb_max = today_row.get("body_battery_max")
    bb_min = today_row.get("body_battery_min")
    fcrep = today_row.get("resting_heart_rate")
    sleep_score = today_row.get("sleep_score")
    sleep_dur = today_row.get("sleep_duration_min")
    rem = today_row.get("sleep_rem_min")
    deep = today_row.get("sleep_deep_min")
    light = today_row.get("sleep_light_min")
    awake = today_row.get("sleep_awake_min")
    stress_avg = today_row.get("stress_avg")
    stress_max = today_row.get("stress_max")
    ready = today_row.get("training_readiness")

    # Deltas vs ontem
    if prev_row:
        hrv_d = _delta_arrow(hrv, prev_row.get("hrv_avg_overnight"))
        bb_d = _delta_arrow(bb_max, prev_row.get("body_battery_max"))
        fcrep_d = _delta_arrow(fcrep, prev_row.get("resting_heart_rate"), lower_better=True)
        sleep_d = _delta_arrow(sleep_dur, prev_row.get("sleep_duration_min"))
        ready_d = _delta_arrow(ready, prev_row.get("training_readiness"))
    else:
        hrv_d = bb_d = fcrep_d = sleep_d = ready_d = "—"

    bb_pair = f"{_int_or_dash(bb_max)} / {_int_or_dash(bb_min)}"

    lines = []
    lines.append(AUTO_START)
    lines.append("## Reportagem matinal")
    lines.append("")
    lines.append(f"_Auto-gerado {datetime.now().strftime('%H:%M')}_")
    lines.append("")
    lines.append("| Métrica | Valor | Δ vs ontem |")
    lines.append("|---|---|---|")
    lines.append(f"| HRV overnight | **{_int_or_dash(hrv)} ms** | {hrv_d} |")
    lines.append(f"| BB max / min | **{bb_pair}** | {bb_d} |")
    lines.append(f"| FCrep | **{_int_or_dash(fcrep)} bpm** | {fcrep_d} |")
    lines.append(f"| Sleep Score | **{_int_or_dash(sleep_score)}** | — |")
    lines.append(f"| Sono total | **{_sleep_pretty(sleep_dur)}** | {sleep_d} |")
    lines.append(f"| REM | **{_sleep_pretty(rem)}** | — |")
    lines.append(f"| Deep | **{_sleep_pretty(deep)}** | — |")
    lines.append(f"| Light | **{_sleep_pretty(light)}** | — |")
    lines.append(f"| Awake | **{_sleep_pretty(awake)}** | — |")
    lines.append(f"| Stress avg / max | **{_int_or_dash(stress_avg)} / {_int_or_dash(stress_max)}** | — |")
    lines.append(f"| Disposição (Garmin Readiness) | **{_int_or_dash(ready)}** | {ready_d} |")
    lines.append("")
    lines.append("### Veredito automático")
    lines.append("")
    headline = verdict.get("headline", "—") if verdict else "—"
    color = verdict.get("color", "gray") if verdict else "gray"
    score = verdict.get("score", "—") if verdict else "—"
    subtitle = verdict.get("subtitle", "") if verdict else ""
    color_emoji = {"green": "🟢", "amber": "🟡", "orange": "🟠", "red": "🔴", "gray": "⚪"}.get(color, "⚪")
    lines.append(f"{color_emoji} **{headline}** (score {score})")
    if subtitle:
        lines.append("")
        lines.append(f"_{subtitle}_")
    lines.append("")
    lines.append(AUTO_END)
    return "\n".join(lines)


SKELETON_TEMPLATE = """# Diário {date_pretty}

{auto_section}

## O que aconteceu

_(análise pendente — adicionar contexto: como dormiu, sintomas, eventos do dia anterior, sensações ao acordar)_

## Decisão / Veredito

_(análise pendente — alinhar com plano da semana, gates de HRV/BB, decisão de treino)_

## Pendências

- [ ] _(adicionar tarefas/promessas do dia)_
"""


def update_journal(diario_dir, today_row, prev_row=None, verdict=None):
    """Atualiza/cria o arquivo diario/YYYY-MM-DD.md com reportagem matinal auto-gerada.

    - Se MD nao existe: cria com SKELETON_TEMPLATE preenchido
    - Se MD ja existe: substitui apenas a secao entre AUTO_START e AUTO_END

    Retorna (path, action) onde action e 'created' | 'updated' | 'skipped'.
    """
    if not diario_dir:
        return None, "skipped"
    diario = Path(diario_dir)
    diario.mkdir(parents=True, exist_ok=True)

    today_iso = today_row["date"]
    today_pretty = _pretty_date(today_iso)
    auto_section = _build_auto_section(today_row, prev_row, verdict)

    path = diario / f"{today_iso}.md"

    if not path.exists():
        # Cria do zero a partir do template
        content = SKELETON_TEMPLATE.format(
            date_pretty=f"{today_iso} ({PT_BR_DAY[datetime.strptime(today_iso, '%Y-%m-%d').weekday()]})",
            auto_section=auto_section,
        )
        path.write_text(content, encoding="utf-8")
        return path, "created"

    # MD ja existe — substitui apenas a secao auto-gerada
    existing = path.read_text(encoding="utf-8")
    if AUTO_START in existing and AUTO_END in existing:
        before = existing.split(AUTO_START)[0]
        after = existing.split(AUTO_END, 1)[1]
        new_content = before + auto_section + after
        path.write_text(new_content, encoding="utf-8")
        return path, "updated"
    else:
        # MD existe mas sem marcadores — adiciona auto_section no topo (apos h1 se houver)
        lines = existing.split("\n", 1)
        if lines and lines[0].startswith("#"):
            new_content = lines[0] + "\n\n" + auto_section + ("\n\n" + lines[1] if len(lines) > 1 else "")
        else:
            new_content = auto_section + "\n\n" + existing
        path.write_text(new_content, encoding="utf-8")
        return path, "updated"
