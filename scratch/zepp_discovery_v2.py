
import sys
import os
import json
import time
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), "src"))
from ingestion.zepp_api import ZeppAPI

def discovery_scan_v2():
    api = ZeppAPI()
    today_str = "2026-05-10"
    
    # Converte para timestamps em ms
    dt = datetime.strptime(today_str, "%Y-%m-%d")
    from_ts = str(int(dt.timestamp() * 1000))
    to_ts = str(int((dt.timestamp() + 86399) * 1000))
    
    print(f"🕵️‍♂️ Iniciando Discovery Scan V2 para {today_str} ({from_ts} -> {to_ts})...")
    
    # Tenta o endpoint de eventos com timestamps
    params = {
        "from": from_ts,
        "to": to_ts,
        "limit": "1000"
    }
    data = api.fetch_data(f"/users/{api.config['user_id']}/events", params)
    
    if data and "items" in data:
        print(f"\n✅ {len(data['items'])} eventos encontrados!")
        types = {}
        for item in data["items"]:
            etype = item.get("eventType")
            if etype not in types:
                types[etype] = item
        
        for etype, example in types.items():
            print(f"\n- {etype}:")
            print(f"  {json.dumps(example, indent=2)}")
    else:
        print("❌ Nenhum evento granular encontrado com timestamps.")

if __name__ == "__main__":
    discovery_scan_v2()
