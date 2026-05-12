import json
import os
from datetime import datetime
from datetime import timedelta

# Configuração de caminhos baseados na estrutura real
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PASTA = os.path.join(ROOT_DIR, "Daily Log", "Semana")
REM_FILE = os.path.join(ROOT_DIR, "data", "database", "remanejamentos.json")

def carregar_remanejamentos():
    if not os.path.exists(REM_FILE):
        # Cria o arquivo vazio se não existir para evitar erros
        return {}
    
    with open(REM_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# =========================
# BASE
# =========================
def garantir_pasta():
    if not os.path.exists(PASTA):
        os.makedirs(PASTA)

def salvar_dia(registro, data_ref):
    nome = data_ref.strftime("%Y%m%d")
    caminho = os.path.join(PASTA, f"{nome}.json")

    with open(caminho, "w", encoding='utf-8') as f:
        json.dump(registro, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Salvo em {caminho}")

# =========================
# INPUTS
# =========================
def input_int(msg, min_val=None, max_val=None, opcional=False, default=None):
    if default is not None:
        msg = f"{msg.strip()} [{default}]"
    
    msg = msg.strip() + ": "
    
    while True:
        val = input(msg).strip()
        if val == "" and default is not None:
            return default
        if opcional and val == "":
            return None
        if val.lstrip('-').isdigit():
            val = int(val)
            if (min_val is None or val >= min_val) and (max_val is None or val <= max_val):
                return val
        print("Valor inválido.")

def input_float(msg, opcional=False, default=None):
    if default is not None:
        msg = f"{msg.strip()} [{default}]"
    
    msg = msg.strip() + ": "
    
    while True:
        val = input(msg).strip()
        if val == "" and default is not None:
            return default
        if opcional and val == "":
            return None
        try:
            return float(val)
        except:
            print("Valor inválido.")

def input_horas(msg, default=None):
    if default is not None:
        if isinstance(default, float):
            h = int(default)
            m = int((default - h) * 60)
            default_str = f"{h}:{m:02d}" if m > 0 else f"{h}"
        else:
            default_str = str(default)
        msg = f"{msg.strip()} [{default_str}]"
    
    msg = msg.strip() + ": "

    while True:
        val = input(msg).strip()
        if val == "" and default is not None:
            return float(default)

        try:
            if ":" in val:
                h, m = val.split(":")
                return int(h) + int(m)/60
            else:
                return float(val)
        except:
            print("Formato inválido (use 9.5 ou 9:30)")

def input_sn(msg, default=None):
    if default is not None:
        msg = f"{msg.strip()} [{default}]"
    
    msg = msg.strip() + ": "
    
    while True:
        val = input(msg).strip().lower()
        if val == "" and default is not None:
            return default
        if val in ["s", "n"]:
            return val
        print("Digite 's' ou 'n'.")

def input_text(msg, default=None):
    if default:
        print(f"\n[Atual]: {default}")
        msg = f"{msg.strip()} (Enter para manter): "
    else:
        msg = f"{msg.strip()}: "
    
    val = input(msg).strip()
    if val == "" and default is not None:
        return default
    return val

def carregar_prefill(data_ref):
    # Busca na nova estrutura data/prefill
    caminho = os.path.join(ROOT_DIR, "data", "prefill", "prefill_daily.json")
    
    print(f"DEBUG: Buscando prefill em: {caminho}")
    
    if not os.path.exists(caminho):
        print("DEBUG: Arquivo prefill não encontrado.")
        return {}
    
    try:
        with open(caminho, "r", encoding='utf-8') as f:
            data = json.load(f)
            target_date = data_ref.strftime("%Y-%m-%d")
            if data.get("date") == target_date:
                return data
    except Exception:
        pass

    # Se chegou aqui, não encontrou prefill válido para hoje. 
    # Tenta disparar o builder automaticamente (Auto-Sustentável)
    print(f"\n🔄 Dados de {data_ref.strftime('%d/%m/%Y')} não encontrados localmente.")
    print("🚀 Disparando extração automática da Zepp Cloud...")
    
    import subprocess
    import sys
    builder_path = os.path.join(ROOT_DIR, "src", "ingestion", "auto_daily_builder.py")
    try:
        subprocess.run([sys.executable, builder_path, data_ref.strftime("%Y-%m-%d")], cwd=ROOT_DIR)
        # Tenta carregar novamente após o builder rodar
        with open(caminho, "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Falha na extração automática: {e}")
        
    return {}

def merge_prefill(registro, prefill):
    """Integra os dados do prefill no registro do daily.py"""
    if not prefill:
        return registro
        
    # Sono
    if "sleep" in prefill:
        s = prefill["sleep"]
        registro["sono"]["horas"] = s.get("total_hours", registro["sono"]["horas"])
        registro["sono"]["rem_min"] = int(s.get("rem_sleep_pct", 0) * s.get("total_hours", 0) * 0.6) # Aproximação
        registro["sono"]["profundo_min"] = int(s.get("deep_sleep_pct", 0) * s.get("total_hours", 0) * 0.6)
        
    # Wearable / Biometrics
    if "biometrics" in prefill:
        b = prefill["biometrics"]
        registro["wearable"]["passos"] = b.get("steps", registro["wearable"]["passos"])
        registro["wearable"]["rhr"] = b.get("rhr", registro["wearable"]["rhr"])
        registro["wearable"]["hrv_ms"] = b.get("hrv", registro["wearable"]["hrv_ms"])
        registro["wearable"]["pai"] = b.get("pai", registro["wearable"]["pai"])
        registro["wearable"]["calorias_ativas"] = b.get("calories", registro["wearable"]["calorias_ativas"])
        registro["corpo"]["peso"] = b.get("weight", registro["corpo"]["peso"])
        
    # Estado
    if "readiness_index" in prefill:
        registro["estado"]["readiness_score"] = prefill["readiness_index"].get("score")
        
    # Habitos
    if "nutrition" in prefill:
        registro["habitos"]["agua_litros"] = prefill["nutrition"].get("water_litros", registro["habitos"]["agua_litros"])
        registro["alimentacao"]["descricao"] = "\n".join(prefill["nutrition"].get("meal_logs", []))
        
    # Performance (TSB / ACWR / Forecast)
    if "longitudinal" in prefill:
        l = prefill["longitudinal"]
        tsb = l.get("tsb", {})
        forecast = l.get("forecast", {})
        
        registro["performance"] = {
            "tsb": tsb.get("tsb"),
            "acwr": tsb.get("acwr"),
            "status": tsb.get("status"),
            "max_safe_load": forecast.get("max_safe_load_tomorrow"),
            "peak_day": 5 # Simplificado
        }
        
    return registro

# =========================
# SCORE
# =========================
def score_sono(horas, qualidade, bio_manha):
    pts = 0

    if horas and horas >= 7: pts += 140
    elif horas and horas >= 6: pts += 100
    else: pts += 60

    qual = qualidade if qualidade is not None else 70
    bio = bio_manha if bio_manha is not None else 70

    pts += qual * 1.1   # até 110 pts
    pts += bio * 1.0   # até 100 pts

    return min(350, int(pts))

def score_treino(exec, completude, intensidade):
    if exec == "n":
        return 0

    pts = 0
    pts += completude * 2.0      # até 200
    pts += intensidade * 20      # até 200

    return min(400, int(pts))

def score_estado(readiness_score, estresse):
    r_val = readiness_score if readiness_score is not None else 70
    e_val = estresse if estresse is not None else 50
    pts = (r_val * 1.5) + (100 - e_val)
    return min(250, int(pts))

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

# =========# =========================
# REVISÃO E EDIÇÃO
# =========================
def exibir_revisao(registro):
    print("\n" + "="*40)
    print("      📋 REVISÃO DOS DADOS DO DIA")
    print("="*40)
    
    indices = []
    
    # Grupos de dados para exibição organizada
    grupos = [
        ("💤 SONO", [
            ("Horas", f"{int(registro['sono']['horas'])}h{int((registro['sono']['horas'] % 1) * 60):02d}" if registro['sono']['horas'] else "0h00"),
            ("Qualidade", registro["sono"].get("qualidade", "N/A")),
            ("Bio Manhã", registro["sono"].get("bio_manha", "N/A")),
            ("Bio Noite", registro["sono"].get("bio_noite", "N/A")),
            ("REM (min)", registro["sono"].get("rem_min", "N/A")),
            ("Profundo (min)", registro["sono"].get("profundo_min", "N/A")),
        ]),
        ("⚡ ESTADO", [
            ("Readiness", registro["estado"].get("readiness_score", "N/A")),
            ("Estresse", registro["estado"].get("estresse", "N/A")),
        ]),
        ("⌚ WEARABLE", [
            ("Passos", registro["wearable"]["passos"]),
            ("RHR", registro["wearable"]["rhr"]),
            ("PAI", registro["wearable"]["pai"]),
            ("HRV (ms)", registro["wearable"]["hrv_ms"]),
            ("Calorias", registro["wearable"]["calorias_ativas"]),
        ]),
        ("📈 PERFORMANCE", [
            ("TSB (Balance)", registro["performance"].get("tsb", "N/A")),
            ("ACWR (Risco)", registro["performance"].get("acwr", "N/A")),
            ("Status", registro["performance"].get("status", "N/A")),
        ]),
        ("🔮 PREDIÇÃO", [
            ("Limite Amanhã", f"{registro['performance'].get('max_safe_load', 'N/A')} Carga"),
            ("Pico Frescor", f"Em {registro['performance'].get('peak_day', 'N/A')} dias"),
        ]),
        ("📐 CORPO/HÁBITOS", [
            ("Peso", f"{registro['corpo']['peso']} kg" if registro["corpo"]["peso"] else "Não pesado"),
            ("Cintura", registro["corpo"]["cintura"]),
            ("Água", registro["habitos"]["agua_litros"]),
        ]),
        ("🏋️ TREINO", [
            ("Executado", registro["treino"]["executado"]),
        ] + ([
            ("Completude", registro["treino"]["completude"]),
            ("Intensidade", registro["treino"]["intensidade"]),
        ] if registro["treino"]["planejado"] != "Descanso" else [])),
        ("📝 CONTEXTO", [
            ("Alimentação", registro["alimentacao"]["descricao"][:50] + "..." if len(registro["alimentacao"]["descricao"]) > 50 else registro["alimentacao"]["descricao"]),
            ("Obstáculo", registro["contexto"][:50] + "..." if len(registro["contexto"]) > 50 else registro["contexto"]),
        ])
    ]

    idx = 1
    mapping = {}
    
    for titulo, campos in grupos:
        print(f"\n{titulo}")
        for label, valor in campos:
            print(f"  {idx:2d}. {label:15}: {valor}")
            mapping[idx] = (titulo, label)
            idx += 1
    
    print("\n" + "="*40)
    print(" 0. ✅ CONFIRMAR TUDO E SALVAR")
    print("="*40)
    return mapping

def editar_campo(idx, mapping, registro):
    if idx not in mapping:
        return
    
    titulo, label = mapping[idx]
    print(f"\nEditando [{label}]...")
    
    if label == "Horas": registro["sono"]["horas"] = input_horas("Novo valor", default=registro["sono"]["horas"])
    elif label == "Bio Manhã": registro["sono"]["bio_manha"] = input_int("Novo Bio Manhã", 0, 100, default=registro["sono"]["bio_manha"])
    elif label == "REM (min)": registro["sono"]["rem_min"] = input_int("Novo REM", 0, 500, default=registro["sono"]["rem_min"])
    elif label == "Profundo (min)": registro["sono"]["profundo_min"] = input_int("Novo Profundo", 0, 500, default=registro["sono"]["profundo_min"])
    elif label == "Estresse": registro["estado"]["estresse"] = input_int("Novo Estresse", 0, 100, default=registro["estado"]["estresse"])
    elif label == "Passos": registro["wearable"]["passos"] = input_int("Novos Passos", 0, 100000, default=registro["wearable"]["passos"])
    elif label == "RHR": registro["wearable"]["rhr"] = input_int("Novo RHR", 30, 200, default=registro["wearable"]["rhr"])
    elif label == "PAI": registro["wearable"]["pai"] = input_float("Novo PAI", default=registro["wearable"]["pai"])
    elif label == "HRV (ms)": registro["wearable"]["hrv_ms"] = input_int("Novo HRV", 0, 200, default=registro["wearable"]["hrv_ms"])
    elif label == "Calorias": registro["wearable"]["calorias_ativas"] = input_int("Novas Calorias", 0, 5000, default=registro["wearable"]["calorias_ativas"])
    elif label == "Peso": registro["corpo"]["peso"] = input_float("Novo Peso", default=registro["corpo"]["peso"])
    elif label == "Cintura": registro["corpo"]["cintura"] = input_float("Nova Cintura", default=registro["corpo"]["cintura"])
    elif label == "Água": registro["habitos"]["agua_litros"] = input_float("Nova Água", default=registro["habitos"]["agua_litros"])
    elif label == "Executado": registro["treino"]["executado"] = input_sn("Executou? (s/n)", default=registro["treino"]["executado"])
    elif label == "Completude": registro["treino"]["completude"] = input_int("Nova Completude", 0, 100, default=registro["treino"]["completude"])
    elif label == "Intensidade": registro["treino"]["intensidade"] = input_int("Nova Intensidade", 0, 10, default=registro["treino"]["intensidade"])
    elif label == "Alimentação": registro["alimentacao"]["descricao"] = input_text("Nova descrição", default=registro["alimentacao"]["descricao"])
    elif label == "Obstáculo": registro["contexto"] = input_text("Novo obstáculo", default=registro["contexto"])


# =========================
# MAIN
# =========================
def main():
    garantir_pasta()

    data_ref = escolher_data()
    prefill = carregar_prefill(data_ref)
    dia_semana = data_ref.weekday()

    print(f"\n=== LOG ATLETA — {data_ref.strftime('%d/%m/%Y')} ===\n")

    # FORECASTING (Módulo TSB)
    try:
        import sys
        sys.path.append(ROOT_DIR)
        from src.analysis.forecasting_engine import ForecastingEngine
        engine = ForecastingEngine(ROOT_DIR)
        previsoes = engine.prever_proximos_dias(dias=3)
        if previsoes:
            print("📈 FORECAST (TSB - Próximos dias):")
            for p in previsoes:
                print(f"  [{p['data']}] TSB: {p['tsb']:>5} -> {p['status']}")
            print()
            
        # Exibe TSB de HOJE (via prefill)
        tsb_hoje = l_data.get("tsb", {})
        if tsb_hoje:
            print(f"📊 STATUS DE HOJE (TSB): {tsb_hoje.get('tsb')} -> {tsb_hoje.get('status')}")
            if tsb_hoje.get("acwr", 0) > 1.5:
                print("🚨 CUIDADO: ACWR acima de 1.5! Risco agudo de fadiga.")
            print()
    except Exception as e:
        print(f"⚠️ Módulo de Forecasting indisponível: {e}\n")

    # PREPARAÇÃO DOS DADOS (Prefill + Defaults)
    s_data = prefill.get("sleep", {})
    b_data = prefill.get("biometrics", {})
    l_data = prefill.get("longitudinal", {})

    # ALERTAS DE FADIGA / OVERTRAINING
    signatures = l_data.get("fatigue_signatures", [])
    if signatures:
        treinos_base = {0: "Upper", 1: "Corrida", 2: "Lower", 4: "Futebol"}
        amanha_weekday = (data_ref.weekday() + 1) % 7
        treino_amanha = treinos_base.get(amanha_weekday, "Descanso")
        
        print("⚠️ ALERTAS FISIOLÓGICOS (Foco em Amanhã):")
        for sig in signatures:
            print(f"  - {sig}")
        
        if treino_amanha != "Descanso":
            print(f"  > Treino planejado para amanhã: {treino_amanha}. Avalie a intensidade com base no alerta!\n")
        else:
            print(f"  > Amanhã é dia de Descanso. Aproveite para absorver a carga!\n")
    
    p_hrs = s_data.get("total_hours")
    p_rhr = b_data.get("rhr")
    p_hrv = b_data.get("hrv")
    p_stress = b_data.get("stress")
    p_passos = b_data.get("steps")
    p_cal = b_data.get("calories")
    p_pai = b_data.get("pai")
    p_peso = b_data.get("weight")
    p_bio_start = b_data.get("biocharge_waking")
    p_bio_current = b_data.get("biocharge_current")
    p_sleep_score = s_data.get("score")
    p_readiness_score = prefill.get("readiness_index", {}).get("score")
    
    total_min = p_hrs * 60 if p_hrs else 0
    p_rem_min = int(total_min * (s_data.get("rem_sleep_pct", 0)/100)) if total_min else None
    p_deep_min = int(total_min * (s_data.get("deep_sleep_pct", 0)/100)) if total_min else None
    p_light_min = int(total_min * (s_data.get("light_sleep_pct", 0)/100)) if total_min else None

    # 1. PERGUNTAS MANUAIS (O que a Zepp não sabe)
    print("\n--- ⚡ HÁBITOS & MANUAIS ---")
    
    p_agua = nutri_prefill.get("water_litros", 0)
    if p_agua > 0:
        print(f"💧 Água detectada na Zepp: {p_agua}L")
        agua = p_agua
    else:
        agua = input_float("Água (Litros)")
        
    cintura = input_float("Cintura (cm) [Enter para pular]", opcional=True)
    
    print("\n--- 🥗 ALIMENTAÇÃO ---")
    nutri_prefill = prefill.get("nutrition", {})
    logs_zepp = nutri_prefill.get("meal_logs", [])
    if logs_zepp:
        print("✅ Logs detectados na Zepp Cloud (usando automação).")
        alimentacao_texto = " | ".join(logs_zepp)
    else:
        alimentacao_texto = input("Descreva sua alimentação (Vazio para pular): ").strip()

    # 2. TREINO
    print("\n--- 🏋️ TREINO ---")
    treinos_base = {0: "Upper", 1: "Corrida", 2: "Lower", 4: "Futebol"}
    
    remanejamentos = carregar_remanejamentos()
    chave_hoje = data_ref.strftime("%Y%m%d")
    if chave_hoje in remanejamentos:
        planejado = remanejamentos[chave_hoje]["treino"]
        print(f"🔄 Treino Remanejado detectado para hoje: {planejado}")
    else:
        planejado = treinos_base.get(dia_semana, "Descanso")
    
    # Check Workout Prefill
    w_detected = b_data.get("workout_detected", False)
    w_info = b_data.get("workout_info", {})
    
    if w_detected:
        print(f"✅ Treino Detectado: {w_info.get('type_name')} ({w_info.get('duration_min')} min)")
        print(f"🔥 Carga capturada: {w_info.get('load')} (Zepp Load)")
        executado = "s"
        # Mapeamento automático de Carga para Completude/Intensidade (para manter compatibilidade de score)
        # Se a carga é capturada, a completude é 100%. A intensidade é derivada do load (máximo 10).
        completude = 100
        intensidade = min(10, round(w_info.get("load", 0) / 10)) if w_info.get("load") else 7
        feeling_treino = input("Feeling do treino (Enter para pular): ").strip()
    else:
        print(f"Planejado: {planejado}")
        if planejado == "Descanso":
            executado, completude, intensidade = "n", 0, 0
            feeling_treino = ""
        else:
            executado = input_sn("Executou? (s/n)")
            if executado == "s":
                completude = input_int("Completude (%)", 0, 100)
                intensidade = input_int("Intensidade (0-10)", 0, 10)
                feeling_treino = input("Feeling do treino (Enter para pular): ").strip()
            else:
                completude, intensidade = 0, 0
                feeling_treino = ""
                remanejar = input_sn("Deseja remanejar este treino? (s/n)", default="s")
                if remanejar == "s":
                    dia_destino = escolher_dia_remanejamento(data_ref)
                    salvar_remanejamento(dia_destino, planejado, data_ref)

    obstaculo_dia = input("Obstáculo/Vitória do dia: ").strip()

    # MONTAGEM DO REGISTRO INICIAL
    registro = {
        "data": data_ref.strftime("%d/%m/%Y"),
        "sono": {
            "horas": p_hrs, "qualidade": p_sleep_score, 
            "bio_manha": p_bio_start, "bio_noite": p_bio_current,
            "rem_min": p_rem_min, "profundo_min": p_deep_min, "leve_min": p_light_min
        },
        "estado": {"readiness_score": p_readiness_score, "estresse": p_stress},
        "habitos": {"agua_litros": agua},
        "wearable": {
            "passos": p_passos, "rhr": p_rhr, "pai": round(p_pai, 1) if p_pai else 0,
            "hrv_ms": p_hrv, "calorias_ativas": p_cal, "sport_load": b_data.get("sport_load")
        },
        "corpo": {"cintura": cintura, "peso": p_peso},
        "performance": {}, # Inicializa performance
        "alimentacao": {"descricao": alimentacao_texto},
        "treino": {
            "planejado": planejado, "executado": executado, 
            "completude": completude, "intensidade": intensidade, "feeling": feeling_treino
        },
        "contexto": obstaculo_dia
    }

    # Integra automações da Zepp e Longitudinal Engine
    registro = merge_prefill(registro, prefill)

    # 3. LOOP DE REVISÃO E EDIÇÃO
    while True:
        mapping = exibir_revisao(registro)
        escolha = input("\nDigite o ID para editar ou 0 para SALVAR: ").strip()
        
        if escolha == "0":
            break
        
        if escolha.isdigit():
            editar_campo(int(escolha), mapping, registro)
        else:
            print("Opção inválida.")

    # FINALIZAÇÃO (Cálculo de Scores e Salvamento)
    s_sono = score_sono(registro["sono"]["horas"], registro["sono"].get("qualidade"), registro["sono"].get("bio_manha"))
    s_treino = score_treino(registro["treino"]["executado"], registro["treino"]["completude"], registro["treino"]["intensidade"])
    s_estado = score_estado(registro["estado"].get("readiness_score"), registro["estado"].get("estresse"))
    
    if registro["treino"]["planejado"] == "Descanso":
        score_total = int(((s_sono + s_estado) / 600) * 1000)
    else:
        score_total = s_sono + s_treino + s_estado
    
    registro["score"] = score_total
    registro["readiness"] = prefill.get("readiness_index", {}).get("score")
    
    print(f"\n📊 Score Final: {score_total}/1000")
    print(feedback(score_total))
    
    salvar_dia(registro, data_ref)

if __name__ == "__main__":
    main()