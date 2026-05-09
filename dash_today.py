"""dash_today.py — gera dash.html a partir de runtech.db e abre no browser.

Uso:
    python dash_today.py                                    # default
    python dash_today.py --no-open                          # nao abre browser
    python dash_today.py --verdict "LR7 reservado" --color amber
    python dash_today.py --archive                          # salva snapshot dash-YYYY-MM-DD.html
    python dash_today.py --db custom.db
    python dash_today.py --no-journal                       # nao escreve no diario MD
"""
import argparse
import sys
from datetime import date
from pathlib import Path

from dash_data import load_history, enrich_with_verdicts, compute_deltas
from dash_render import build_context, render_html, write_and_open, render_empty_state
from dash_journal import update_journal


DEFAULT_DIARIO_DIR = "2026-05-04-protocolo-recuperacao-corrida-rua-amador/diario"


def main():
    p = argparse.ArgumentParser(description="Gera dash.html dos dados de saude diarios")
    p.add_argument("--db", default="runtech.db", help="Path do SQLite")
    p.add_argument("--output", default="index.html", help="Path do HTML de saida (default: index.html — entry pra Cloudflare Pages)")
    p.add_argument("--no-open", action="store_true", help="Nao abrir no browser apos gerar")
    p.add_argument("--archive", action="store_true", help="Tambem salvar em dash_archive/")
    p.add_argument("--verdict", help="Override headline do veredito")
    p.add_argument("--color", choices=["green", "amber", "orange", "red"], help="Override cor do veredito")
    p.add_argument("--subtitle", help="Override sub-mensagem do veredito")
    p.add_argument("--diario-dir", default=DEFAULT_DIARIO_DIR, help="Path da pasta de diarios MD")
    p.add_argument("--no-journal", action="store_true", help="Nao escrever/atualizar diario MD")
    args = p.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERRO: DB nao encontrado em {db_path}.", file=sys.stderr)
        print(f"      Rode 'python health_daily.py' primeiro pra criar.", file=sys.stderr)
        return 1

    try:
        rows = load_history(str(db_path), days=30)
    except FileNotFoundError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1

    if not rows:
        # DB vazio
        html = render_empty_state()
        write_and_open(html, output_path=args.output, archive=False, open_browser=not args.no_open)
        print(f"[OK] {args.output} (empty state)")
        return 0

    enriched = enrich_with_verdicts(rows)
    today_iso = date.today().isoformat()
    today_row = enriched[0]
    is_stale = today_row["date"] != today_iso
    prev_row = enriched[1] if len(enriched) > 1 else None
    deltas = compute_deltas(today_row, prev_row) if prev_row else {}

    override = None
    if args.verdict:
        override = {
            "headline": args.verdict,
            "color": args.color or "amber",
            "subtitle": args.subtitle or "",
        }

    diario_dir = None if args.no_journal else args.diario_dir

    # Atualiza/cria diario MD com reportagem matinal auto-gerada (antes do dashboard)
    if diario_dir:
        try:
            j_path, j_action = update_journal(
                diario_dir,
                today_row,
                prev_row=prev_row,
                verdict=enriched[0]["verdict"],
            )
            if j_action == "created":
                print(f"[+] Diario criado: {j_path}")
            elif j_action == "updated":
                print(f"[+] Diario atualizado: {j_path}")
        except Exception as e:
            print(f"     (diario skipped: {e})")

    ctx = build_context(today_row, enriched, deltas, override=override, diario_dir=diario_dir)
    ctx["is_stale"] = is_stale

    html = render_html(ctx)
    out_path = write_and_open(
        html,
        output_path=args.output,
        archive=args.archive,
        open_browser=not args.no_open,
    )
    print(f"[OK] {out_path} gerado.")
    if is_stale:
        print(f"     Aviso: ultimo dado e de {today_row['date']} (nao de hoje).")
    if args.archive:
        print(f"     Snapshot tambem em dash_archive/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
