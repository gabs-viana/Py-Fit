import os
import glob
import json
import shutil
from datetime import datetime
import statistics
from fitparse import FitFile

IDADE = 19
FC_MAX_TEO = 220 - IDADE
CAD_CORRIDA = 75

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def media(l):
    return sum(l) / len(l) if l else None

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
    # Lemos mantendo os objetos datetime nativos.
    for record in fitfile.get_messages('record'):
        row = {}
        for d in record:
            row[d.name] = d.value
        
        if "timestamp" in row and row["timestamp"]:
            dados.append({
                "t": row.get("timestamp"),
                "hr": row.get("heart_rate"),
                "cad": row.get("cadence"),
                "spd": row.get("speed")
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
    # 5. GERAR RESULTADO
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
            "pico_eficiencia": round(pico_eficiencia, 4) if pico_eficiencia else None
        },
        "avaliacao": {
            "score_0_10": score,
            "status_fisiologico": status,
            "qualidade_execucao": qualidade_execucao,
            "perfil_sessao": perfil
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
    print("🚀 Fit Analyzer V4.0 Iniciado")
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