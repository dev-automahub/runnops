"""
health_daily.py - Coleta diaria de metricas de saude do Garmin Connect.
Salva em SQLite (runtech.db) de forma idempotente (UPDATE se ja existe).

Uso:
    python health_daily.py                          # Hoje
    python health_daily.py 2026-05-06               # Data especifica
    python health_daily.py --backfill 7             # Ultimos 7 dias (incluindo hoje)
    python health_daily.py --backfill-from 2026-05-05  # De 05/05 ate hoje
    python health_daily.py --db custom.db           # Outro path do DB
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from garminconnect import Garmin


DB_PATH = Path("runtech.db")
SCHEMA = """
CREATE TABLE IF NOT EXISTS health_daily (
    date TEXT PRIMARY KEY,
    sleep_score INTEGER,
    sleep_duration_min INTEGER,
    sleep_rem_min INTEGER,
    sleep_deep_min INTEGER,
    sleep_light_min INTEGER,
    sleep_awake_min INTEGER,
    hrv_avg_overnight REAL,
    hrv_status TEXT,
    body_battery_max INTEGER,
    body_battery_min INTEGER,
    body_battery_charged INTEGER,
    body_battery_drained INTEGER,
    resting_heart_rate INTEGER,
    stress_avg INTEGER,
    stress_max INTEGER,
    training_readiness INTEGER,
    vo2_max REAL,
    weight_kg REAL,
    steps INTEGER,
    active_calories INTEGER,
    fetched_at TEXT,
    raw_json TEXT
);
"""


def init_db(path):
    conn = sqlite3.connect(str(path))
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def login_garmin():
    load_dotenv()
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        sys.exit("ERRO: configure GARMIN_EMAIL e GARMIN_PASSWORD em .env")
    g = Garmin(email, password)
    g.login()
    return g


def safe_get(d, *keys, default=None):
    """Pega chave aninhada de dict. Retorna default se algum nivel for None/missing."""
    cur = d
    for k in keys:
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return default
    return cur if cur is not None else default


def sec_to_min(s):
    if s is None:
        return None
    try:
        return int(s // 60)
    except (TypeError, ValueError):
        return None


def parse_body_battery(bb):
    """Retorna (max, min, charged, drained). Computa max/min do array se necessario."""
    if not bb:
        return None, None, None, None
    entry = bb[0] if isinstance(bb, list) and bb else (bb if isinstance(bb, dict) else None)
    if not entry:
        return None, None, None, None

    charged = entry.get("charged")
    drained = entry.get("drained")

    bb_max = entry.get("max") or entry.get("highestBodyBattery")
    bb_min = entry.get("min") or entry.get("lowestBodyBattery")

    if bb_max is None or bb_min is None:
        values = entry.get("bodyBatteryValuesArray") or []
        nums = [v[1] for v in values if isinstance(v, (list, tuple)) and len(v) > 1 and v[1] is not None]
        if nums:
            bb_max = bb_max if bb_max is not None else max(nums)
            bb_min = bb_min if bb_min is not None else min(nums)

    return bb_max, bb_min, charged, drained


def fetch_one_day(g, target_date):
    """Coleta tudo que conseguir pra uma data. Campos faltantes = None. Tudo bruto guardado em raw_json."""
    iso = target_date.isoformat()
    raw = {}

    def call(method_name, *args):
        try:
            method = getattr(g, method_name, None)
            if method is None:
                raw[method_name + "_error"] = "method not available"
                return None
            result = method(*args)
            raw[method_name] = result
            return result
        except Exception as e:
            raw[method_name + "_error"] = str(e)
            return None

    sleep = call("get_sleep_data", iso)
    hrv = call("get_hrv_data", iso)
    bb = call("get_body_battery", iso)
    summary = call("get_user_summary", iso)
    readiness = call("get_training_readiness", iso)
    vo2 = call("get_max_metrics", iso)
    body = call("get_body_composition", iso)

    sleep_dto = safe_get(sleep, "dailySleepDTO") or {}
    sleep_score = safe_get(sleep_dto, "sleepScores", "overall", "value")
    sleep_duration = sec_to_min(sleep_dto.get("sleepTimeSeconds"))
    sleep_deep = sec_to_min(sleep_dto.get("deepSleepSeconds"))
    sleep_light = sec_to_min(sleep_dto.get("lightSleepSeconds"))
    sleep_rem = sec_to_min(sleep_dto.get("remSleepSeconds"))
    sleep_awake = sec_to_min(sleep_dto.get("awakeSleepSeconds"))

    hrv_summary = safe_get(hrv, "hrvSummary") or {}
    hrv_avg = hrv_summary.get("lastNightAvg")
    hrv_status = hrv_summary.get("status")

    bb_max, bb_min, bb_charged, bb_drained = parse_body_battery(bb)

    rhr = safe_get(summary, "restingHeartRate")
    stress_avg = safe_get(summary, "averageStressLevel")
    stress_max = safe_get(summary, "maxStressLevel")
    steps = safe_get(summary, "totalSteps")
    calories = safe_get(summary, "activeKilocalories")

    readiness_score = None
    if readiness:
        if isinstance(readiness, list) and readiness:
            readiness_score = readiness[0].get("score")
        elif isinstance(readiness, dict):
            readiness_score = readiness.get("score")

    vo2_max_value = None
    if vo2:
        entry = vo2[0] if isinstance(vo2, list) and vo2 else (vo2 if isinstance(vo2, dict) else None)
        if entry:
            vo2_max_value = safe_get(entry, "generic", "vo2MaxValue") or entry.get("vo2MaxValue")

    weight = None
    if body:
        weight_g = safe_get(body, "totalAverage", "weight")
        if weight_g:
            try:
                weight = round(float(weight_g) / 1000, 2)
            except (TypeError, ValueError):
                weight = None

    return {
        "date": iso,
        "sleep_score": sleep_score,
        "sleep_duration_min": sleep_duration,
        "sleep_rem_min": sleep_rem,
        "sleep_deep_min": sleep_deep,
        "sleep_light_min": sleep_light,
        "sleep_awake_min": sleep_awake,
        "hrv_avg_overnight": hrv_avg,
        "hrv_status": hrv_status,
        "body_battery_max": bb_max,
        "body_battery_min": bb_min,
        "body_battery_charged": bb_charged,
        "body_battery_drained": bb_drained,
        "resting_heart_rate": rhr,
        "stress_avg": stress_avg,
        "stress_max": stress_max,
        "training_readiness": readiness_score,
        "vo2_max": vo2_max_value,
        "weight_kg": weight,
        "steps": steps,
        "active_calories": calories,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "raw_json": json.dumps(raw, default=str, ensure_ascii=False),
    }


def upsert(conn, row):
    keys = list(row.keys())
    placeholders = ",".join(["?"] * len(keys))
    cols = ",".join(keys)
    sets = ",".join([f"{k}=excluded.{k}" for k in keys if k != "date"])
    sql = f"INSERT INTO health_daily ({cols}) VALUES ({placeholders}) ON CONFLICT(date) DO UPDATE SET {sets};"
    conn.execute(sql, [row[k] for k in keys])
    conn.commit()


def fmt(val, unit=""):
    if val is None or val == "":
        return "-"
    return f"{val}{unit}"


def print_summary(row):
    d = row["date"]
    print(f"\n--- Saude de {d} ---")
    print(f"Sleep Score:       {fmt(row['sleep_score'])}")
    if row["sleep_duration_min"]:
        h = row["sleep_duration_min"] // 60
        m = row["sleep_duration_min"] % 60
        print(f"Sono total:        {h}h{m:02d}min  (REM {fmt(row['sleep_rem_min'])} / Deep {fmt(row['sleep_deep_min'])} / Light {fmt(row['sleep_light_min'])} / Awake {fmt(row['sleep_awake_min'])} min)")
    else:
        print("Sono total:        -")
    print(f"HRV overnight:     {fmt(row['hrv_avg_overnight'], ' ms')}  ({fmt(row['hrv_status'])})")
    bb_pair = f"{row['body_battery_max']} / {row['body_battery_min']}" if row['body_battery_max'] is not None else None
    bb_flow = f"+{row['body_battery_charged']} / -{row['body_battery_drained']}" if row['body_battery_charged'] is not None else None
    print(f"Body Battery max/min: {fmt(bb_pair)}   carga/desgaste: {fmt(bb_flow)}")
    print(f"FC repouso:        {fmt(row['resting_heart_rate'], ' bpm')}")
    stress_pair = f"{row['stress_avg']} / {row['stress_max']}" if row['stress_avg'] is not None else None
    print(f"Stress avg/max:    {fmt(stress_pair)}")
    print(f"Training Readiness: {fmt(row['training_readiness'], '/100')}")
    print(f"VO2 Max:           {fmt(row['vo2_max'])}")
    print(f"Peso:              {fmt(row['weight_kg'], ' kg')}")
    print(f"Passos:            {fmt(row['steps'])}")
    print(f"Calorias ativas:   {fmt(row['active_calories'], ' kcal')}")


def main():
    parser = argparse.ArgumentParser(description="Coleta saude diaria do Garmin -> SQLite")
    parser.add_argument("date", nargs="?", help="Data YYYY-MM-DD (default: hoje)")
    parser.add_argument("--backfill", type=int, metavar="N", help="Pega ultimos N dias (incluindo hoje)")
    parser.add_argument("--backfill-from", help="Data inicial YYYY-MM-DD ate hoje")
    parser.add_argument("--db", default=str(DB_PATH), help="Path do SQLite (default: runtech.db)")
    parser.add_argument("--quiet", action="store_true", help="Suprime output detalhado")
    parser.add_argument("--no-publish", action="store_true", help="Nao publicar no GitHub/Cloudflare apos gerar dash")
    args = parser.parse_args()

    today = date.today()

    if args.backfill:
        dates = [today - timedelta(days=i) for i in range(args.backfill - 1, -1, -1)]
    elif args.backfill_from:
        try:
            start = date.fromisoformat(args.backfill_from)
        except ValueError:
            sys.exit("ERRO: --backfill-from precisa ser YYYY-MM-DD")
        days = (today - start).days
        if days < 0:
            sys.exit("ERRO: data inicial e futura")
        dates = [start + timedelta(days=i) for i in range(days + 1)]
    elif args.date:
        try:
            dates = [date.fromisoformat(args.date)]
        except ValueError:
            sys.exit("ERRO: data precisa ser YYYY-MM-DD")
    else:
        dates = [today]

    print(f"Conectando ao Garmin Connect...")
    g = login_garmin()
    print(f"OK. Coletando {len(dates)} dia(s).")

    db = init_db(Path(args.db))
    success_count = 0
    error_count = 0

    for i, d in enumerate(dates):
        print(f"\n>> {d.isoformat()} ({i+1}/{len(dates)})")
        try:
            row = fetch_one_day(g, d)
            upsert(db, row)
            if not args.quiet:
                print_summary(row)
            success_count += 1
        except Exception as e:
            print(f"  ERRO: {e}")
            error_count += 1
        if i < len(dates) - 1:
            time.sleep(1.5)

    db.close()
    print(f"\n[OK] Gravado em {args.db}")
    print(f"     Sucesso: {success_count}/{len(dates)}  Erros: {error_count}")

    # Hook: gera dash + publica automaticamente apos run default (hoje, sem backfill)
    if (
        not args.backfill
        and not args.backfill_from
        and not args.date
        and not args.quiet
        and success_count > 0
    ):
        import os
        import subprocess
        here = Path(__file__).parent
        # Env com unbuffered output pros subprocesses Python — saida fica sequencial
        sub_env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}

        dash_script = here / "dash_today.py"
        dash_ok = False
        if dash_script.exists():
            try:
                print(f"\n[+] Gerando dashboard...", flush=True)
                r = subprocess.run([sys.executable, "-u", str(dash_script)], check=False, env=sub_env)
                dash_ok = (r.returncode == 0)
            except Exception as e:
                print(f"     (dash skipped: {e})", flush=True)

        # Publica no GitHub/Cloudflare se dash gerou OK e usuario nao pediu --no-publish
        if dash_ok and not args.no_publish:
            publish_script = here / "publish.py"
            if publish_script.exists():
                try:
                    print(f"\n[+] Publicando no GitHub/Cloudflare...", flush=True)
                    subprocess.run([sys.executable, "-u", str(publish_script)], check=False, env=sub_env)
                except Exception as e:
                    print(f"     (publish skipped: {e})", flush=True)


if __name__ == "__main__":
    main()
