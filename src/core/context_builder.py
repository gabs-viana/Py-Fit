import json
import os
import glob
from datetime import datetime, timedelta

# Configurações de Caminhos
# Configurações de Caminhos baseados na nova estrutura
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

CONSOLIDADAS_DIR = os.path.join(ROOT_DIR, "Daily Log", "Semanas_consolidadas")
FIT_DIR = os.path.join(ROOT_DIR, "Fit Analyzer")
MEMORY_FILE = os.path.join(ROOT_DIR, "data", "database", "athlete_memory.json")

def carregar_memoria():
    """Carrega a memória longitudinal do atleta."""
    if os.path.exists(MEMORY_FILE):
        return carregar_json(MEMORY_FILE)
    return {}

def obter_ultima_semana_consolidada():
    """Identifica a pasta Semana_X e retorna o caminho e o índice X."""
    if not os.path.exists(CONSOLIDADAS_DIR):
        return None, None
    
    pastas = [d for d in os.listdir(CONSOLIDADAS_DIR) if d.startswith("Semana_")]
    if not pastas:
        return None, None
    
    # Extrai os números e pega o maior
    try:
        indices = [int(d.split("_")[1]) for d in pastas]
        ultimo_idx = max(indices)
        return os.path.join(CONSOLIDADAS_DIR, f"Semana_{ultimo_idx}"), ultimo_idx
    except:
        return None, None

