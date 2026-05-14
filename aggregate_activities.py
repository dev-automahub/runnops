"""
aggregate_activities.py - Le todos TCX em 'Atividades Baixadas/' e gera:
  - session_summary (1 linha por treino, com matching opcional para scheduled_workout)
  - weekly_summary  (1 linha por semana ISO)
em runtech.db. Idempotente: reprocessa tudo sempre.

Uso:
    python aggregate_activities.py
    python aggregate_activities.py --db custom.db
"""
import argparse
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PASTA_TCX = Path("Atividades Baixadas")
DB_PATH = Path("runtech.db")

NS = {
    'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
    'ns3': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2',
}

# Karvonen zones — usuario: FCmax=170, FCrep=51, HRR=119
FC_MAX = 170
FC_REP = 51
HRR = FC_MAX - FC_REP
ZONE_BOUNDS = [
    int(FC_REP + 0.50 * HRR),  # Z1: 110
    int(FC_REP + 0.60 * HRR),  # Z1/Z2: 122
    int(FC_REP + 0.70 * HRR),  # Z2/Z3: 134
    int(FC_REP + 0.80 * HRR),  # Z3/Z4: 146
    int(FC_REP + 0.90 * HRR),  # Z4/Z5: 158
]


SCHEMA_SESSION = """
CREATE TABLE IF NOT EXISTS session_summary (
    session_id TEXT PRIMARY KEY,
    filename TEXT,
    date_iso TEXT,
    week_id TEXT,
    sport TEXT,
    distance_km REAL,
    duration_min REAL,
    avg_hr INTEGER,
    max_hr INTEGER,
    avg_cadence_spm REAL,
    avg_pace_sec_per_km REAL,
    time_z1_sec INTEGER,
    time_z2_sec INTEGER,
    time_z3_sec INTEGER,
    time_z4_sec INTEGER,
    time_z5_sec INTEGER,
    scheduled_id INTEGER,
    workout_code TEXT
);
"""

# Colunas adicionadas em 12/05/2026 — migração idempotente pra DBs existentes
NEW_SESSION_COLUMNS = [
    ("scheduled_id", "INTEGER"),
    ("workout_code", "TEXT"),
]

SCHEMA_WEEK = """
CREATE TABLE IF NOT EXISTS weekly_summary (
    week_id TEXT PRIMARY KEY,
    week_start_iso TEXT,
    sessions_count INTEGER,
    total_distance_km REAL,
    total_duration_min REAL,
    avg_hr INTEGER,
    avg_cadence_spm REAL,
    avg_pace_sec_per_km REAL,
    time_z1_sec INTEGER,
    time_z2_sec INTEGER,
    time_z3_sec INTEGER,
    time_z4_sec INTEGER,
    time_z5_sec INTEGER,
    pct_z2 REAL,
    longest_session_km REAL,
    longest_session_id TEXT
);
"""


def extract_workout_code(title):
    """Extrai prefixo tipo LR7, FFR4, RRe5, HRR4, RHR6, RF5, AEM do titulo.

    Lida com:
      - prefixos numericos de filename ("12345_...")
      - "Vitória - LR7 ..." / "Vitória LR7 ..." / "Vitória Corrida RHR6 ..."
      - prefixos como "VO2 Máx." (treinos sem code tradicional, retorna None)
    """
    if not title:
        return None
    cleaned = title.strip()
    # Remove prefixo numerico de filename: "22853346305_..."
    cleaned = re.sub(r'^\d+_', '', cleaned)
    # Remove "Vitória" (com e sem hífen)
    cleaned = re.sub(r'^\s*Vit[óôo]ria\s*[-]?\s*', '', cleaned, flags=re.IGNORECASE)
    # Alguns TCX tem "Corrida XXX Corrida" — strip o "Corrida " inicial se houver
    cleaned = re.sub(r'^Corrida\s+', '', cleaned)
    # Match prefixo de letras + opcional letra minuscula + opcional digitos
    m = re.match(r'([A-Z]{1,5}[a-z]?\d{0,3})\b', cleaned)
    if m:
        code = m.group(1)
        if len(code) >= 2 or any(c.isdigit() for c in code):
            return code
    return None


