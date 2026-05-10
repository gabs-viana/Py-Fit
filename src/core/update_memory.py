import json
import os
import re

# Configuração de caminhos baseados na nova estrutura
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

MEMORY_FILE = os.path.join(ROOT_DIR, "data", "database", "athlete_memory.json")
UPDATE_FILE = os.path.join(ROOT_DIR, "data", "database", "update.txt")

def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(dados, caminho):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def extrair_json_do_texto(texto):
    # Procura o conteúdo entre as tags [MEMORY_UPDATE]
    # O re.DOTALL faz o . capturar quebras de linha
    match = re.search(r"\[MEMORY_UPDATE\]\s*(\{.*?\})\s*\[/MEMORY_UPDATE\]", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao decodificar JSON do GPT: {e}")
    return None

def main():
    if not os.path.exists(UPDATE_FILE):
        print(f"⚠️ Arquivo {UPDATE_FILE} não encontrado. Crie o arquivo e cole a resposta do GPT.")
        return

    if not os.path.exists(MEMORY_FILE):
        print(f"❌ Arquivo de memória {MEMORY_FILE} não encontrado.")
        return

    with open(UPDATE_FILE, "r", encoding="utf-8") as f:
        texto = f.read()

    update_data = extrair_json_do_texto(texto)
    if not update_data:
        print("❌ Nenhuma tag [MEMORY_UPDATE] válida encontrada no texto.")
        return

    memoria = carregar_json(MEMORY_FILE)

    # 1. Atualizar Insight Histórico
    # Vamos usar a contagem de semanas atual para o index
    historico = memoria.get("historico_de_insights", [])
    proxima_semana = len(historico)
    
    novo_insight = {
        "semana": proxima_semana,
        "veredito": update_data.get("insight_semana", "Sem veredito."),
        "gargalo_chave": update_data.get("gargalo_chave", "N/A")
    }
    memoria["historico_de_insights"].append(novo_insight)

    # 2. Adicionar Novo Padrão (se houver)
    if "novo_padrao" in update_data:
        # Verifica se já existe um padrão do mesmo tipo para não duplicar, ou apenas anexa
        memoria["padroes_detectados"].append(update_data["novo_padrao"])

    # 3. Ajustar Assinatura Fisiológica
    if "ajuste_assinatura" in update_data:
        for k, v in update_data["ajuste_assinatura"].items():
            # Tenta encontrar onde a chave se encaixa
            if k in memoria["assinaturas_fisiologicas"]["recuperacao"]:
                memoria["assinaturas_fisiologicas"]["recuperacao"][k] = v
            elif k in memoria["assinaturas_fisiologicas"]["cardio"]:
                memoria["assinaturas_fisiologicas"]["cardio"][k] = v
            else:
                # Se for uma chave nova, coloca em recuperação por padrão
                memoria["assinaturas_fisiologicas"]["recuperacao"][k] = v

    salvar_json(memoria, MEMORY_FILE)
    print(f"✅ Memória do Atleta atualizada com sucesso! (Sincronizado histórico da Semana {proxima_semana})")

if __name__ == "__main__":
    main()
