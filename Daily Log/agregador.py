import json
import os
from datetime import datetime

PASTA = "Semana"

def carregar_semana():
    arquivos = [f for f in os.listdir(PASTA) if f.endswith(".json")]

    # ordena por nome (YYYYMMDD já ordena certo)
    arquivos.sort()

    dados = []

    for arquivo in arquivos:
        caminho = os.path.join(PASTA, arquivo)
        with open(caminho, "r") as f:
            dados.append(json.load(f))

    return dados

def media(lista):
    lista = [x for x in lista if x is not None]
    return round(sum(lista)/len(lista), 2) if lista else None

def calcular():
    semana = carregar_semana()

    if not semana:
        print("Sem dados na pasta Semana.")
        return

    # ===== CORPO =====
    cinturas = [d.get("cintura") for d in semana if d.get("cintura")]
    cintura_media = media(cinturas)

    cintura_inicio = cinturas[0] if cinturas else None
    cintura_fim = cinturas[-1] if cinturas else None
    delta_cintura = round(cintura_fim - cintura_inicio, 2) if cintura_inicio and cintura_fim else None

    pesos = [d.get("peso") for d in semana if d.get("peso")]
    peso_semana = pesos[0] if pesos else None

    # ===== FISIO =====
    sono = media([d.get("sono") for d in semana])
    bio = media([d.get("biocharge") for d in semana])
    energia = media([d.get("energia") for d in semana])
    joelho = media([d.get("joelho") for d in semana])

    # ===== ALIMENTAÇÃO =====
    total_refeicoes = 0
    refeicoes_ok = 0

    for d in semana:
        for ref in d["alimentacao"].values():
            total_refeicoes += 1
            if ref.lower() == "s":
                refeicoes_ok += 1

    aderencia = round((refeicoes_ok / total_refeicoes) * 100, 2) if total_refeicoes else 0

    # ===== TREINO =====
    planejados = 0
    executados = 0
    remanejados = 0

    for d in semana:
        if d["treino"]["planejado"] != "Descanso":
            planejados += 1
            if d["treino"]["executado"] == "s":
                executados += 1
        if d["treino"]["remanejado"] == "s":
            remanejados += 1

    taxa_execucao = round((executados / planejados) * 100, 2) if planejados else 0

    # ===== SCORE =====
    nota_media = media([d.get("nota") for d in semana])

    resumo = {
        "dias_analisados": len(semana),
        "corpo": {
            "cintura_media": cintura_media,
            "delta_cintura": delta_cintura,
            "peso_semana": peso_semana
        },
        "fisiologico": {
            "sono_medio": sono,
            "biocharge_medio": bio,
            "energia_media": energia,
            "joelho_media": joelho
        },
        "alimentacao": {
            "aderencia_percentual": aderencia
        },
        "treino": {
            "planejados": planejados,
            "executados": executados,
            "taxa_execucao": taxa_execucao,
            "remanejamentos": remanejados
        },
        "geral": {
            "nota_media": nota_media
        }
    }

    print(json.dumps(resumo, indent=4))

if __name__ == "__main__":
    calcular()