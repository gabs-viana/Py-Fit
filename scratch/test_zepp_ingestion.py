
import sys
import os
import json
from datetime import datetime

# Adiciona o caminho do src para importar o ZeppAPI
sys.path.append(os.path.join(os.getcwd(), "src"))
from ingestion.zepp_api import ZeppAPI

def test_extraction():
    api = ZeppAPI()
    today = "2026-05-10"
    
    print(f"🚀 Iniciando extração de elite para {today}...")
    data = api.normalize_for_daily(today)
    
    if data:
        print("\n✅ Dados capturados com sucesso:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Validação de campos novos
        if data.get("sleep") and data["sleep"].get("score"):
            print(f"⭐️ Sleep Score: {data['sleep']['score']}")
        if data.get("hrv"):
            print(f"💓 HRV (RMSSD): {data['hrv']} ms")
        if data.get("pai_gain"):
            print(f"🔥 PAI Ganho hoje: +{data['pai_gain']}")
    else:
        print("❌ Falha na extração. Verifique o token ou a conexão.")

if __name__ == "__main__":
    test_extraction()
