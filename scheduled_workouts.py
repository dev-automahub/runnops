"""
scheduled_workouts.py - Baixa treinos do calendario Garmin Connect (semana atual + proxima)
e grava em SQLite (tabela scheduled_workout) + gera MD por semana.

Uso:
    python scheduled_workouts.py                  # semana atual + proxima
    python scheduled_workouts.py --weeks 4         # proximas 4 semanas
    python scheduled_workouts.py --db custom.db    # outro path
"""
import argparse
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from garminconnect import Garmin

DB_PATH = Path("runtech.db")
PLANO_DIR = Path("2026-05-04-protocolo-recuperacao-corrida-rua-amador/planos-semana")

SCHEMA = """
CREATE TABLE IF NOT EXISTS scheduled_workout (
    scheduled_id INTEGER PRIMARY KEY,
    workout_id INTEGER,
    date_iso TEXT NOT NULL,
    week_id TEXT,
    title TEXT NOT NULL,
    sport TEXT,
    fetched_at TEXT
);
"""

PT_BR_DAY = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def _week_id(d):
    """date -> 'YYYY-Www'."""
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _week_monday(week_id):
    """'2026-W20' -> date(2026,5,11)."""
    year, week = week_id.split("-W")
    return datetime.strptime(f"{year}-{int(week)}-1", "%G-%V-%u").date()


def login_garmin():
    load_dotenv()
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        sys.exit("ERRO: configure GARMIN_EMAIL e GARMIN_PASSWORD em .env")
    g = Garmin(email, password)
    g.login()
    return g


def fetch_workouts(g, target_dates):
    """Retorna lista de workouts agendados nas datas alvo. Faz 1 call por mes distinto."""
    months_needed = sorted({(d.year, d.month) for d in target_dates})
    target_set = {d.isoformat() for d in target_dates}

    items = []
    for year, month in months_needed:
        try:
            data = g.get_scheduled_workouts(year, month)
        except Exception as e:
            print(f"  [!] Erro ao buscar {year}-{month:02d}: {e}", file=sys.stderr)
            continue
        for it in data.get("calendarItems", []):
            if it.get("itemType") != "workout":
                continue
            d_iso = it.get("date")
            if d_iso not in target_set:
                continue
            items.append({
                "scheduled_id": it.get("id"),
                "workout_id": it.get("workoutId"),
                "date_iso": d_iso,
                "week_id": _week_id(date.fromisoformat(d_iso)),
                "title": it.get("title", "").strip(),
                "sport": it.get("sportTypeKey"),
            })
    return items


def upsert_all(conn, items):
    now = datetime.now().isoformat(timespec="seconds")
    for it in items:
        conn.execute(
            "INSERT INTO scheduled_workout "
            "(scheduled_id, workout_id, date_iso, week_id, title, sport, fetched_at) "
            "VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(scheduled_id) DO UPDATE SET "
            "workout_id=excluded.workout_id, date_iso=excluded.date_iso, "
            "week_id=excluded.week_id, title=excluded.title, sport=excluded.sport, "
            "fetched_at=excluded.fetched_at",
            (it["scheduled_id"], it["workout_id"], it["date_iso"], it["week_id"],
             it["title"], it["sport"], now),
        )
    conn.commit()


def write_week_md(week_id, items_for_week):
    """Escreve MD da semana em planos-semana/plano-semana-YYYY-Www.md."""
    PLANO_DIR.mkdir(parents=True, exist_ok=True)
    monday = _week_monday(week_id)
    sunday = monday + timedelta(days=6)

    lines = [
        f"# Plano da semana {week_id}",
        "",
        f"**Janela:** {monday.strftime('%d/%m')} a {sunday.strftime('%d/%m/%Y')} ({PT_BR_DAY[monday.weekday()]} a {PT_BR_DAY[sunday.weekday()]})",
        f"_Gerado por `scheduled_workouts.py` em {datetime.now().strftime('%d/%m/%Y %H:%M')}._",
        "",
        "## Treinos agendados",
        "",
    ]
    if not items_for_week:
        lines.append("_(nenhum treino agendado no Garmin Connect pra essa semana)_")
    else:
        items_sorted = sorted(items_for_week, key=lambda i: i["date_iso"])
        for it in items_sorted:
            d = date.fromisoformat(it["date_iso"])
            day_short = PT_BR_DAY[d.weekday()]
            lines.append(f"- **{day_short} {d.strftime('%d/%m')}** — {it['title']}")

    path = PLANO_DIR / f"plano-semana-{week_id}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main():
    p = argparse.ArgumentParser(description="Baixa scheduled workouts do calendario Garmin")
    p.add_argument("--weeks", type=int, default=2,
                   help="Quantas semanas a partir de hoje (default: 2 = atual + proxima)")
    p.add_argument("--backfill-months", type=int, default=0,
                   help="Quantos meses passados puxar tambem (default: 0). Util pra cruzar com TCX historicos.")
    p.add_argument("--db", default=str(DB_PATH))
    args = p.parse_args()

    today = date.today()
    monday_atual = today - timedelta(days=today.weekday())
    target_dates = []

    # Backfill historico (meses passados completos)
    for m_back in range(args.backfill_months, 0, -1):
        # Pega mes "m_back" meses atras, do dia 1 ao ultimo dia
        ref = today.replace(day=1)
        for _ in range(m_back):
            ref = (ref - timedelta(days=1)).replace(day=1)
        # Ate o ultimo dia do mes
        next_month = (ref.replace(day=28) + timedelta(days=4)).replace(day=1)
        last_day = (next_month - timedelta(days=1)).day
        for d in range(1, last_day + 1):
            target_dates.append(ref.replace(day=d))

    # Janela atual + futura
    for w in range(args.weeks):
        wstart = monday_atual + timedelta(weeks=w)
        for i in range(7):
            target_dates.append(wstart + timedelta(days=i))

    print(f"[+] Janela: {target_dates[0]} a {target_dates[-1]} ({args.weeks} semanas)")
    print(f"[+] Conectando ao Garmin Connect...")
    g = login_garmin()
    print(f"[+] Coletando scheduled workouts...")
    items = fetch_workouts(g, target_dates)

    if not items:
        print("[!] Nenhum treino agendado encontrado nessa janela.")
        return 0

    conn = sqlite3.connect(args.db)
    conn.execute(SCHEMA)
    upsert_all(conn, items)
    conn.close()
    print(f"[OK] {len(items)} treinos gravados em {args.db}")

    # MD por semana
    by_week = defaultdict(list)
    for it in items:
        by_week[it["week_id"]].append(it)
    for week_id, week_items in sorted(by_week.items()):
        path = write_week_md(week_id, week_items)
        print(f"[OK] {path}")

    # Terminal summary
    print("\n=== PLANO BAIXADO ===")
    for week_id in sorted(by_week.keys()):
        monday = _week_monday(week_id)
        sunday = monday + timedelta(days=6)
        print(f"\n## {week_id} ({monday.strftime('%d/%m')} a {sunday.strftime('%d/%m')})")
        for it in sorted(by_week[week_id], key=lambda i: i["date_iso"]):
            d = date.fromisoformat(it["date_iso"])
            print(f"  {PT_BR_DAY[d.weekday()]} {d.strftime('%d/%m')} — {it['title']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
