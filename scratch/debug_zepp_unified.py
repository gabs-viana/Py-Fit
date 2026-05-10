
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), "src"))
from ingestion.zepp_api import ZeppAPI

def debug_unified():
    api = ZeppAPI()
    today = "2026-05-10"
    print(f"🔍 Investigando sumário decodificado para {today}...")
    
    unified = api.get_unified_data(today)
    if unified and "summary_decoded" in unified:
        print("\n💎 Sumário Decodificado (Raw Keys):")
        summary = unified["summary_decoded"]
        print(json.dumps(summary, indent=2))
        
        # Procura por HRV ou Readiness
        for key in summary.keys():
            if key in ["hrv", "vfc", "rdn", "readiness", "chg", "biocharge"]:
                print(f"🎯 ACHAMOS UMA KEY INTERESSANTE: {key} -> {summary[key]}")
    else:
        print("❌ Não foi possível obter o sumário unificado.")

if __name__ == "__main__":
    debug_unified()
