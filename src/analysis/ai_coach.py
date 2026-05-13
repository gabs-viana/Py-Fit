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

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sugerir_remanejamento_treino",
            "description": "Sugere fortemente uma alteração no treino de amanhã devido a fadiga (TSB negativo) ou risco de lesão (ACWR > 1.5).",
            "parameters": {
                "type": "object",
                "properties": {
                    "novo_treino": {
                        "type": "string",
                        "description": "O tipo de treino recomendado para amanhã (ex: 'Descanso', 'Recovery Run', 'Mobilidade')."
                    },
                    "justificativa": {
                        "type": "string",
                        "description": "A justificativa sádico-construtiva de por que a carga deve ser reduzida."
                    }
                },
                "required": ["novo_treino", "justificativa"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ajustar_meta_agua",
            "description": "Ajusta a meta de hidratação para o dia seguinte se houver perda de suor detectada ou baixa ingestão.",
            "parameters": {
                "type": "object",
                "properties": {
                    "litros": {
                        "type": "number",
                        "description": "A nova meta de hidratação em litros (ex: 3.5)."
                    },
                    "justificativa": {
                        "type": "string",
                        "description": "Por que a meta foi aumentada."
                    }
                },
                "required": ["litros", "justificativa"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emitir_alerta_sistemico",
            "description": "Emite um alerta crítico (vermelho) que será forçado na tela do usuário antes dele preencher o log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mensagem": {
                        "type": "string",
                        "description": "A mensagem de alerta de risco."
                    }
                },
                "required": ["mensagem"]
            }
        }
    }
]

def get_coach_insight():
    try:
        with open(PROMPT_PATH, "r", encoding='utf-8') as f:
            system_prompt = f.read()
    except Exception as e:
        return f"❌ Erro ao carregar o prompt: {e}", []
    
    if not os.path.exists(DATA_PATH):
        return "❌ Erro: Dados de hoje não encontrados. Execute a sincronização primeiro.", []
        
    try:
        with open(DATA_PATH, "r", encoding='utf-8') as f:
            today_data = json.load(f)
    except Exception as e:
        return f"❌ Erro ao ler dados: {e}", []
        
    print("🧠 Consultando o Protocolo Sentinel (GPT-4o-mini)...")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Aqui estão meus dados de hoje: {json.dumps(today_data, indent=2)}"}
    ]

    actions_taken = []

    try:
        response = client.chat.completions.create(
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7
        )
        
        response_message = response.choices[0].message
        
        # O Coach decidiu usar alguma ferramenta?
        if response_message.tool_calls:
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"⚙️ [Tool Calling] O Coach acionou: {function_name}")
                actions_taken.append({
                    "action": function_name,
                    "args": function_args
                })
                
                # Feedback simulado para a IA continuar o texto
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"status": "success", "message": "Ação registrada no sistema. Aguardando aprovação do usuário."})
                })
                
            # Segunda chamada para gerar o texto final após usar as tools
            second_response = client.chat.completions.create(
                model=os.getenv("AI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=0.7
            )
            final_text = second_response.choices[0].message.content
        else:
            final_text = response_message.content

        return final_text, actions_taken

    except Exception as e:
        if "api_key" in str(e).lower():
            return "❌ Erro: API Key inválida ou ausente no arquivo .env.", []
        return f"❌ Erro na API: {e}", []

if __name__ == "__main__":
    insight, actions = get_coach_insight()
    
    print("\n" + "═"*50)
    print(" 🔥 O VEREDITO DO SENTINEL 🔥")
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

    # 2. Injeta no ai_state.json as ações do AI para que o daily.py processe amanhã
    try:
        ai_state_path = os.path.join(ROOT_DIR, "data", "prefill", "ai_state.json")
        state_data = {
            "coach_insight": insight,
            "ai_actions": actions,
            "date_generated": datetime.now().strftime("%Y-%m-%d")
        }
        with open(ai_state_path, "w", encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
        print(f"⚠️ {len(actions)} ações sistêmicas foram salvas em ai_state.json para a próxima revisão.")
    except Exception as e:
        print(f"⚠️ Erro ao salvar ai_state: {e}")