def carregar_json(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler {caminho}: {e}")
        return None

def buscar_treino_mais_recente():
    """Busca recursivamente o treino (JSON) mais recente no Fit Analyzer."""
    arquivos = glob.glob(os.path.join(FIT_DIR, "**", "Zepp*.json"), recursive=True)
    if not arquivos:
        return None
    
    # Ordena pelo nome do arquivo (que contém timestamp YYYYMMDD)
    arquivos.sort(key=lambda x: os.path.basename(x), reverse=True)
    return arquivos[0]

def carregar_logs_semana(pasta_semana):
    """Carrega todos os logs da pasta da semana (consolidada)."""
    # Procura por arquivos JSON que começam com "20" (formato YYYYMMDD)
    arquivos = sorted(glob.glob(os.path.join(pasta_semana, "20*.json")))
    logs = []
    for arq in arquivos:
        dado = carregar_json(arq)
        if dado:
            try:
                # O formato no JSON é DD/MM/YYYY
                dado["dt_obj"] = datetime.strptime(dado["data"], "%d/%m/%Y")
                logs.append(dado)
            except:
                continue
    return logs

def extrair_metricas_fit(fit_data):
    """Filtra apenas as métricas de elite/ouro do Fit Analyzer."""
    resumo = fit_data.get("resumo", {})
    v6 = fit_data.get("v6_elite", {})
    aval = fit_data.get("avaliacao", {})
    
    return {
        "id": os.path.basename(fit_data.get("id", "fit_analysis")),
        "tipo": aval.get("tipo_treino_detectado"),
        "score_fit": aval.get("score_0_10"),
        "drift_aerobico": resumo.get("drift_aerobico"),
        "dominancia_simpatica": v6.get("dominancia_simpatica"),
        "pacing_emocional": v6.get("pacing_emocional_detectado"),
        "fluxo_util_min": v6.get("tempo_fluxo_util_min"),
        "recuperacao_fc": resumo.get("recuperacao_fc"),
        "gap_pace": resumo.get("gap_pace"),
        "esforço_perc": resumo.get("training_effect")
    }

def extrair_metricas_daily(daily_data):
    """Filtra métricas relevantes do Daily Log."""
    return {
        "data": daily_data.get("data"),
        "readiness": daily_data.get("readiness"),
        "energia": daily_data.get("estado", {}).get("energia"),
        "stress": daily_data.get("estado", {}).get("estresse"),
        "sono_horas": daily_data.get("sono", {}).get("horas"),
        "hrv": daily_data.get("wearable", {}).get("hrv_ms"),
        "rhr": daily_data.get("wearable", {}).get("rhr"),
        "treino_executado": daily_data.get("treino", {}).get("executado"),
        "alimentacao_desc": daily_data.get("alimentacao", {}).get("descricao", "")
    }

def extrair_contexto_alimentar(logs):
    """Analisa o texto das refeições em busca de padrões semânticos."""
    palavras_sabotagem = ["bolo", "fritura", "lanche", "batata frita", "refrigerante", "doce", "açúcar", "pizza", "hambúrguer", "refri"]
    palavras_proteina = ["carne", "frango", "ovo", "peixe", "whey", "proteína", "músculo", "linguiça"]
    
    ultraprocessado = False
    proteina_presente = False
    omitidas = 0

    for l in logs:
        desc = l.get("alimentacao_desc", "").lower()
        if any(p in desc for p in palavras_sabotagem):
            ultraprocessado = True
        if any(p in desc for p in palavras_proteina):
            proteina_presente = True
        if "faltando" in desc or "sem jantar" in desc or "pulei" in desc:
            omitidas += 1
            
    return {
        "ultraprocessado_detectado": ultraprocessado,
        "proteina_inconsistente": not proteina_presente,
        "refeicoes_omitidas_estimadas": omitidas,
        "densidade_nutricional": "baixa" if ultraprocessado else "boa"
    }

def calcular_assinatura_recuperacao(impactos, baseline):
    """Gera a meta-análise da curva de recuperação."""
    if not impactos or not baseline:
        return {}
    
    quedas_energia = [v["delta_vs_treino"]["energia"] for v in impactos.values() if "delta_vs_treino" in v]
    
    severidade = "baixa"
    if any(q <= -4 for q in quedas_energia): severidade = "crítica"
    elif any(q <= -2 for q in quedas_energia): severidade = "moderada"
    
    # Estimativa de horas para normalização
    horas = 24
    recuperacao = "rápida"
    for dia, dados in impactos.items():
        if dados.get("delta_vs_treino", {}).get("energia", 0) < 0:
            horas += 24
            recuperacao = "lenta"
        else:
            break
            
    return {
        "severidade_impacto": severidade,
        "tempo_normalizacao_estimado_horas": horas,
        "assinatura_recuperacao": recuperacao,
        "persistencia_fadiga": "alta" if horas > 48 else "baixa"
    }

def analisar_aderencia_pos_esforco(impactos):
    """Verifica se o atleta falhou em treinar após o grande esforço."""
    falhas = [dia for dia, d in impactos.items() if d["treino_executado"] == "n"]
    return {
        "baixa_execucao_pos_esforco": len(falhas) > 0,
        "fadiga_percebida_impacto_operacional": "alta" if len(falhas) >= 2 else "moderada"
    }

def calcular_impactos(treino_dt, logs_semana):
    """
    Calcula a evolução das métricas nos dias seguintes ao treino.
    """
    impactos = {}
    log_d0 = next((l for l in logs_semana if l["dt_obj"].date() == treino_dt.date()), None)
    
    for i in range(1, 4): # Analisar até D+3
        target_dt = treino_dt + timedelta(days=i)
        log_di = next((l for l in logs_semana if l["dt_obj"].date() == target_dt.date()), None)
        
        if log_di:
            metrica_di = extrair_metricas_daily(log_di)
            if log_d0:
                delta_energia = (metrica_di["energia"] or 0) - (log_d0["estado"]["energia"] or 0)
                metrica_di["delta_vs_treino"] = {
                    "energia": round(delta_energia, 1)
                }
            impactos[f"D+{i}"] = metrica_di
            
    return impactos

def build_context():
    print("🚀 Iniciando Context Builder (Crossover Fit <-> Daily)...")
    
    # 1. Identificar Pasta de Destino e Índice
    pasta_semana, idx_semana = obter_ultima_semana_consolidada()
    
    if pasta_semana:
        print(f"📁 Pasta detectada: Semana_{idx_semana}")
        nome_arquivo = f"contexto_semana_{idx_semana}.json"
        output_path = os.path.join(pasta_semana, nome_arquivo)
    else:
        print("⚠️ Nenhuma pasta consolidada encontrada. Tentando pasta 'Semana' atual.")
        pasta_semana = os.path.join(BASE_DIR, "Daily Log", "Semana")
        output_path = os.path.join(BASE_DIR, "contexto_semana.json")

    # 2. Carregar Treino Mais Recente
    fit_path = buscar_treino_mais_recente()
    if not fit_path:
        print("⚠️ Nenhum treino encontrado no Fit Analyzer.")
        return
    
    fit_data = carregar_json(fit_path)
    if not fit_data: return
    
    nome_arq = os.path.basename(fit_path)
    try:
        dt_str = nome_arq.replace("Zepp", "")[:8]
        treino_dt = datetime.strptime(dt_str, "%Y%m%d")
    except:
        print("⚠️ Não foi possível determinar a data do treino.")
        return

    fit_context = extrair_metricas_fit(fit_data)
    fit_context["data_treino"] = treino_dt.strftime("%d/%m/%Y")

    # 3. Carregar Logs
    logs_semana = carregar_logs_semana(pasta_semana)
    if not logs_semana:
        print(f"⚠️ Nenhum log diário encontrado em: {pasta_semana}")
        return
    
    # 4. Calcular Meta-Contexto
    hoje = datetime.now()
    dias_desde_corrida = (hoje.date() - treino_dt.date()).days
    
    log_d0 = next((l for l in logs_semana if l["dt_obj"].date() == treino_dt.date()), None)
    impactos = calcular_impactos(treino_dt, logs_semana)
    
    # 5. Carregar Memória do Atleta
    memoria = carregar_memoria()
    
    # 6. Montar Super Contexto
    super_contexto = {
        "timestamp_geracao": hoje.strftime("%d/%m/%Y %H:%M"),
        "analise_longitudinal": {
            "dias_desde_ultimo_treino": dias_desde_corrida,
            "status_atual": "Recuperação" if dias_desde_corrida <= 2 else "Pronto para nova carga"
        },
        "memoria_do_atleta": memoria,
        "baseline_treino_d0": extrair_metricas_daily(log_d0) if log_d0 else None,
        "ultimo_treino_relevante": fit_context,
        "evolucao_pos_treino": impactos,
        "meta_analise": {
            "recuperacao": calcular_assinatura_recuperacao(impactos, log_d0),
            "aderencia": analisar_aderencia_pos_esforco(impactos),
            "alimentacao": extrair_contexto_alimentar(logs_semana)
        },
        "resumo_semana_daily": [extrair_metricas_daily(l) for l in logs_semana]
    }
    
    # 5. Salvar
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(super_contexto, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Super Contexto gerado com sucesso em: {output_path}")

if __name__ == "__main__":
    build_context()