def match_session_to_scheduled(conn, session_rows):
    """Para cada session, encontra o scheduled_workout mais provavel (mesma data + workout code).
    Atualiza session_summary.scheduled_id e workout_code in-place.
    Retorna (matched_count, total).
    """
    # Carrega todos scheduled (idempotente: nao filtra por data)
    try:
        cur = conn.execute("SELECT scheduled_id, date_iso, title FROM scheduled_workout")
        scheduled_by_date = defaultdict(list)
        for sid, d_iso, title in cur.fetchall():
            scheduled_by_date[d_iso].append({
                "scheduled_id": sid,
                "title": title,
                "code": extract_workout_code(title),
            })
    except sqlite3.OperationalError:
        # Tabela nao existe ainda — nada pra matchar
        return 0, len(session_rows)

    matched = 0
    for s in session_rows:
        date_short = (s["date_iso"] or "")[:10]
        s_code = extract_workout_code(Path(s["filename"]).stem)
        candidates = scheduled_by_date.get(date_short, [])

        chosen = None
        if len(candidates) == 1:
            chosen = candidates[0]
        elif len(candidates) > 1:
            # multiplos treinos no mesmo dia — match por code
            for c in candidates:
                if c["code"] and s_code and c["code"] == s_code:
                    chosen = c
                    break
            # fallback: primeiro candidato (raro)
            if not chosen:
                chosen = candidates[0]

        sched_id = chosen["scheduled_id"] if chosen else None
        conn.execute(
            "UPDATE session_summary SET scheduled_id=?, workout_code=? WHERE session_id=?",
            (sched_id, s_code, s["session_id"]),
        )
        if sched_id:
            matched += 1

    conn.commit()
    return matched, len(session_rows)


def _zone_idx(hr):
    """Retorna 1-5 baseado em Karvonen."""
    if hr is None:
        return None
    if hr < ZONE_BOUNDS[0]:
        return 1
    if hr < ZONE_BOUNDS[1]:
        return 1
    if hr < ZONE_BOUNDS[2]:
        return 2
    if hr < ZONE_BOUNDS[3]:
        return 3
    if hr < ZONE_BOUNDS[4]:
        return 4
    return 5


