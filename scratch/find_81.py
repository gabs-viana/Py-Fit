
import sys
import os
import json

sys.path.append(os.path.join(os.getcwd(), "src"))
from ingestion.zepp_api import ZeppAPI

def find_81():
    api = ZeppAPI()
    today = "2026-05-10"
    print(f"🕵️‍♂️ Operação Resgate: Buscando o Score 81 em {today}...")
    
    # 1. Puxa tudo que é unificado
    unified = api.get_unified_data(today)
    if unified and "summary_decoded" in unified:
        summary = unified["summary_decoded"]
        # Dump para eu ler as chaves
        with open("scratch/summary_dump.json", "w") as f:
            json.dump(summary, f, indent=2)
            
        print("🔍 Vasculhando chaves do sumário...")
        for k, v in summary.items():
            if v == 81 or (isinstance(v, dict) and 81 in v.values()):
                print(f"🎯 ACHEI O 81 NA CHAVE: {k} -> {v}")
    
    # 2. Busca o despertar exato para o Biocharge
    slp = api.get_daily_sleep(today)
    if slp and "items" in slp and slp["items"]:
        # O último item do sono geralmente tem o stop time
        last_sleep = slp["items"][-1]
        wake_time = last_sleep.get("stop") # Ex: 1778418000
        print(f"⏰ Horário do Despertar Detectado: {wake_time}")

if __name__ == "__main__":
    find_81()
