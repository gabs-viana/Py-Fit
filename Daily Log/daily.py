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
    horas = input_horas("Horas de sono: ")
    qualidade = input_int("Qualidade (0-100): ", 0, 100)
    bio_manha = input_int("Biocharge manhã (0-100): ", 0, 100)
    bio_noite = input_int("Biocharge noite (0-100): ", 0, 100)

    # ===== ESTADO =====
    energia = input_int("Energia (0-10): ", 0, 10)
    foco = input_int("Foco (0-10): ", 0, 10)
    estresse = input_int("Estresse (0-100): ", 0, 100)

    # ===== CORPO =====
    cintura = input_float("Cintura (cm) [Enter para pular]: ", opcional=True)
    peso = None
    if dia_semana == 2:
        peso = input_float("Peso (kg) [Enter para pular]: ", opcional=True)

    # ===== HÁBITOS =====
    agua = input_float("Água (Litros): ")
    alcool = input_sn("Consumiu álcool? (s/n): ")

    # ===== WEARABLE (Bip 6) =====
    passos = input_int("Passos: ")
    rhr = input_int("RHR (Batimentos em repouso): ")
    pai = input_int("PAI (Ganho no dia) [Enter para pular]: ", min_val=0, opcional=True)

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
        # Se é descanso, o treino não entra na conta (max 600 base -> vira 1000)
        score_base = s_sono + s_estado
        score_total = int((score_base / 600) * 1000)
    else:
        score_total = s_sono + s_treino + s_estado

    print(f"\n📊 Score do dia: {score_total}/1000")
    print(feedback(score_total))

    registro = {
        "data": data_ref.strftime("%d/%m/%Y"),
        "sono": {
            "horas": horas,
            "qualidade": qualidade,
            "bio_manha": bio_manha,
            "bio_noite": bio_noite
        },
        "estado": {
            "energia": energia,
            "foco": foco,
            "estresse": estresse
        },
        "habitos": {
            "agua_litros": agua,
            "alcool": alcool
        },
        "wearable": {
            "passos": passos,
            "rhr": rhr,
            "pai": pai
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
        "score": score_total
    }

    salvar_dia(registro, data_ref)

if __name__ == "__main__":
    main()