import os
import sys
import json
from datetime import datetime, timedelta

# Ajuste de path para achar os módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from ingestion.zepp_api import ZeppAPI

def debug_sport_load_history():
    config_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "config", "zepp_config.json")
    api = ZeppAPI(config_path)
    
    end_date = "2026-05-12"
    # Tenta buscar os últimos 10 dias primeiro (em vez de 60) para ver se vem algo
    start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
    
    print(f"--- 📊 Investigando Histórico de SPORT_LOAD ({start_date} até {end_date}) ---")
    
    endpoint = f"/watch/users/{api.config['user_id']}/WatchSportStatistics/SPORT_LOAD"
    params = {
        "startDay": start_date,
        "endDay": end_date,
        "userid": api.config["user_id"]
    }
    data = api.fetch_data(endpoint, params)
    
    if data and "items" in data and data["items"]:
        print(f"✅ Sucesso! Encontrados {len(data['items'])} dias com carga.")
        for i in range(min(3, len(data['items']))):
            print(f"\n--- Item {i} ({data['items'][i].get('dayId')}) ---")
            print(json.dumps(data['items'][i], indent=2))
    else:
        print("❌ Nenhum dado histórico retornado para este intervalo.")
        print(f"Resposta bruta: {json.dumps(data, indent=2)}")

if __name__ == "__main__":
    debug_sport_load_history()
