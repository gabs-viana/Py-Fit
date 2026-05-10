import sys
import os
import time
from datetime import datetime

# Adiciona a raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.zepp_api import ZeppAPI

def discover_events(date_str):
    api = ZeppAPI()
    api.check_session()
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start_ts = int(time.mktime(dt.timetuple()) * 1000)
    end_ts = start_ts + 86399000
    
    print(f"🔍 Vasculhando TODOS os eventos para {date_str}...")
    
    endpoint = "/v2/users/me/events"
    params = {
        "limit": 200,
        "from": start_ts,
        "to": end_ts,
        "reverse": "true"
    }
    
    data = api.fetch_data(endpoint, params=params)
    if not data or "items" not in data:
        print("❌ Nenhum evento encontrado.")
        return

    items = data["items"]
    print(f"✅ Encontrados {len(items)} eventos.")
    
    event_types = {}
    for item in items:
        etype = item.get("eventType")
        stype = item.get("subType")
        key = f"{etype} | {stype}"
        if key not in event_types:
            event_types[key] = item
            
    print("\n📋 Tipos de eventos detectados:")
    for key, example in event_types.items():
        print(f"🔹 {key}")
        # Se parecer suspeito, mostra o valor
        if any(s in key.lower() for s in ["hrv", "vfc", "stress", "readiness", "heart", "blood"]):
            print(f"   ↳ Amostra: {example.get('value')}")

if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else "2026-05-10"
    discover_events(date)
