import requests
import time
import json
import os
import sys
from datetime import datetime, timedelta

# Adiciona o diretório src ao path para importar a ZeppAPI
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.ingestion.zepp_api import ZeppAPI

print("\n--- Teste de Integração ZeppAPI ---")
api = ZeppAPI()

print("\n--- Teste 1: Dados Diários (Bio + Sono) ---")
ontem = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
resultado = api.normalize_for_daily(ontem)
if resultado:
    print(f"✅ Dados de {ontem}:")
    print(json.dumps(resultado, indent=2))

print("\n--- Teste 2: Histórico de Treinos (Maio 2026) ---")
treinos = api.get_workout_history("2026-05", "2026-05")
if treinos and "data" in treinos and "summary" in treinos["data"]:
    count = len(treinos["data"]["summary"])
    print(f"✅ Encontrados {count} treinos em Maio.")
    # Mostra o primeiro treino para validar
    if count > 0:
        t = treinos["data"]["summary"][0]
        print(f"Exemplo Treino: Tipo {t.get('type')}, Cal: {t.get('calorie')}, TE: {t.get('te')}")
else:
    print("❌ Falha ao buscar treinos.")

print("\n--- Teste 4: Estatísticas de Carreira ---")
stats = api.get_sport_stats()
if stats and "data" in stats:
    print(f"✅ Encontrados {len(stats['data'])} tipos de atividades acumuladas.")
    for s in stats["data"]:
        t_type = s.get("type")
        count = s.get("count")
        cal = s.get("calorie")
        print(f" - Tipo {t_type}: {count} treinos, {cal} kcal totais")
print("\n--- Teste 5: Informações de PAI (Últimos 7 dias) ---")
seven_days_ago_ts = str(int((datetime.now() - timedelta(days=7)).timestamp() * 1000))
pai = api.get_pai_info(seven_days_ago_ts)
if pai and "items" in pai and pai["items"]:
    ultimo_pai = pai["items"][-1]
    print(f"✅ PAI Total: {ultimo_pai.get('totalPai')}")
    print(f"✅ RHR via PAI: {ultimo_pai.get('restHr')} BPM")
else:
    print("❌ Falha ao buscar informações de PAI.")
