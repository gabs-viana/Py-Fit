import requests
import json
import os
import re
import argparse

# Configurações de API Zepp/Huami
LOGIN_URL = "https://api-user.huami.com/registrations/{}/tokens?password={}"
# Fluxo Xiaomi/Mi (Geralmente o mais estável para Zepp/Amazfit)
AUTH_URL = "https://account.xiaomi.com/oauth2/authorize?skip_confirm=false&client_id=2882303761517305101&pt=0&scope=1%206000%2016001%2020000&redirect_uri=https%3A%2F%2Fapi-mifit-us3.zepp.com%2Fdevices%2Fauth%2Fxiaomi%2Fcallback&_locale=pt_BR&response_type=code"

def get_tokens_from_url(url):
    """Extrai os tokens da URL de redirecionamento após o login."""
    match = re.search(r"access_token=(.*?)&", url)
    if not match:
        # Tenta pegar o code se não houver access_token direto
        match = re.search(r"code=(.*?)($|&)", url)
        if not match:
            print("❌ Erro: Não encontrei o token ou código na URL.")
            return None
    
    # Detecta se é um code da Xiaomi
    is_code = "code=" in url
    token_or_code = match.group(1)
    print(f"✅ {'Código (Xiaomi)' if is_code else 'Token'} detectado: {token_or_code[:10]}...")
    
    # Agora trocamos isso pelo app_token final
    login_data = {
        "dn": "api-user.huami.com,api-mifit.huami.com,app-analytics.huami.com",
        "app_name": "com.xiaomi.hm.health",
        "code": token_or_code,
        "grant_type": "code" if is_code else "access_token",
        "allow_params": "true"
    }
    
    if is_code:
        # Se for code da Xiaomi, precisamos especificar o app_id usado no AUTH_URL
        login_data["app_id"] = "2882303761517305101"
    
    # Endpoint de troca de token
    response = requests.post("https://api-user.huami.com/tokens", data=login_data)
    result = response.json()
    
    if "token_info" in result:
        return {
            "app_token": result["token_info"]["app_token"],
            "user_id": result["token_info"]["user_id"],
            "login_token": result["token_info"]["login_token"]
        }
    else:
        print(f"❌ Erro na troca de token: {result}")
        return None

def main():
    print("=== Py-Fit: Capturador de Token Zepp ===")
    print("\nSiga os passos abaixo:")
    print(f"1. Abra este link no seu navegador:\n\n{AUTH_URL}\n")
    print("2. Faça login com sua conta Zepp (Google, Mi, etc.).")
    print("3. Após o login, você será redirecionado. A página pode dar erro, NÃO TEM PROBLEMA.")
    print("4. Copie a URL INTEIRA da barra de endereços e cole aqui embaixo.\n")
    
    user_url = input("URL de redirecionamento: ").strip()
    
    tokens = get_tokens_from_url(user_url)
    
    if tokens:
        config = {
            "app_token": tokens["app_token"],
            "login_token": tokens.get("login_token"),
            "user_id": tokens["user_id"],
            "host": "api-mifit.huami.com" # Global como padrão, us3 como fallback no builder
        }
        
        # Salva na pasta config na raiz do projeto
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_path = os.path.join(root_dir, "config", "zepp_config.json")
        
        with open(save_path, "w") as f:
            json.dump(config, f, indent=4)
            
        print(f"\n🚀 SUCESSO! Configuração salva em: {save_path}")
        print("Agora o Py-Fit tem as chaves mestras para a nuvem.")
    else:
        print("\n⚠️ Falha ao obter os tokens. Verifique se copiou a URL correta.")

if __name__ == "__main__":
    main()
