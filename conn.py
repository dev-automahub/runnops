"""
Teste rapido de conexao com Garmin Connect.

Le credenciais de .env (NUNCA hardcode senha em codigo).
Mostra resumo do dia e atividades registradas hoje.
"""
from garminconnect import Garmin
from datetime import date
from dotenv import load_dotenv
import os
import sys

load_dotenv()
email = os.getenv("GARMIN_EMAIL")
senha = os.getenv("GARMIN_PASSWORD")

if not email or not senha:
    print("ERRO: configure GARMIN_EMAIL e GARMIN_PASSWORD no arquivo .env")
    print("Veja .env.example como modelo.")
    sys.exit(1)

try:
    client = Garmin(email, senha)
    client.login()

    hoje = date.today()
    stats = client.get_stats(hoje.isoformat())

    print(f"--- Dados de {hoje} ---")
    print(f"Passos totais: {stats.get('totalSteps', 'n/a')}")
    print(f"FC Repouso: {stats.get('restingHeartRate', 'n/a')} bpm")
    print(f"Stress medio: {stats.get('averageStressLevel', 'n/a')}")
    print(f"Body Battery min/max: {stats.get('bodyBatteryLowestValue', 'n/a')} / {stats.get('bodyBatteryHighestValue', 'n/a')}")

    atividades = client.get_activities_by_date(hoje.isoformat(), hoje.isoformat())
    if atividades:
        print("\nAtividades de hoje:")
        for atv in atividades:
            dist_km = atv.get('distance', 0) / 1000
            dur_min = atv.get('duration', 0) / 60
            print(f"  - {atv['activityName']} | {dist_km:.2f} km | {dur_min:.0f} min")
    else:
        print("\nNenhuma atividade registrada hoje.")

except Exception as e:
    print(f"Erro ao conectar ou coletar dados: {e}")
    sys.exit(1)
