"""
Baixador de atividades do Garmin Connect.

Le credenciais de .env (NUNCA hardcode senha em codigo).
Salva TCXs em 'Atividades Baixadas/' e atualiza 'lastrun_log.txt'.
Pula arquivos ja existentes (idempotente).

Uso:
    python lastrun.py            # baixa as 10 ultimas
    python lastrun.py 5          # baixa as 5 ultimas
    python lastrun.py 20         # baixa as 20 ultimas
"""
from garminconnect import Garmin
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import os
import re
import sys

DEFAULT_QTD = 10
PASTA_DESTINO = Path("Atividades Baixadas")
LOG_FILE = Path("lastrun_log.txt")

load_dotenv()
email = os.getenv("GARMIN_EMAIL")
senha = os.getenv("GARMIN_PASSWORD")

if not email or not senha:
    print("ERRO: configure GARMIN_EMAIL e GARMIN_PASSWORD no arquivo .env")
    sys.exit(1)

if len(sys.argv) > 1:
    try:
        qtd_solicitada = int(sys.argv[1])
        if qtd_solicitada <= 0:
            raise ValueError("quantidade deve ser positiva")
    except ValueError:
        print(f"ERRO: argumento invalido '{sys.argv[1]}'. Esperado: numero inteiro positivo.")
        sys.exit(1)
else:
    qtd_solicitada = DEFAULT_QTD

print("--- Baixador de Treinos do Garmin ---")
print(f"Buscando as {qtd_solicitada} ultimas atividades...\n")

PASTA_DESTINO.mkdir(exist_ok=True)

try:
    client = Garmin(email, senha)
    client.login()
    print("Login OK.\n")

    atividades = client.get_activities(0, qtd_solicitada)

    if not atividades:
        print("Nenhuma atividade encontrada.")
        sys.exit(0)

    count_baixados = 0
    count_pulados_existentes = 0
    count_pulados_nao_corrida = 0

    for atv in atividades:
        tipo = atv['activityType']['typeKey']
        nome = atv['activityName']
        id_atividade = atv['activityId']

        if tipo != 'running':
            count_pulados_nao_corrida += 1
            continue

        nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
        nome_arquivo = f"{id_atividade}_{nome_limpo}.tcx"
        caminho_arquivo = PASTA_DESTINO / nome_arquivo

        if caminho_arquivo.exists():
            print(f"[skip] {nome_arquivo} (ja existe)")
            count_pulados_existentes += 1
            continue

        print(f"[ok]   {nome} (ID {id_atividade})")
        data = client.download_activity(id_atividade, dl_fmt=client.ActivityDownloadFormat.TCX)
        caminho_arquivo.write_bytes(data)

        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        linha_log = f"{data_hora} - {nome} (ID: {id_atividade}) - Arquivo: {nome_arquivo}\n"
        with LOG_FILE.open("a", encoding="utf-8") as log_file:
            log_file.write(linha_log)

        count_baixados += 1

    print()
    print("Resumo:")
    print(f"  Baixados      : {count_baixados}")
    print(f"  Ja existiam   : {count_pulados_existentes}")
    print(f"  Nao-corridas  : {count_pulados_nao_corrida}")

except Exception as e:
    print(f"Erro: {e}")
    sys.exit(1)
