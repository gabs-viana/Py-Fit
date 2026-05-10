
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), "src"))
from ingestion.zepp_api import ZeppAPI

def discovery_scan():
    api = ZeppAPI()
    today = "2026-05-10"
    print(f"🕵️‍♂️ Iniciando Discovery Scan para {today}...")
    
    # Varre os eventos do dia
    data = api.debug_discovery(today)
    
    if data and "items" in data:
        print("\n📈 Tipos de eventos detectados:")
        # Agrupa e mostra um exemplo de cada
        types = {}
        for item in data["items"]:
            etype = item.get("eventType")
            if etype not in types:
                types[etype] = item
        
        for etype, example in types.items():
            print(f"- {etype}: {list(example.keys())}")
            # Se for HRV ou similar, mostramos o valor
            if "hrv" in etype.lower() or "readiness" in etype.lower() or "charge" in etype.lower():
                print(f"  🎯 Exemplo: {json.dumps(example, indent=2)}")
    else:
        print("❌ Nenhum evento granular encontrado.")

if __name__ == "__main__":
    discovery_scan()
