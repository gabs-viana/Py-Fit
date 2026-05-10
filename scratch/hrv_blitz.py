import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ingestion.zepp_api import ZeppAPI

def hrv_blitz(date_str):
    api = ZeppAPI()
    api.check_session()
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start_ts = int(time.mktime(dt.timetuple()) * 1000)
    end_ts = start_ts + 86399000
    
    types_to_test = ["Hrv", "vfc", "readiness", "night_hrv", "heart_rate_variability"]
    
    print(f"🚀 Iniciando Blitz de HRV para {date_str}...")
    
    for etype in types_to_test:
        print(f"🔍 Testando eventType: {etype}...")
        endpoint = "/v2/users/me/events"
        params = {
            "limit": 10,
            "eventType": etype,
            "from": start_ts,
            "to": end_ts
        }
        data = api.fetch_data(endpoint, params=params)
        if data and "items" in data and data["items"]:
            print(f"   ✅ ACHOU! {len(data['items'])} itens encontrados para {etype}")
            for item in data["items"]:
                print(f"   Subtype: {item.get('subType')} | Value: {item.get('value')}")
        else:
            print(f"   ❌ Nada para {etype}")

if __name__ == "__main__":
    hrv_blitz("2026-05-09") # Ontem
    print("-" * 30)
    hrv_blitz("2026-05-10") # Hoje
