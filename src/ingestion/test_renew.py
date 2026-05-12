import sys
import os

# Adiciona o diretório src ao path para poder importar zepp_api
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

from ingestion.zepp_api import ZeppAPI

def test_renewal():
    print("Iniciando teste de Session Replay...")
    api = ZeppAPI()
    
    print(f"Token Antigo: {api.config.get('app_token')[:20]}...")
    print(f"Login Token Antigo: {api.config.get('login_token')[:20]}...")
    
    success = api.renew_session()
    
    if success:
        print("\n✅ SUCESSO ABSOLUTO! Sessão renovada.")
        print(f"Novo Token: {api.config.get('app_token')[:20]}...")
        print(f"Novo Login Token: {api.config.get('login_token')[:20]}...")
    else:
        print("\n❌ FALHA na renovação da sessão.")

if __name__ == "__main__":
    test_renewal()
