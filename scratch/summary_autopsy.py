import sys
import os
import json

# Adiciona a raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import base64
from src.ingestion.zepp_api import ZeppAPI

def autopsy_summary(date_str):
    api = ZeppAPI()
    api.check_session()
    print(f"🔬 Iniciando autópsia do sumário para {date_str}...")
    
    unified = api.get_unified_data(date_str)
    if not unified or "summary_decoded" not in unified:
        print("❌ Sumário não encontrado.")
        return

    summary = unified["summary_decoded"]
    
    # Salva o sumário completo para inspeção manual se necessário
    output_file = f"scratch/autopsy_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Sumário salvo em {output_file}")
    print("\n🔍 Buscando chaves suspeitas de VFC/HRV...")
    
    suspect_keys = ["hrv", "vfc", "rmssd", "sdnn", "readiness", "score", "ss", "hp"]
    found = []
    
    def search_recursive(d, path=""):
        if isinstance(d, dict):
            for k, v in d.items():
                new_path = f"{path}.{k}" if path else k
                if any(s in k.lower() for s in suspect_keys):
                    found.append((new_path, v))
                search_recursive(v, new_path)
        elif isinstance(d, list):
            for i, item in enumerate(d):
                search_recursive(item, f"{path}[{i}]")

    search_recursive(summary)
    
    if found:
        for path, val in found:
            print(f"🚩 ACHADO: {path} = {val}")
    else:
        print("📭 Nenhuma chave óbvia encontrada. O VFC pode estar codificado em chaves de 2 letras (ex: 'rv', 'hv').")
        print(f"📋 Chaves de nível 1 disponíveis: {list(summary.keys())}")

if __name__ == "__main__":
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else "2026-05-10"
    autopsy_summary(date)