def _parse_tcx(path):
    """Parse 1 TCX. Retorna dict ou None."""
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return None

    root = tree.getroot()
    act = root.find('.//tcx:Activity', NS)
    if act is None:
        return None

    sport = act.get('Sport', 'Running')
    id_node = act.find('tcx:Id', NS)
    date_iso = id_node.text if id_node is not None else None

    total_dist_m = 0.0
    total_time_s = 0.0
    hr_values = []
    cadence_values_spm = []
    zone_time_sec = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    last_time = None

    for lap in act.findall('tcx:Lap', NS):
        d = lap.find('tcx:DistanceMeters', NS)
        t = lap.find('tcx:TotalTimeSeconds', NS)
        if d is not None and d.text:
            total_dist_m += float(d.text)
        if t is not None and t.text:
            total_time_s += float(t.text)

        for tp in lap.findall('.//tcx:Trackpoint', NS):
            time_node = tp.find('tcx:Time', NS)
            cur_time = None
            if time_node is not None and time_node.text:
                try:
                    cur_time = datetime.fromisoformat(time_node.text.replace('Z', '+00:00'))
                except ValueError:
                    cur_time = None

            hr_node = tp.find('tcx:HeartRateBpm/tcx:Value', NS)
            hr = int(hr_node.text) if hr_node is not None and hr_node.text else None

            # Cadencia: ambos Cadence e RunCadence vem em strides/min — x2 pra spm
            run_cad = tp.find('.//ns3:RunCadence', NS)
            cad_node = tp.find('tcx:Cadence', NS)
            cad_spm = None
            if run_cad is not None and run_cad.text:
                cad_spm = float(run_cad.text) * 2
            elif cad_node is not None and cad_node.text:
                cad_spm = float(cad_node.text) * 2

            if hr is not None:
                hr_values.append(hr)
            if cad_spm is not None and cad_spm > 0:
                cadence_values_spm.append(cad_spm)

            # Zone time: usa delta entre trackpoints
            if cur_time is not None and last_time is not None and hr is not None:
                dt = (cur_time - last_time).total_seconds()
                if 0 < dt < 30:  # ignora gaps >30s (pausas)
                    z = _zone_idx(hr)
                    if z is not None:
                        zone_time_sec[z] += dt
            last_time = cur_time

    if total_dist_m == 0 or total_time_s == 0:
        return None

    distance_km = total_dist_m / 1000
    duration_min = total_time_s / 60
    avg_pace_sec = total_time_s / distance_km if distance_km else None
    avg_hr = round(sum(hr_values) / len(hr_values)) if hr_values else None
    max_hr = max(hr_values) if hr_values else None
    avg_cad = round(sum(cadence_values_spm) / len(cadence_values_spm), 1) if cadence_values_spm else None

    # Week ID ISO (YYYY-Www)
    dt_obj = None
    if date_iso:
        try:
            dt_obj = datetime.fromisoformat(date_iso.replace('Z', '+00:00'))
        except ValueError:
            pass
    week_id = None
    if dt_obj:
        iso = dt_obj.isocalendar()
        week_id = f"{iso[0]}-W{iso[1]:02d}"

    return {
        "filename": str(path).replace('\\', '/'),
        "session_id": path.stem.split('_')[0] if '_' in path.stem else path.stem,
        "date_iso": date_iso,
        "week_id": week_id,
        "sport": sport,
        "distance_km": round(distance_km, 2),
        "duration_min": round(duration_min, 1),
        "avg_hr": avg_hr,
        "max_hr": max_hr,
        "avg_cadence_spm": avg_cad,
        "avg_pace_sec_per_km": round(avg_pace_sec, 1) if avg_pace_sec else None,
        "time_z1_sec": int(zone_time_sec[1]),
        "time_z2_sec": int(zone_time_sec[2]),
        "time_z3_sec": int(zone_time_sec[3]),
        "time_z4_sec": int(zone_time_sec[4]),
        "time_z5_sec": int(zone_time_sec[5]),
    }


def _week_monday_iso(week_id):
    """'2026-W19' -> '2026-05-04' (segunda da semana ISO)."""
    if not week_id:
        return None
    try:
        year, week = week_id.split("-W")
        d = datetime.strptime(f"{year}-{int(week)}-1", "%G-%V-%u")
        return d.date().isoformat()
    except ValueError:
        return None


def _aggregate_weeks(sessions):
    """Agrega lista de sessions em weekly_summary rows."""
    by_week = defaultdict(list)
    for s in sessions:
        if s["week_id"]:
            by_week[s["week_id"]].append(s)

    rows = []
    for week_id, sess in by_week.items():
        total_dist = sum(s["distance_km"] for s in sess)
        total_time_min = sum(s["duration_min"] for s in sess)
        total_time_sec = total_time_min * 60

        # Avg ponderado por duracao
        hr_weighted = sum((s["avg_hr"] or 0) * s["duration_min"] for s in sess if s["avg_hr"])
        hr_weight_sum = sum(s["duration_min"] for s in sess if s["avg_hr"])
        avg_hr = round(hr_weighted / hr_weight_sum) if hr_weight_sum else None

        cad_weighted = sum((s["avg_cadence_spm"] or 0) * s["duration_min"] for s in sess if s["avg_cadence_spm"])
        cad_weight_sum = sum(s["duration_min"] for s in sess if s["avg_cadence_spm"])
        avg_cad = round(cad_weighted / cad_weight_sum, 1) if cad_weight_sum else None

        avg_pace = round(total_time_sec / total_dist, 1) if total_dist else None

        z = {f"time_z{i}_sec": sum(s[f"time_z{i}_sec"] for s in sess) for i in range(1, 6)}
        total_zone_time = sum(z.values())
        pct_z2 = round(z["time_z2_sec"] / total_zone_time * 100, 1) if total_zone_time else 0.0

        longest = max(sess, key=lambda s: s["distance_km"])

        rows.append({
            "week_id": week_id,
            "week_start_iso": _week_monday_iso(week_id),
            "sessions_count": len(sess),
            "total_distance_km": round(total_dist, 2),
            "total_duration_min": round(total_time_min, 1),
            "avg_hr": avg_hr,
            "avg_cadence_spm": avg_cad,
            "avg_pace_sec_per_km": avg_pace,
            **z,
            "pct_z2": pct_z2,
            "longest_session_km": longest["distance_km"],
            "longest_session_id": longest["session_id"],
        })
    rows.sort(key=lambda r: r["week_id"])
    return rows


