import os
import glob
import json
import shutil
from datetime import datetime
import statistics
from fitparse import FitFile
import urllib.request
import urllib.error

IDADE = 19
PESO_KG = 64
ALTURA_M = 1.65
FC_MAX_TEO = 220 - IDADE
CAD_CORRIDA = 75

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def media(l):
    return sum(l) / len(l) if l else None

def fetch_weather(lat, lon, dt):
    """
    Busca as condições climáticas na hora da corrida usando a Open-Meteo API.
    """
    if lat is None or lon is None or dt is None:
        return None
        
    date_str = dt.strftime("%Y-%m-%d")
    hour = dt.hour
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if "hourly" in data:
                    hourly = data["hourly"]
                    times = hourly.get("time", [])
                    target_time = f"{date_str}T{hour:02d}:00"
                    
                    try:
                        idx = times.index(target_time)
                        return {
                            "temperatura_c": hourly["temperature_2m"][idx],
                            "umidade_pct": hourly["relative_humidity_2m"][idx],
                            "precipitacao_mm": hourly["precipitation"][idx],
                            "vento_kmh": hourly["wind_speed_10m"][idx]
                        }
                    except ValueError:
                        return None
    except Exception as e:
        print(f"  [Aviso] Não foi possível buscar o clima: {e}")
        return None
    return None

def fetch_elevation_profile(lats, lons):
    """ Busca altimetria de uma lista de coordenadas na Open-Meteo. """
    if not lats or not lons or len(lats) != len(lons):
        return None
    lat_str = ",".join(f"{lat:.5f}" for lat in lats)
    lon_str = ",".join(f"{lon:.5f}" for lon in lons)
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat_str}&longitude={lon_str}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("elevation")
    except Exception as e:
        print(f"  [Aviso] Erro ao buscar elevação: {e}")
    return None

def classificar_treino(dist_km, tempo_s, blocos, fc_media, pct_corrida):
    if pct_corrida is None or pct_corrida < 0.5:
        return "caminhada"
        
    corridas = [b for b in blocos if b["tipo"] == "corrida"]
    if len(corridas) > 5 and len(blocos) > 10:
        return "intervalado/fartlek"
        
    if tempo_s > 3600 and dist_km > 10:
        return "longão"
        
    if fc_media and fc_media > 155:
        return "tempo run"
        
    if fc_media and fc_media < 135:
        return "recovery run"
        
    return "corrida base"

def estimar_sudorese(peso, tempo_s, temperatura, umidade, fc_media):
    """ Estima a perda de líquidos em ml """
    if not temperatura or not umidade or not tempo_s:
        return None
    
    horas = tempo_s / 3600.0
    taxa_base_ml = peso * 10 
    fator_temp = max(0, (temperatura - 20) * 0.02)
    fator_intensidade = (fc_media / 150.0) if fc_media else 1.0
    fator_umidade = 1.0 + (umidade / 100.0 * 0.1)
    
    suor_total = (taxa_base_ml * fator_intensidade) * (1 + fator_temp) * fator_umidade * horas
    return round(suor_total)

