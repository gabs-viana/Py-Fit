
import requests
import json
import time
import os

# Carrega config
base_dir = os.path.abspath(os.path.join(os.getcwd()))
with open(os.path.join(base_dir, "config", "zepp_config.json"), "r") as f:
    config = json.load(f)

def discovery_v3():
    today = "2026-05-10"
    url = f"https://{config['host']}/v2/users/me/events"
    
    headers = {
        "User-Agent": "Zepp/10.2.5 (SM-N976N; Android 9; Density/2.0)",
        "apptoken": config["app_token"],
        "appname": "com.huami.midong",
        "appplatform": "android_phone",
        "cv": "151830_10.2.5",
        "vn": "10.2.5",
        "timezone": "America/Sao_Paulo"
    }
    
    # Testando HRV e Readiness especificamente no v2
    params_list = [
        {"startDate": today, "endDate": today, "eventType": "Hrv", "subType": "RMSSD"},
        {"startDate": today, "endDate": today, "eventType": "Charge", "subType": "insight_data"},
        {"startDate": today, "endDate": today, "eventType": "Readiness"}
    ]
    
    for params in params_list:
        print(f"📡 Tentando: {params['eventType']} ({params.get('subType', '')})...")
        try:
            r = requests.get(url, headers=headers, params=params)
            if r.status_code == 200:
                data = r.json()
                if data.get("items"):
                    print(f"  ✅ SUCESSO! Encontrado: {len(data['items'])} itens.")
                    print(json.dumps(data["items"][0], indent=2))
                else:
                    print("  ⚠️ Sem dados para este tipo hoje.")
            else:
                print(f"  ❌ Erro {r.status_code}: {r.text}")
        except Exception as e:
            print(f"  ❌ Falha: {e}")

if __name__ == "__main__":
    discovery_v3()
