import sys
import os
from datetime import datetime

# Adiciona o diretório src ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

from ingestion.zepp_api import ZeppAPI

def test_fetch():
    print("🚀 Testando Ingestão com DNA de POCO...")
    api = ZeppAPI()
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📅 Buscando dados para: {today}")
    data = api.normalize_for_daily(today)
    
    if data:
        print("\n✅ SUCESSO! Dados recebidos da Zepp Cloud:")
        print(f"Índice de Readiness: {data['readiness_index']['score']}")
        print(f"Status: {data['readiness_index']['status']}")
        print(f"Passos: {data['biometrics']['steps']}")
        print(f"RHR: {data['biometrics']['rhr']}")
        print(f"Sono (Horas): {data['sleep']['total_hours'] if data['sleep'] else 'N/A'}")
        print("\nO transplante de DNA do POCO funcionou perfeitamente!")
    else:
        print("\n❌ FALHA na busca de dados. Verifique o token ou a conexão.")

if __name__ == "__main__":
    test_fetch()