def process_fit(filepath):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processando: {os.path.basename(filepath)}...")
    try:
        fitfile = FitFile(filepath)
    except Exception as e:
        print(f"Erro ao ler {filepath}: {e}")
        return

    dados = []
    
    # =========================
    # 1. EXTRAÇÃO OTIMIZADA
    # =========================
    lat_start = None
    lon_start = None

    # Lemos mantendo os objetos datetime nativos.
    try:
        records = list(fitfile.get_messages('record'))
    except Exception as e:
        print(f"  [Erro] Arquivo corrompido ou vazio (falha da Amazfit/Zepp): {e}")
        return

    for record in records:
        row = {}
        for d in record:
            row[d.name] = d.value
        
        if lat_start is None and row.get("position_lat") is not None and row.get("position_long") is not None:
            lat_start = row.get("position_lat") * (180.0 / (2**31))
            lon_start = row.get("position_long") * (180.0 / (2**31))

        if "timestamp" in row and row["timestamp"]:
            lat = None
            lon = None
            if row.get("position_lat") is not None and row.get("position_long") is not None:
                lat = row.get("position_lat") * (180.0 / (2**31))
                lon = row.get("position_long") * (180.0 / (2**31))

            dados.append({
                "t": row.get("timestamp"),
                "hr": row.get("heart_rate"),
                "cad": row.get("cadence"),
                "spd": row.get("speed"),
                "lat": lat,
                "lon": lon
            })

    if not dados:
        print(f"Nenhum dado de 'record' encontrado no arquivo {filepath}")
        return

    # =========================
    # 2. COMPUTAÇÃO EM PASSO ÚNICO
    # =========================
    dist = 0
    tempo_total = 0
    tempo_corrida = 0
    ultima_t = None
    
    hrs = []
    spds = []

    eficiencia_janelas = []
    janela = []
    tempo_janela = 0
    
    blocos = []
    estado = None
    buffer = []

    for d in dados:
        t = d["t"]
        
        if ultima_t:
            delta = (t - ultima_t).total_seconds()
            tempo_total += delta
            
            # Acumula distância (velocidade vem em m/s na maioria dos FITs)
            if d["spd"] is not None:
                dist += d["spd"] * delta
                
            # Acumula tempo de corrida
            if d["cad"] is not None and d["cad"] >= CAD_CORRIDA:
                if estado == "corrida":
                    tempo_corrida += delta

            # Acumula Janelas de 60s (Eficiência Dinâmica)
            tempo_janela += delta
            janela.append(d)
            if tempo_janela >= 60:
                hrs_j = [x["hr"] for x in janela if x["hr"] is not None]
                spd_j = [x["spd"] for x in janela if x["spd"] is not None]
                if hrs_j and spd_j:
                    eff = (media(spd_j) * 3.6) / media(hrs_j)
                    eficiencia_janelas.append(eff)
                janela = []
                tempo_janela = 0
                
        d["dist"] = dist
        
        if d["hr"] is not None: hrs.append(d["hr"])
        if d["spd"] is not None: spds.append(d["spd"])

        # Identificação de Blocos (Corrida vs Caminhada)
        cad = d.get("cad")
        atual = "corrida" if (cad is not None and cad >= CAD_CORRIDA) else "caminhada"
        
        if atual != estado:
            if buffer:
                hrs_b = [x["hr"] for x in buffer if x["hr"] is not None]
                blocos.append({
                    "tipo": estado,
                    "duracao_s": len(buffer), # Aproximadamente 1 seg por registro, mas usamos len
                    "fc_media": media(hrs_b)
                })
            buffer = []
            estado = atual
            
        buffer.append(d)
        ultima_t = t

    # Fechar último bloco
    if buffer:
        hrs_b = [x["hr"] for x in buffer if x["hr"] is not None]
        blocos.append({
            "tipo": estado,
            "duracao_s": len(buffer),
            "fc_media": media(hrs_b)
        })

    # =========================
    # 3. MÉTRICAS OFICIAIS DA SESSÃO (Evita erros de integração e fornece extras)
    # =========================
    session_data = {}
    for session in fitfile.get_messages('session'):
        for field in ['total_distance', 'total_timer_time', 'avg_heart_rate', 'max_heart_rate', 
                      'total_calories', 'total_training_effect', 'total_anaerobic_training_effect']:
            val = session.get_value(field)
            if val is not None:
                session_data[field] = val
        break
        
    if 'total_distance' in session_data: dist = session_data['total_distance']
    if 'total_timer_time' in session_data: tempo_total = session_data['total_timer_time']
    
    dist_km = dist / 1000
    fc_media = session_data.get('avg_heart_rate') or media(hrs)
    spd_media = media(spds)
    
    desvio_vel = statistics.pstdev(spds) if len(spds) > 1 else None
    
    # Efficiency Factor (EF): Velocidade(km/h) / FC
    eficiencia = (spd_media * 3.6) / fc_media if (fc_media and spd_media) else None
    
    pct_corrida = (tempo_corrida / tempo_total) if tempo_total else None

    # Recuperação FC Pós-Corrida
    recuperacoes = []
    for i in range(1, len(dados)-10):
        if dados[i]["cad"] and dados[i]["cad"] >= CAD_CORRIDA:
            fim_hr = dados[i]["hr"]
            for j in range(i+1, min(i+10, len(dados))):
                if dados[j]["cad"] and dados[j]["cad"] < CAD_CORRIDA:
                    if dados[j]["hr"] and fim_hr:
                        recuperacoes.append(fim_hr - dados[j]["hr"])
                    break
    recuperacao_media = media(recuperacoes)

    # Detecção de Quebras (Suavizada para evitar falsos positivos do GPS)
    quebras = 0
    # Compara blocos de 5s para ter uma análise mais coerente da tendência
    for i in range(5, len(dados)-5, 5):
        bloco_ant = dados[i-5:i]
        bloco_pos = dados[i:i+5]
        
        spd_ant = media([x["spd"] for x in bloco_ant if x["spd"] is not None])
        hr_ant  = media([x["hr"]  for x in bloco_ant if x["hr"] is not None])
        spd_pos = media([x["spd"] for x in bloco_pos if x["spd"] is not None])
        hr_pos  = media([x["hr"]  for x in bloco_pos if x["hr"] is not None])
        
        if spd_ant and hr_ant and spd_pos and hr_pos:
            # Velocidade caiu significativamente (>5%) e FC subiu
            if spd_pos < (spd_ant * 0.95) and hr_pos > hr_ant:
                quebras += 1

    # Cardiac Drift (Queda da Eficiência da 1ª metade p/ 2ª metade)
    drift = None
    if len(eficiencia_janelas) > 2:
        meio = len(eficiencia_janelas) // 2
        ef_inicio = media(eficiencia_janelas[:meio])
        ef_final = media(eficiencia_janelas[meio:])
        if ef_inicio and ef_inicio > 0:
            # O drift é a redução da eficiência aeróbica com o tempo
            drift = (ef_inicio - ef_final) / ef_inicio

    pico_eficiencia = max(eficiencia_janelas) if eficiencia_janelas else None

    # =========================
    # 4. AVALIAÇÃO E SCORE (V4.0)
    # =========================
    score = 0
    
    # Novos limiares baseados em EF (km/h por bpm)
    # Ex: Um atleta correndo a 12km/h (5 min/km) com 150 bpm = 0.08 de EF.
    if eficiencia:
        if eficiencia > 0.08: score += 3
        elif eficiencia > 0.06: score += 2
        else: score += 1

    if drift is not None:
        if drift < 0.03: score += 3
        elif drift < 0.06: score += 2
        else: score += 1

    if quebras < 5: score += 2
    else: score += 1

    if desvio_vel and desvio_vel < 0.5: score += 2
    else: score += 1

    status = "indefinido"
    if drift is not None:
        if drift > 0.06: status = "fadiga alta"
        elif drift > 0.03: status = "moderado"
        else: status = "estável"

    qualidade_execucao = "boa" if desvio_vel and desvio_vel < 0.5 else "irregular"

    perfil = "constante"
    if quebras > 10: perfil = "irregular"
    elif drift is not None and drift < 0: perfil = "progressivo"
    elif drift is not None and drift > 0.05: perfil = "regressivo"

    # =========================
    # 5. BIOMECÂNICA V5 (Altimetria, Power, GAP, Suor, Classificação)
    # =========================
    dt_clima = session_data.get('start_time') or dados[0]["t"]
    clima = fetch_weather(lat_start, lon_start, dt_clima)

    valid_gps = [d for d in dados if d["lat"] is not None and d["lon"] is not None]
    
    ganho_elevacao = 0
    perda_elevacao = 0
    inclinacao_media = 0
    potencia_media_w = None
    gap_vel_kmh = None

    if valid_gps:
        passo = max(1, len(valid_gps) // 50)
        amostra_gps = valid_gps[::passo][:50]
        lats = [g["lat"] for g in amostra_gps]
        lons = [g["lon"] for g in amostra_gps]
        
        elevs = fetch_elevation_profile(lats, lons)
        
        if elevs and len(elevs) == len(amostra_gps):
            for i in range(1, len(elevs)):
                diff = elevs[i] - elevs[i-1]
                if diff > 0:
                    ganho_elevacao += diff
                else:
                    perda_elevacao += abs(diff)
            
            if dist > 0:
                inclinacao_media = (ganho_elevacao - perda_elevacao) / dist * 100

    if spd_media:
        inclinacao_fator = inclinacao_media if inclinacao_media is not None else 0
        ajuste = 1.0 + (inclinacao_fator * 0.03)
        gap_vel_kmh = (spd_media * 3.6) * max(0.5, ajuste)
        
        custo = 4.0 + (inclinacao_fator * 0.5 if inclinacao_fator > 0 else inclinacao_fator * 0.2)
        potencia_media_w = PESO_KG * spd_media * max(2.0, custo)

    suor_ml = estimar_sudorese(
        PESO_KG, tempo_total, 
        clima["temperatura_c"] if clima else None,
        clima["umidade_pct"] if clima else None,
        fc_media
    )

    tipo_treino = classificar_treino(dist_km, tempo_total, blocos, fc_media, pct_corrida)

    # =========================
    # 6. GERAR RESULTADO
    # =========================
    resultado = {
        "resumo": {
            "dist_km": round(dist_km, 3) if dist_km else 0,
            "tempo_s": round(tempo_total, 1),
            "fc_media": round(fc_media, 1) if fc_media else None,
            "fc_max": session_data.get('max_heart_rate'),
            "calorias": session_data.get('total_calories'),
            "training_effect": session_data.get('total_training_effect'),
            "anaerobic_te": session_data.get('total_anaerobic_training_effect'),
            "eficiencia_global": round(eficiencia, 4) if eficiencia else None,
            "desvio_vel": round(desvio_vel, 3) if desvio_vel else None,
            "pct_corrida": round(pct_corrida, 3) if pct_corrida else None,
            "recuperacao_fc": round(recuperacao_media, 1) if recuperacao_media else None,
            "quebras": quebras,
            "drift_aerobico": round(drift, 4) if drift else None,
            "pico_eficiencia": round(pico_eficiencia, 4) if pico_eficiencia else None,
            "altimetria_ganho_m": round(ganho_elevacao, 1),
            "altimetria_perda_m": round(perda_elevacao, 1),
            "gap_vel_kmh": round(gap_vel_kmh, 2) if gap_vel_kmh else None,
            "potencia_media_w": round(potencia_media_w, 1) if potencia_media_w else None,
            "estimativa_suor_ml": suor_ml
        },
        "clima": clima,
        "avaliacao": {
            "score_0_10": score,
            "status_fisiologico": status,
            "qualidade_execucao": qualidade_execucao,
            "perfil_sessao": perfil,
            "tipo_treino_detectado": tipo_treino
        },
        "eficiencia_janelas": [round(e, 4) for e in eficiencia_janelas] if eficiencia_janelas else [],
        "blocos": []
    }
    
    # Arredondando FC nos blocos
    for b in blocos:
        r_b = b.copy()
        if r_b["fc_media"] is not None:
            r_b["fc_media"] = round(r_b["fc_media"], 1)
        resultado["blocos"].append(r_b)

    # =========================
    # 6. MUDANÇA E ESTRUTURAÇÃO DE DIRETÓRIOS
    # =========================
    dt_atividade = dados[0]["t"]
    ano = str(dt_atividade.year)
    mes_nome = MESES_PT[dt_atividade.month]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    pasta_destino = os.path.join(base_path, ano, mes_nome)
    os.makedirs(pasta_destino, exist_ok=True)
    
    base_name = os.path.basename(filepath)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Salvar JSON
    json_path = os.path.join(pasta_destino, f"{name_without_ext}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
        
    # Mover arquivo FIT
    novo_fit_path = os.path.join(pasta_destino, base_name)
    shutil.move(filepath, novo_fit_path)
    
    print(f"   -> JSON gerado e FIT arquivados com sucesso na pasta: {ano}/{mes_nome}/\n")

if __name__ == "__main__":
    print("========================================")
    print("🚀 Fit Analyzer V5.0 Iniciado")
    print("========================================\n")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Procura arquivos .fit na pasta atual
    fit_files = glob.glob(os.path.join(base_path, "*.fit"))
    
    if not fit_files:
        print("Nenhum arquivo .fit encontrado na pasta raiz.")
    else:
        for f in fit_files:
            process_fit(f)
        print("✅ Todas as atividades foram processadas com sucesso!")