from zepp_api import ZeppAPI
from datetime import datetime

def test():
    print("🚀 Iniciando teste de conexão Py-Fit...")
    api = ZeppAPI()
    
    # Testa o Heartbeat (Profile)
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Data de teste: {today}")
    
    data = api.normalize_for_daily(today)
    
    if data:
        print("\n✅ SUCESSO ABSOLUTO!")
        print(f"📊 Readiness: {data['readiness_index']['score']} ({data['readiness_index']['status']})")
        print(f"👣 Passos: {data['biometrics']['steps']}")
        print(f"💤 Sono: {data['sleep']['total_hours'] if data['sleep'] else 'N/A'}h")
    else:
        print("\n❌ Falha ao buscar dados. Verifique os logs acima.")

if __name__ == "__main__":
    test()
