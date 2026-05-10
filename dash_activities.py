"""
Gera activities.json com lista de atividades disponiveis em 'Atividades Baixadas/'.
Le metadados de cada TCX (data, distancia, duracao) sem parsear trackpoints todos.
Saida: activities.json na raiz do projeto, consumida por activity.html.
"""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime

PASTA_TCX = Path("Atividades Baixadas")
OUTPUT = Path("activities.json")

NS = {
    'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
}


def _parse_filename(fname: str) -> dict:
    m = re.match(r'^(\d+)_(.+)\.tcx$', fname)
    if not m:
        return {"id": fname, "name": fname}
    return {"id": m.group(1), "name": m.group(2)}


def _read_metadata(tcx_path: Path) -> dict | None:
    try:
        tree = ET.parse(tcx_path)
        root = tree.getroot()
        act = root.find('.//tcx:Activity', NS)
        if act is None:
            return None

        id_node = act.find('tcx:Id', NS)
        start_iso = id_node.text if id_node is not None else None

        total_dist = 0.0
        total_time = 0.0
        for lap in act.findall('tcx:Lap', NS):
            d = lap.find('tcx:DistanceMeters', NS)
            t = lap.find('tcx:TotalTimeSeconds', NS)
            if d is not None and d.text:
                total_dist += float(d.text)
            if t is not None and t.text:
                total_time += float(t.text)

        sport = act.get('Sport', 'Running')

        return {
            "start_iso": start_iso,
            "distance_m": total_dist,
            "duration_s": total_time,
            "sport": sport,
        }
    except Exception as e:
        print(f"[!] Falha ao ler {tcx_path.name}: {e}")
        return None


def _date_br(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        clean = iso.replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso[:10]


def build_manifest(pasta: Path = PASTA_TCX) -> list[dict]:
    if not pasta.exists():
        print(f"[!] Pasta '{pasta}' nao existe.")
        return []

    items = []
    for tcx in sorted(pasta.glob("*.tcx")):
        meta = _read_metadata(tcx)
        if not meta:
            continue
        finfo = _parse_filename(tcx.name)
        km = meta["distance_m"] / 1000
        mins = meta["duration_s"] / 60
        items.append({
            "id": finfo["id"],
            "name": finfo["name"],
            "filename": str(tcx).replace('\\', '/'),
            "date_iso": meta["start_iso"],
            "date_br": _date_br(meta["start_iso"]),
            "distance_km": round(km, 2),
            "duration_min": round(mins, 1),
            "sport": meta["sport"],
        })

    items.sort(key=lambda x: x["date_iso"] or "", reverse=True)
    return items


def main():
    items = build_manifest()
    payload = {
        "generated_at": datetime.now().isoformat(timespec='seconds'),
        "count": len(items),
        "activities": items,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] {OUTPUT} gerado com {len(items)} atividades.")


if __name__ == "__main__":
    main()
