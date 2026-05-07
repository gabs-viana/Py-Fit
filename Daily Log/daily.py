import json
import os
from datetime import datetime
from datetime import timedelta

REM_FILE = "remanejamentos.json"

def carregar_remanejamentos():
    if not os.path.exists(REM_FILE):
        return {}
    
    with open(REM_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

PASTA = "Semana"

# =========================
# BASE
# =========================
def garantir_pasta():
    if not os.path.exists(PASTA):
        os.makedirs(PASTA)

def salvar_dia(registro, data_ref):
    nome = data_ref.strftime("%Y%m%d")
    caminho = os.path.join(PASTA, f"{nome}.json")

    with open(caminho, "w") as f:
        json.dump(registro, f, indent=4)

    print(f"\n✅ Salvo em {caminho}")

# =========================
# INPUTS
# =========================
def input_int(msg, min_val=None, max_val=None, opcional=False):
    while True:
        val = input(msg).strip()
        if opcional and val == "":
            return None
        if val.isdigit():
            val = int(val)
            if (min_val is None or val >= min_val) and (max_val is None or val <= max_val):
                return val
        print("Valor inválido.")

def input_float(msg, opcional=False):
    while True:
        val = input(msg).strip()
        if opcional and val == "":
            return None
        try:
            return float(val)
        except:
            print("Valor inválido.")

def input_horas(msg):
    while True:
        val = input(msg).strip()

        try:
            if ":" in val:
                h, m = val.split(":")
                return int(h) + int(m)/60
            else:
                return float(val)
        except:
            print("Formato inválido (use 9.5 ou 9:30)")

def input_sn(msg):
    while True:
        val = input(msg).strip().lower()
        if val in ["s", "n"]:
            return val
        print("Digite 's' ou 'n'.")

# =========================
# SCORE
# =========================
def score_sono(horas, qualidade, bio_manha):
    pts = 0

    if horas >= 7: pts += 140
    elif horas >= 6: pts += 100
    else: pts += 60

    pts += qualidade * 1.1   # até 110 pts
    pts += bio_manha * 1.0   # até 100 pts

    return min(350, int(pts))

def score_treino(exec, completude, intensidade):
    if exec == "n":
        return 0

    pts = 0
    pts += completude * 2.0      # até 200
    pts += intensidade * 20      # até 200

    return min(400, int(pts))

def score_estado(energia, foco, estresse):
    pts = (energia * 10) + (foco * 10) + ((100 - estresse) * 0.5)
    return min(250, pts)

# =========================
# READINESS INDEX V6
# =========================
# Pesos: HRV 45%, RHR 25%, Sono Profundo 20%, Estresse 10%
RHR_REF = 55  # Sua baseline pessoal de RHR

def calcular_readiness(hrv, rhr, sono_profundo_min, sono_total_min, estresse):
    """
    Calcula Readiness Index (0-100) baseado em sinais vitais do Bip 6.
    Retorna None se não houver HRV disponível.
    """
    if hrv is None:
        return None
    
    # HRV Score (45%) — Baseline ~40ms, excelente ~80ms+
    hrv_score = min(100, max(0, (hrv / 80) * 100))
    
    # RHR Score (25%) — Quanto mais baixo vs. referência, melhor
    if rhr is not None:
        rhr_delta = RHR_REF - rhr  # positivo = abaixo da ref = bom
        rhr_score = min(100, max(0, 70 + (rhr_delta * 5)))
    else:
        rhr_score = 50  # neutro
    
    # Sono Profundo Score (20%) — Ideal: >20% do tempo total
    if sono_profundo_min is not None and sono_total_min and sono_total_min > 0:
        pct_profundo = (sono_profundo_min / sono_total_min) * 100
        profundo_score = min(100, max(0, pct_profundo * 5))  # 20% = 100
    else:
        profundo_score = 50  # neutro
    
    # Estresse Score (10%) — Quanto menor, melhor
    if estresse is not None:
        stress_score = max(0, 100 - estresse)
    else:
        stress_score = 50  # neutro
    
    readiness = (
        hrv_score * 0.45 +
        rhr_score * 0.25 +
        profundo_score * 0.20 +
        stress_score * 0.10
    )
    
    return round(readiness, 1)

# =========================
# FEEDBACK
# =========================
def feedback(score):
    if score >= 850:
        return "🔥 Elite absoluta"
    elif score >= 700:
        return "🚀 Muito forte"
    elif score >= 550:
        return "✅ Bom dia"
    elif score >= 400:
        return "⚠️ Regular"
    else:
        return "🚨 Abaixo do esperado"

def semana_atual_datas():
    hoje = datetime.now()
    inicio = hoje - timedelta(days=hoje.weekday())  # segunda

    return [inicio + timedelta(days=i) for i in range(7)]

def dias_pendentes():
    datas = semana_atual_datas()
    existentes = set(os.listdir(PASTA))

    pendentes = []

    for d in datas:
        nome = d.strftime("%Y%m%d.json")
        if nome not in existentes:
            pendentes.append(d)

    return pendentes

def escolher_data_manual():
    while True:
        val = input("Digite a data (YYYY-MM-DD): ").strip()
        try:
            return datetime.strptime(val, "%Y-%m-%d")
        except:
            print("Formato inválido.")

def escolher_data():
    hoje_str = datetime.now().strftime("%Y%m%d")
    pendentes_todos = dias_pendentes()
    
    # Filtra 'Hoje' da lista de pendentes para não duplicar com a opção 0
    pendentes = [d for d in pendentes_todos if d.strftime("%Y%m%d") != hoje_str]

    print("\nOpções de data:")
    if pendentes:
        print("Dias pendentes da semana:")
        for i, d in enumerate(pendentes):
            print(f"{i+1} - {d.strftime('%A %d/%m')}")

    print("0 - Hoje")
    print("9 - Escolher manual")

    while True:
        val = input("Escolha: ").strip()

        if val == "0":
            return datetime.now()

        if val == "9":
            return escolher_data_manual()

        if pendentes and val.isdigit() and 1 <= int(val) <= len(pendentes):
            return pendentes[int(val)-1]
            
        print("Opção inválida.")


def dias_restantes(data_ref):
    dias = []
    for i in range(1, 7 - data_ref.weekday()):
        dias.append(data_ref + timedelta(days=i))
    return dias

def verificar_treino_existente(data_destino):
    nome = data_destino.strftime("%Y%m%d")
    caminho = os.path.join(PASTA, f"{nome}.json")

    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            d = json.load(f)
            return d.get("treino", {}).get("planejado")
    
    return None


def salvar_remanejamento(data_destino, treino, data_origem):
    dados = carregar_remanejamentos()
    chave = data_destino.strftime("%Y%m%d")

    dados[chave] = {
        "treino": treino,
        "origem": data_origem.strftime("%Y%m%d")
    }

    with open(REM_FILE, "w") as f:
        json.dump(dados, f, indent=4)

    print(f"\n🔁 Remanejado para {data_destino.strftime('%d/%m')}")

def escolher_dia_remanejamento(data_ref):
    dias = dias_restantes(data_ref)

    print("\nDias disponíveis para remanejar:")

    for i, d in enumerate(dias):
        print(f"{i+1} - {d.strftime('%A %d/%m')}")

    while True:
        escolha = input("Escolha o dia: ")
        if escolha.isdigit() and 1 <= int(escolha) <= len(dias):
            return dias[int(escolha)-1]
        print("Opção inválida.")

# =========================
# MAIN
# =========================
def main():
    garantir_pasta()

    data_ref = escolher_data()
    dia_semana = data_ref.weekday()

    print(f"\n=== LOG ATLETA — {data_ref.strftime('%d/%m/%Y')} ===\n")

    # ===== SONO =====
    print("\n--- 💤 SONO ---")
    horas = input_horas("Horas de sono: ")
    qualidade = input_int("Qualidade (0-100): ", 0, 100)
    bio_manha = input_int("Biocharge manhã (0-100): ", 0, 100)
    bio_noite = input_int("Biocharge noite (0-100): ", 0, 100)
    sono_rem = input_int("Sono REM (min) [Enter para pular]: ", min_val=0, opcional=True)
    sono_profundo = input_int("Sono Profundo (min) [Enter para pular]: ", min_val=0, opcional=True)
    sono_leve = input_int("Sono Leve (min) [Enter para pular]: ", min_val=0, opcional=True)

    # ===== ESTADO =====
    print("\n--- ⚡ ESTADO ---")
    energia = input_int("Energia (0-10): ", 0, 10)
    foco = input_int("Foco (0-10): ", 0, 10)
    estresse = input_int("Estresse médio do dia (0-100): ", 0, 100)

    # ===== CORPO =====
    print("\n--- 📐 CORPO ---")
    cintura = input_float("Cintura (cm) [Enter para pular]: ", opcional=True)
    peso = None
    if dia_semana == 2:
        peso = input_float("Peso (kg) [Enter para pular]: ", opcional=True)

    # ===== HÁBITOS =====
    print("\n--- 💧 HÁBITOS ---")
    agua = input_float("Água (Litros): ")

    # ===== WEARABLE (Amazfit Bip 6 — BioTracker 6.0) =====
    print("\n--- ⌚ WEARABLE (Bip 6) ---")
    passos = input_int("Passos: ")
    rhr = input_int("RHR (Batimentos em repouso): ")
    pai = input_int("PAI (Ganho no dia) [Enter para pular]: ", min_val=0, opcional=True)
    hrv = input_int("HRV (ms) [Enter para pular]: ", min_val=0, opcional=True)
    calorias_ativas = input_int("Calorias Ativas [Enter para pular]: ", min_val=0, opcional=True)

    # ===== ALIMENTAÇÃO =====
    print("\nAlimentação do dia:")
    alimentacao_texto = input("Descreva tudo que comeu hoje: ").strip()

    # ===== TREINO =====
    treinos = {
        0: "Upper",
        1: "Corrida",
        2: "Lower",
        4: "Futebol"
    }

    remanejamentos = carregar_remanejamentos()
    chave_hoje = data_ref.strftime("%Y%m%d")
    remanejado = "n"

    if chave_hoje in remanejamentos:
        planejado = remanejamentos[chave_hoje]["treino"]
        print(f"Treino planejado (remanejado): {planejado}")
        
        del remanejamentos[chave_hoje]

        with open(REM_FILE, "w") as f:
            json.dump(remanejamentos, f, indent=4)
            
    else:
        planejado = treinos.get(dia_semana, "Descanso")
        print(f"Treino planejado: {planejado}")

    if planejado == "Descanso":
        executado = "n"
        completude = 0
        intensidade = 0
        remanejado = "n"
        justificativa = ""
        feeling_treino = ""
        print("Dia de descanso — sem treino.")
    else:
        executado = input_sn("Executou? (s/n): ")

        if executado == "s":
            completude = input_int("Completude (%) 0-100: ", 0, 100)
            intensidade = input_int("Intensidade (0-10): ", 0, 10)
            remanejado = "n"
            justificativa = ""
            feeling_treino = input("Como se sentiu no treino? (Enter para pular): ").strip()
        else:
            completude = 0
            intensidade = 0
            remanejado = input_sn("Remanejar? (s/n): ")
            justificativa = input("Justificativa: ")
            feeling_treino = ""

    if planejado != "Descanso" and remanejado == "s":
        dias_disp = dias_restantes(data_ref)
        if not dias_disp:
            print("\n⚠️ Domingo é o último dia da semana. Não há para onde remanejar!")
            remanejado = "n"
        else:
            destino = escolher_dia_remanejamento(data_ref)
            chave_destino = destino.strftime("%Y%m%d")
            cancelar = False

            # Verifica se já há remanejamento lá
            if chave_destino in remanejamentos:
                treino_agendado = remanejamentos[chave_destino]["treino"]
                print(f"⚠️ Já existe um remanejamento para esse dia ({treino_agendado}).")
                opc = input("Deseja sobrescrever? (s/n): ").strip().lower()
                if opc != "s":
                    print("Remanejamento cancelado.")
                    cancelar = True

            if not cancelar:
                treino_existente = verificar_treino_existente(destino)

                # Se não há json criado para o dia, checa se há um treino padrão para o dia da semana
                if treino_existente is None:
                    treino_existente = treinos.get(destino.weekday(), "Descanso")

                # Verifica se existe um treino real (que não seja Descanso)
                if treino_existente and treino_existente != "Descanso":
                    print(f"⚠️ Já existe treino ({treino_existente}) nesse dia.")
                    print(f"Você está tentando mover: {planejado}")
                    
                    opc = input("Deseja substituir? (s/n): ").strip().lower()
                    if opc != "s":
                        print("Remanejamento cancelado.")
                    else:
                        salvar_remanejamento(destino, planejado, data_ref)

                else:
                    salvar_remanejamento(destino, planejado, data_ref)

    # ===== CONTEXTO DO DIA =====
    obstaculo_dia = input("\nPrincipal obstáculo ou vitória do dia (Enter para pular): ").strip()

    # ===== SCORE =====
    s_sono = score_sono(horas, qualidade, bio_manha)
    s_treino = score_treino(executado, completude, intensidade)
    s_estado = score_estado(energia, foco, estresse)

    if planejado == "Descanso":
        score_base = s_sono + s_estado
        score_total = int((score_base / 600) * 1000)
    else:
        score_total = s_sono + s_treino + s_estado

    # ===== READINESS INDEX V6 =====
    sono_total_min = int(horas * 60) if horas else None
    readiness = calcular_readiness(hrv, rhr, sono_profundo, sono_total_min, estresse)

    print(f"\n📊 Score do dia: {score_total}/1000")
    print(feedback(score_total))
    if readiness is not None:
        if readiness >= 75:
            r_label = "🟢 PRONTO"
        elif readiness >= 50:
            r_label = "🟡 ALERTA"
        else:
            r_label = "🔴 RECUPERAR"
        print(f"🧬 Readiness Index: {readiness}/100 — {r_label}")

    registro = {
        "data": data_ref.strftime("%d/%m/%Y"),
        "sono": {
            "horas": horas,
            "qualidade": qualidade,
            "bio_manha": bio_manha,
            "bio_noite": bio_noite,
            "rem_min": sono_rem,
            "profundo_min": sono_profundo,
            "leve_min": sono_leve
        },
        "estado": {
            "energia": energia,
            "foco": foco,
            "estresse": estresse
        },
        "habitos": {
            "agua_litros": agua
        },
        "wearable": {
            "passos": passos,
            "rhr": rhr,
            "pai": pai,
            "hrv_ms": hrv,
            "calorias_ativas": calorias_ativas
        },
        "corpo": {
            "cintura": cintura,
            "peso": peso
        },
        "alimentacao": {
            "descricao": alimentacao_texto
        },
        "treino": {
            "planejado": planejado,
            "executado": executado,
            "completude": completude,
            "intensidade": intensidade,
            "remanejado": remanejado,
            "justificativa": justificativa,
            "feeling": feeling_treino
        },
        "contexto": obstaculo_dia,
        "score": score_total,
        "readiness": readiness
    }

    salvar_dia(registro, data_ref)

if __name__ == "__main__":
    main()