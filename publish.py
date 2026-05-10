"""publish.py - Commit + push automatico do dashboard pra Cloudflare Pages.

Fluxo tipico de manha:
    python health_daily.py    # coleta + gera index.html + atualiza diario
    python publish.py         # publica no site (https://runnops.pages.dev)

Ou em sequencia:
    python health_daily.py && python publish.py

Comportamento:
- Se nada mudou → exit 0 com mensagem "nada a publicar"
- Se mudou → git add . + commit + push (mensagem auto-gerada)
- Erros sao reportados em stderr com exit code 1
"""
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run(cmd, capture=True):
    """Roda comando shell. Retorna (stdout, stderr, returncode)."""
    result = subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        capture_output=capture,
        text=True,
        encoding="utf-8",
    )
    return result.stdout or "", result.stderr or "", result.returncode


def is_git_repo():
    """Verifica se estamos num repo git."""
    _, _, code = run(["git", "rev-parse", "--git-dir"])
    return code == 0


def has_remote():
    """Verifica se ha remote configurado."""
    out, _, _ = run(["git", "remote"])
    return bool(out.strip())


def what_changed():
    """Retorna lista de arquivos modificados (relativo ao repo)."""
    out, _, code = run(["git", "status", "--porcelain"])
    if code != 0:
        return []
    return [line[3:].strip() for line in out.splitlines() if line.strip()]


def build_commit_message(changes):
    """Monta mensagem de commit baseada no que mudou."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    has_index = any("index.html" in c for c in changes)
    has_diary = any("/diario/" in c for c in changes)
    has_glossary = any("dash_glossary.py" in c for c in changes)
    has_template = any(c in changes for c in ["dash_template.html", "dash_styles.css"])
    has_activity = any(("activity.html" in c) or ("activities.json" in c) for c in changes)
    has_tcx = any("Atividades Baixadas/" in c for c in changes)
    has_code = any(c.endswith(".py") and "dash_glossary" not in c for c in changes)

    parts = []
    if has_diary:
        parts.append("diario")
    if has_index:
        parts.append("dash")
    if has_glossary:
        parts.append("glossario")
    if has_template:
        parts.append("template/css")
    if has_activity:
        parts.append("atividades")
    if has_tcx:
        parts.append("tcx")
    if has_code:
        parts.append("codigo")

    if parts:
        scope = ", ".join(parts)
        return f"auto: publish {scope} ({now})"
    return f"auto: publish ({now})"


def main():
    p = argparse.ArgumentParser(
        description="Commit + push automatico do dashboard pra Cloudflare Pages."
    )
    p.add_argument("--message", "-m", help="Mensagem de commit customizada (override)")
    p.add_argument("--dry-run", action="store_true", help="Mostra o que faria, sem executar")
    p.add_argument("--no-push", action="store_true", help="So commita, nao da push")
    args = p.parse_args()

    # Sanity checks
    if not is_git_repo():
        print("ERRO: nao e um repositorio git. Rode 'git init' primeiro.", file=sys.stderr)
        return 1

    if not has_remote() and not args.no_push:
        print("ERRO: sem remote configurado. Rode 'git remote add origin <url>'.", file=sys.stderr)
        return 1

    if not Path("index.html").exists():
        print("AVISO: index.html nao existe. Rode 'python dash_today.py' primeiro.", file=sys.stderr)
        # Nao aborta — pode haver outros arquivos pra commitar (ex: codigo)

    # Ver o que mudou
    changes = what_changed()
    if not changes:
        print("[OK] Nada a publicar — repo limpo.")
        return 0

    print(f"[+] {len(changes)} arquivo(s) modificado(s):")
    for c in changes[:10]:
        print(f"     {c}")
    if len(changes) > 10:
        print(f"     ... +{len(changes) - 10} mais")

    # Mensagem
    msg = args.message or build_commit_message(changes)
    print(f"[+] Mensagem: {msg}")

    if args.dry_run:
        print("\n[DRY-RUN] Comandos que seriam executados:")
        print(f"     git add .")
        print(f"     git commit -m \"{msg}\"")
        if not args.no_push:
            print(f"     git push")
        return 0

    # Add
    _, err, code = run(["git", "add", "."])
    if code != 0:
        print(f"ERRO no git add: {err}", file=sys.stderr)
        return 1

    # Commit
    _, err, code = run(["git", "commit", "-m", msg])
    if code != 0:
        print(f"ERRO no git commit: {err}", file=sys.stderr)
        return 1
    print("[OK] Commit feito.")

    # Push
    if args.no_push:
        print("[OK] --no-push ativo. Pra publicar depois: git push")
        return 0

    out, err, code = run(["git", "push"])
    if code != 0:
        print(f"ERRO no git push: {err}", file=sys.stderr)
        print("     Commit local foi feito. Tente 'git push' manualmente.", file=sys.stderr)
        return 1

    print("[OK] Push feito. Cloudflare republica em ~30s.")
    print(f"     https://runnops.pages.dev")
    return 0


if __name__ == "__main__":
    sys.exit(main())
