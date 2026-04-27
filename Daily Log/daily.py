import json
import os
from datetime import datetime

PASTA = "Semana"

def garantir_pasta():
    if not os.path.exists(PASTA):
        os.makedirs(PASTA)

def salvar_dia(registro):
    hoje_arquivo = datetime.now().strftime("%Y%m%d")
    caminho = os.path.join(PASTA, f"{hoje_arquivo}.json")

    if os.path.exists(caminho):
        print("⚠️ Registro de hoje já existe. Sobrescrevendo...")

    with open(caminho, "w") as f:
        json.dump(registro, f, indent=4)

    print(f"\n✅ Salvo em {caminho}")

def input_float(msg):
    val = input(msg).strip()
    return float(val) if val else None

def input_int(msg):
    val = input(msg).strip()
    return int(val) if val else None

def input_sn(msg):
    val = input(msg).strip().lower()
    return val if val in ["s", "n"] else None

def main():
    garantir_pasta()

    hoje_formatado = datetime.now().strftime("%d/%m/%Y")
    dia_semana = datetime.now().weekday()  # 0=Seg, 6=Dom

    print(f"\n=== LOG DO DIA: {hoje_formatado} ===\n")

    # ===== SONO =====
    sono = input_int("Pontuação do sono: ")
    biocharge = input_int("Biocharge: ")

    # ===== CORPO =====
    energia = input_int("Energia (0-10): ")
    joelho = input_int("Joelho (0-10): ")
    cintura = input_float("Cintura (cm): ")

    peso = None
    if dia_semana == 2:  # quarta
        peso = input_float("Peso (kg): ")

    # ===== ALIMENTAÇÃO =====
    cafe = input_sn("Café da manhã OK? (s/n): ")
    almoco = input_sn("Almoço OK? (s/n): ")
    lanche = input_sn("Lanche OK? (s/n): ")
    jantar = input_sn("Jantar OK? (s/n): ")

    # ===== TREINO =====
    treinos = {
        0: "Upper",
        1: "Corrida",
        2: "Lower",
        4: "Futebol"
    }

    planejado = treinos.get(dia_semana, "Descanso")

    print(f"Treino planejado: {planejado}")
    executado = input_sn("Executou? (s/n): ")

    remanejado = input_sn("Remanejar? (s/n): ")
    justificativa = input("Justificativa: ").strip()

    # ===== RESUMO =====
    nota = input_int("Nota do dia (0-10): ")
    obs = input("Observações: ").strip()

    registro = {
        "data": hoje_formatado,
        "sono": sono,
        "biocharge": biocharge,
        "energia": energia,
        "joelho": joelho,
        "cintura": cintura,
        "peso": peso,
        "alimentacao": {
            "cafe": cafe,
            "almoco": almoco,
            "lanche": lanche,
            "jantar": jantar
        },
        "treino": {
            "planejado": planejado,
            "executado": executado,
            "remanejado": remanejado,
            "justificativa": justificativa
        },
        "nota": nota,
        "obs": obs
    }

    salvar_dia(registro)

if __name__ == "__main__":
    main()