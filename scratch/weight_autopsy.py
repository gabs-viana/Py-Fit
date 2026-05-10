import sys
import os
import json
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ingestion.zepp_api import ZeppAPI

def weight_autopsy():
    api = ZeppAPI()
    api.check_session()
    
    user_id = api.config['user_id']
    token = api.config['app_token']
    
    url = f"https://api-mifit-us3.zepp.com/users/{user_id}/members/-1/weightRecords"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "apptoken": token,
        "User-Agent": "Zepp/10.2.5 (SM-N976N; Android 9; Density/2.0)"
    }
    
    # Tentativa 1: Sem parâmetros extras, só o limit
    print(f"🔍 Tentando GET Peso em: {url}")
    r = requests.get(url, headers=headers, params={"limit": 5})
    
    print(f"📡 Status: {r.status_code}")
    try:
        data = r.json()
        print(f"📦 Resposta Bruta: {json.dumps(data, indent=2)[:1000]}...") # Primeiros 1000 chars
    except:
        print(f"❌ Resposta não é JSON: {r.text}")

if __name__ == "__main__":
    weight_autopsy()
