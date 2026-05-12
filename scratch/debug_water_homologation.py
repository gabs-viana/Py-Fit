import os
import sys
import json
from datetime import datetime, timedelta
import time

# Ajuste de path para achar os módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ingestion.zepp_api import ZeppAPI

def debug_water_today():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    config_path = os.path.join(base_dir, "config", "zepp_config.json")
    
    api = ZeppAPI(config_path)
    date_str = "2026-05-12" # Focado em hoje
    
    print(f"--- 🛰️ VARREDURA TOTAL DE EVENTOS para {date_str} ---")
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start_ts = int(dt.timestamp() * 1000)
    end_ts = int((dt.timestamp() + 86400 + 21600) * 1000)
    
    # Usa a função oficial que sabemos que funciona (a mesma do Estresse/PAI)
    print(f"--- 🧬 Buscando no fluxo do Estresse/PAI ({date_str}) ---")
    data = api.get_stress_and_pai(date_str)
    
    if data and "items" in data and data["items"]:
        print(f"✅ Sucesso! Encontrados {len(data['items'])} itens no fluxo.")
        for item in data["items"]:
            e_type = item.get("eventType")
            # Se encontrar qualquer menção a água ou volume
            raw = json.dumps(item).lower()
            if "água" in raw or "water" in raw or "ml" in raw:
                print(f"⭐ ÁGUA DETECTADA NO FLUXO!")
                print(json.dumps(item, indent=4))
            else:
                print(f" - Tipo ignorado: {e_type}")
    else:
        print(f"❌ Nenhum item no fluxo de eventos para hoje.")

if __name__ == "__main__":
    debug_water_today()
