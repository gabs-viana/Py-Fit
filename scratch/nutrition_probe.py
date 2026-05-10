import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ingestion.zepp_api import ZeppAPI

def nutrition_probe():
    api = ZeppAPI()
    api.check_session()
    
    print("🚀 Buscando endpoints de Nutrição...")
    
    # Teste 1: Manual Data (comum para comida em apps Huami)
    print("🔍 Testando /v1/user/manualData.json (tipo 'food')...")
    endpoint = "/v1/user/manualData.json"
    params = {
        "type": "food",
        "limit": 10
    }
    data = api.fetch_data(endpoint, params=params)
    print(f"   Manual Data (food): {data}")

    # Teste 2: Events (v2)
    print("\n🔍 Testando v2 events (eventType 'food' ou 'diet')...")
    for etype in ["food", "diet", "nutrition", "meal"]:
        params = {
            "eventType": etype,
            "limit": 5
        }
        data = api.fetch_data("/v2/users/me/events", params=params)
        if data and data.get("items"):
            print(f"   ✅ ACHOU em v2 events ({etype}): {data['items'][0]}")
        else:
            print(f"   ❌ Nada em v2 events ({etype})")

if __name__ == "__main__":
    nutrition_probe()
