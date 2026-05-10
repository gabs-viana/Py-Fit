import json
import os
import requests
import time
from datetime import datetime

def check_latest_stress():
    config_path = "config/zepp_config.json"
    with open(config_path, "r") as f:
        config = json.load(f)

    headers = {
        "Authorization": f"Bearer {config['app_token']}",
        "apptoken": config['app_token'],
        "User-Agent": "Zepp/10.2.5 (SM-N976N; Android 9; Density/2.0)"
    }
    
    # Range enorme só pra achar onde estão os dados
    url = "https://api-mifit-us3.zepp.com/v2/users/me/events"
    params = {
        "limit": 50,
        "subType": "single_stress",
        "eventType": "single_stress",
        "from": 0,
        "to": int(time.time() * 1000) + 1000000000,
        "reverse": "true"
    }
    
    print("🔍 Sonda de Estresse Iniciada...")
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        items = r.json().get("items", [])
        if not items:
            print("❌ Nenhum evento de estresse encontrado no histórico.")
            return
        
        print(f"✅ Encontrados {len(items)} eventos.")
        for item in items[:5]:
            ts = item.get("timestamp")
            dt = datetime.fromtimestamp(ts/1000)
            avg = item.get("value", {}).get("avgStress")
            print(f"📅 Data: {dt.strftime('%Y-%m-%d %H:%M')} | Stress Médio: {avg}")
    else:
        print(f"❌ Erro na API: {r.status_code} - {r.text}")

if __name__ == "__main__":
    check_latest_stress()
