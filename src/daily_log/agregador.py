import json
import os
import shutil
from datetime import datetime

PASTA = "Semana"

# =========================
# LOAD
# =========================
def carregar_semana():
    arquivos = sorted([f for f in os.listdir(PASTA) if f.endswith(".json")])
    dados = []

    for arq in arquivos:
        with open(os.path.join(PASTA, arq), "r") as f:
            d = json.load(f)

            # adiciona weekday baseado na data
            data = datetime.strptime(d["data"], "%d/%m/%Y")
            d["weekday"] = data.weekday()

            dados.append(d)

    return dados

def carregar_resumo_anterior():
    idx_atual = proxima_semana()
    if idx_atual == 0:
        return None
    idx_anterior = idx_atual - 1
    caminho = os.path.join("Semanas_consolidadas", f"Semana_{idx_anterior}", "resumo.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return None
    return None

def media(lista):
    lista = [x for x in lista if x is not None]
    return round(sum(lista)/len(lista), 2) if lista else None

# =========================
# CORE vs EXTRA
# =========================
def separar_grupos(semana):
    core = []
    extra = []

    for d in semana:
        wd = d["weekday"]

        if wd in [0,1,2,4]:  # seg, ter, qua, sex
            core.append(d)
        else:  # qui, sab, dom
            extra.append(d)

    return core, extra

# =========================
# ANALISE BLOCO
# =========================
def analisar_bloco(dados):
    if not dados:
        return {}

    scores = [d["score"] for d in dados]
    score_medio = media(scores)

    execs = []
    for d in dados:
        t = d.get("treino", {})
        if t.get("planejado", "Descanso") != "Descanso":
            execs.append(1 if t.get("executado") == "s" else 0)

    taxa_exec = round(sum(execs)/len(execs)*100, 2) if execs else 0

    cinturas = [d.get("corpo", {}).get("cintura") for d in dados if d.get("corpo", {}).get("cintura") is not None]
    delta_cintura = round(cinturas[-1] - cinturas[0], 2) if len(cinturas) > 1 else None

    return {
        "dias": len(dados),
        "score_medio": score_medio,
        "taxa_execucao": taxa_exec,
        "delta_cintura": delta_cintura
    }

# =========================
# MAIN
# =========================
def proxima_semana():
    pasta_base = "Semanas_consolidadas"

    if not os.path.exists(pasta_base):
        os.makedirs(pasta_base)

    existentes = [d for d in os.listdir(pasta_base) if d.startswith("Semana_")]

    if not existentes:
        return 0

    indices = [int(d.split("_")[1]) for d in existentes]
    return max(indices) + 1

def consolidar_semana(resumo=None):
    pasta_origem = "Semana"
    pasta_destino_base = "Semanas_consolidadas"

    idx = proxima_semana()
    pasta_destino = os.path.join(pasta_destino_base, f"Semana_{idx}")

    os.makedirs(pasta_destino, exist_ok=True)

    arquivos = [f for f in os.listdir(pasta_origem) if f.endswith(".json")]

    for arq in arquivos:
        origem = os.path.join(pasta_origem, arq)
        destino = os.path.join(pasta_destino, arq)

        shutil.move(origem, destino)

    if resumo:
        caminho_resumo = os.path.join(pasta_destino, "resumo.json")
        with open(caminho_resumo, "w", encoding="utf-8") as f:
            json.dump(resumo, f, indent=4, ensure_ascii=False)

    print(f"\n📦 Semana consolidada em: {pasta_destino} (com resumo.json)")

def calcular():
    semana = carregar_semana()

    if not semana:
        print("Sem dados.")
        return

    quarta = get_quarta(semana)

    cintura_oficial = None
    peso_oficial = None

    if quarta:
        cintura_oficial = quarta["corpo"]["cintura"]
        peso_oficial = quarta["corpo"]["peso"]
        
    # ===== ANÁLISE ORIGINAL (mantida) =====
    cinturas = [d.get("corpo", {}).get("cintura") for d in semana if d.get("corpo", {}).get("cintura") is not None]
    cintura_media = media(cinturas)
    
    delta_cintura_real = None
    if len(cinturas) >= 2:
        delta_cintura_real = round(cinturas[-1] - cinturas[0], 2)
    
    pesos = [d.get("corpo", {}).get("peso") for d in semana if d.get("corpo", {}).get("peso") is not None]
    peso_fallback = media(pesos)

    # Novas Métricas
    agua = media([d.get("habitos", {}).get("agua_litros") for d in semana])
    alcool_dias = sum([1 for d in semana if d.get("habitos", {}).get("alcool") == "s"])

    passos = media([d.get("wearable", {}).get("passos") for d in semana])
    rhr = media([d.get("wearable", {}).get("rhr") for d in semana])
    pai = media([d.get("wearable", {}).get("pai") for d in semana])

    horas = media([d["sono"]["horas"] for d in semana])
    qualidade = media([d["sono"]["qualidade"] for d in semana])
    bio_manha = media([d["sono"]["bio_manha"] for d in semana])

    energia = media([d["estado"]["energia"] for d in semana])
    foco = media([d["estado"]["foco"] for d in semana])
    estresse = media([d["estado"]["estresse"] for d in semana])

    textos_alimentacao = []
    textos_treino = []
    textos_contexto = []
    
    dias_nome = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"}
    
    for d in semana:
        nome_dia = dias_nome.get(d.get("weekday"), "")
        prefix = f"[{nome_dia} - {d.get('data')}]"
        
        desc = d.get("alimentacao", {}).get("descricao")
        if desc:
            textos_alimentacao.append(f"{prefix}: {desc}")
            
        ft = d.get("treino", {}).get("feeling")
        if ft:
            textos_treino.append(f"{prefix}: {ft}")
            
        ctx = d.get("contexto")
        if ctx:
            textos_contexto.append(f"{prefix}: {ctx}")

    execs = []
    completude = []
    intensidade = []

    for d in semana:
        t = d.get("treino", {})
        if t.get("planejado", "Descanso") != "Descanso":
            execs.append(1 if t.get("executado") == "s" else 0)

        if t.get("executado") == "s":
            completude.append(t.get("completude", 0))
            intensidade.append(t.get("intensidade", 0))

    taxa_exec = round(sum(execs)/len(execs)*100, 2) if execs else 0
    comp_media = media(completude)
    int_media = media(intensidade)

    scores = [d["score"] for d in semana]
    score_medio = media(scores)

    def classificar(score):
        if score >= 850: return "Elite"
        elif score >= 700: return "Forte"
        elif score >= 550: return "Boa"
        elif score >= 400: return "Regular"
        else: return "Fraca"

    # ===== CORE vs EXTRA =====
    core, extra = separar_grupos(semana)

    analise_core = analisar_bloco(core)
    analise_extra = analisar_bloco(extra)

    # ===== DIAGNÓSTICO =====
    diagnostico = []

    if analise_core.get("score_medio", 0) > 700 and analise_extra.get("score_medio", 0) < 600:
        diagnostico.append("Final de semana está sabotando a semana")

    if taxa_exec < 70:
        diagnostico.append("Baixa execução de treinos")


    if comp_media and comp_media < 70:
        diagnostico.append("Treinos incompletos")

    if score_medio and score_medio > 700 and delta_cintura_real and delta_cintura_real >= 0:
        diagnostico.append("Boa execução geral mas sem redução de cintura → ajuste fino na dieta")

    if cintura_oficial and delta_cintura_real and delta_cintura_real >= 0:
        diagnostico.append("Cintura não reduziu na semana (base quarta) → revisar déficit/calorias")
        
    # ===== COMPARAÇÃO (VARIÂNCIA) =====
    resumo_anterior = carregar_resumo_anterior()
    variacoes = {}

    if resumo_anterior:
        try:
            score_ant = resumo_anterior.get("geral", {}).get("score_medio")
            if score_ant and score_medio:
                variacoes["score_medio"] = round(score_medio - score_ant, 2)
                
            cintura_ant = resumo_anterior.get("corpo", {}).get("cintura_media")
            if cintura_ant and cintura_media:
                variacoes["cintura_media"] = round(cintura_media - cintura_ant, 2)
                
            passos_ant = resumo_anterior.get("wearable", {}).get("passos_media")
            if passos_ant and passos:
                variacoes["passos_media"] = round(passos - passos_ant, 2)
                
            rhr_ant = resumo_anterior.get("wearable", {}).get("rhr_media")
            if rhr_ant and rhr:
                variacoes["rhr_media"] = round(rhr - rhr_ant, 2)
                
            taxa_exec_ant = resumo_anterior.get("treino", {}).get("taxa_execucao")
            if taxa_exec_ant is not None:
                variacoes["taxa_execucao"] = round(taxa_exec - taxa_exec_ant, 2)
        except Exception:
            pass
    
    # ===== OUTPUT =====
    resumo = {
        "geral": {
            "dias": len(semana),
            "score_medio": score_medio,
            "classificacao": classificar(score_medio)
        },
        "variacoes_vs_semana_anterior": variacoes,
        "corpo": {
            "cintura_oficial_quarta": cintura_oficial,
            "peso_oficial_quarta": peso_oficial,
            "cintura_media": cintura_media,
            "delta_cintura_real": delta_cintura_real
        },
        "habitos": {
            "agua_litros_media": agua,
            "alcool_dias_uso": alcool_dias
        },
        "wearable": {
            "passos_media": passos,
            "rhr_media": rhr,
            "pai_media": pai
        },
        "treino": {
            "taxa_execucao": taxa_exec,
            "completude_media": comp_media,
            "intensidade_media": int_media
        },
        "sono_estado": {
            "horas_media": horas,
            "qualidade_media": qualidade,
            "energia_media": energia,
            "foco_media": foco,
            "estresse_medio": estresse
        },
        "logs_narrativos": {
            "alimentacao": textos_alimentacao,
            "feeling_treino": textos_treino,
            "contexto_obstaculos": textos_contexto
        },
        "core": analise_core,
        "extra": analise_extra,
        "diagnostico": diagnostico
    }

    print(json.dumps(resumo, indent=4, ensure_ascii=False))
    consolidar_semana(resumo)

def get_quarta(semana):
    for d in semana:
        if d["weekday"] == 2:  # quarta
            return d
    return None

if __name__ == "__main__":
    calcular()