def _upsert(conn, table, row):
    keys = list(row.keys())
    placeholders = ",".join(["?"] * len(keys))
    cols = ",".join(keys)
    pk = "session_id" if table == "session_summary" else "week_id"
    sets = ",".join(f"{k}=excluded.{k}" for k in keys if k != pk)
    conn.execute(
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) "
        f"ON CONFLICT({pk}) DO UPDATE SET {sets}",
        [row[k] for k in keys],
    )


def main():
    p = argparse.ArgumentParser(description="Agrega TCX em session_summary + weekly_summary")
    p.add_argument("--db", default=str(DB_PATH))
    p.add_argument("--pasta", default=str(PASTA_TCX))
    args = p.parse_args()

    pasta = Path(args.pasta)
    if not pasta.exists():
        print(f"[!] Pasta '{pasta}' nao existe.", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    conn.execute(SCHEMA_SESSION)
    conn.execute(SCHEMA_WEEK)
    # Migracao idempotente pra DBs antigos
    existing = {row[1] for row in conn.execute("PRAGMA table_info(session_summary)").fetchall()}
    for col, coltype in NEW_SESSION_COLUMNS:
        if col not in existing:
            conn.execute(f"ALTER TABLE session_summary ADD COLUMN {col} {coltype}")
    conn.commit()

    tcx_files = sorted(pasta.glob("*.tcx"))
    print(f"[+] Parseando {len(tcx_files)} TCX...")
    sessions = []
    for tcx in tcx_files:
        s = _parse_tcx(tcx)
        if s:
            sessions.append(s)
            _upsert(conn, "session_summary", s)

    print(f"[+] {len(sessions)} sessoes parseadas. Agregando semanas...")
    weeks = _aggregate_weeks(sessions)
    for w in weeks:
        _upsert(conn, "weekly_summary", w)

    conn.commit()

    # Matching session <-> scheduled (planejado vs executado)
    matched, total = match_session_to_scheduled(conn, sessions)
    print(f"[+] Matching planejado-vs-executado: {matched}/{total} sessoes vinculadas a scheduled_workout")

    conn.close()

    print(f"[OK] {len(sessions)} sessoes + {len(weeks)} semanas gravadas em {args.db}")

    # Resumo terminal
    print("\n=== RESUMO POR SEMANA ===")
    print(f"{'Semana':<10} {'#Treinos':>10} {'Vol (km)':>10} {'Cad (spm)':>11} {'%Z2':>7} {'Pace':>10} {'Maior':>9}")
    for w in weeks[-8:]:
        pace_str = f"{int((w['avg_pace_sec_per_km'] or 0)//60)}:{int((w['avg_pace_sec_per_km'] or 0) % 60):02d}/km" if w['avg_pace_sec_per_km'] else "—"
        print(
            f"{w['week_id']:<10} {w['sessions_count']:>10} {w['total_distance_km']:>10.1f} "
            f"{(w['avg_cadence_spm'] or 0):>11.1f} {w['pct_z2']:>6.1f}% {pace_str:>10} "
            f"{w['longest_session_km']:>8.1f}km"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
