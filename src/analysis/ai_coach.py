import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

# Inicializa o cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Caminhos de arquivos
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROMPT_PATH = os.path.join(ROOT_DIR, "Docs", "COACH_PROMPT.md")
DATA_PATH = os.path.join(ROOT_DIR, "data", "prefill", "prefill_daily.json")

def get_coach_insight():
    # 1. Carrega o Prompt do Sistema (Manual de Instruções)
    try:
        with open(PROMPT_PATH, "r", encoding='utf-8') as f:
            system_prompt = f.read()
    except Exception as e:
        return f"❌ Erro ao carregar o prompt: {e}"
    
    # 2. Carrega os dados de hoje
    if not os.path.exists(DATA_PATH):
        return "❌ Erro: Dados de hoje não encontrados. Por favor, execute a sincronização primeiro."
        
    try:
        with open(DATA_PATH, "r", encoding='utf-8') as f:
            today_data = json.load(f)
    except Exception as e:
        return f"❌ Erro ao ler dados: {e}"
        
    print("🧠 Consultando o Oráculo Py-Fit (GPT-4o-mini)...")
    
    try:
        # 3. Chamada da API
        response = client.chat.completions.create(
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Aqui estão meus dados de hoje: {json.dumps(today_data, indent=2)}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        if "api_key" in str(e).lower():
            return "❌ Erro: API Key inválida ou ausente no arquivo .env."
        return f"❌ Erro na API: {e}"

if __name__ == "__main__":
    insight = get_coach_insight()
    
    # FINALIZAÇÃO (Exibição e Persistência)
    print("\n" + "═"*50)
    print(" 🔥 O VEREDITO DO COACH PY-FIT 🔥")
    print("═"*50)
    print(insight)
    print("═"*50 + "\n")

    # 1. Salva como Markdown no Histórico
    try:
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        history_path = os.path.join(ROOT_DIR, "data", "history", f"coach_{date_str}.md")
        with open(history_path, "w", encoding='utf-8') as f:
            f.write(f"# 📜 Veredito do Coach - {date_str}\n\n")
            f.write(insight)
        print(f"✅ Veredito salvo em: {history_path}")
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico MD: {e}")

    # 2. Injeta no Prefill JSON para uso futuro
    try:
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, "r", encoding='utf-8') as f:
                data = json.load(f)
            data["coach_insight"] = insight
            with open(DATA_PATH, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erro ao atualizar prefill: {e}")
