from fitparse import FitFile
import json
from datetime import datetime
import statistics

IDADE = 19
FC_MAX_TEO = 220 - IDADE
CAD_CORRIDA = 75

fitfile = FitFile('Zepp20260421180225.fit')

# =========================
# EXTRAÇÃO
# =========================
dados = []

for record in fitfile.get_messages('record'):
    row = {}
    for d in record:
        val = d.value
        if isinstance(val, datetime):
            val = val.isoformat()
        row[d.name] = val

    if "timestamp" in row:
        dados.append({
            "t": row.get("timestamp"),
            "hr": row.get("heart_rate"),
            "cad": row.get("cadence"),
            "spd": row.get("speed")
        })

# =========================
# TEMPO + DISTÂNCIA
# =========================
dist = 0
tempo = 0
ultima_t = None

for d in dados:
    if not d["t"]:
        continue

    t = datetime.fromisoformat(d["t"])

    if ultima_t:
        delta = (t - ultima_t).total_seconds()
        tempo += delta
        if d["spd"]:
            dist += d["spd"] * delta

    d["dist"] = dist
    ultima_t = t

dist_km = dist / 1000

# =========================
# LISTAS
# =========================
hrs = [d["hr"] for d in dados if d["hr"]]
spds = [d["spd"] for d in dados if d["spd"]]

def media(l): return sum(l)/len(l) if l else None

fc_media = media(hrs)

# =========================
# CONSISTÊNCIA DE RITMO
# =========================
desvio_vel = statistics.pstdev(spds) if len(spds) > 1 else None

# =========================
# EFICIÊNCIA GLOBAL
# =========================
eficiencia = (dist_km / fc_media) if fc_media else None

# =========================
# EFICIÊNCIA DINÂMICA (janela 60s)
# =========================
eficiencia_janelas = []
janela = []
tempo_janela = 0
ultima_t = None

for d in dados:
    if not d["t"]:
        continue

    t = datetime.fromisoformat(d["t"])

    if ultima_t:
        delta = (t - ultima_t).total_seconds()
        tempo_janela += delta

    janela.append(d)

    if tempo_janela >= 60:
        hrs_j = [x["hr"] for x in janela if x["hr"]]
        spd_j = [x["spd"] for x in janela if x["spd"]]

        if hrs_j and spd_j:
            eff = (media(spd_j) * 3.6) / media(hrs_j)
            eficiencia_janelas.append(eff)

        janela = []
        tempo_janela = 0

    ultima_t = t

# =========================
# DETECÇÃO DE BLOCOS
# =========================
blocos = []
estado = None
buffer = []

tempo_corrida = 0
tempo_total = 0

ultima_t = None

for d in dados:
    if not d["t"] or not d["cad"]:
        continue

    t = datetime.fromisoformat(d["t"])

    if ultima_t:
        delta = (t - ultima_t).total_seconds()
        tempo_total += delta

        if estado == "corrida":
            tempo_corrida += delta

    atual = "corrida" if d["cad"] >= CAD_CORRIDA else "caminhada"

    if atual != estado:
        if buffer:
            hrs_b = [x["hr"] for x in buffer if x["hr"]]

            blocos.append({
                "tipo": estado,
                "duracao_s": len(buffer),
                "fc_media": media(hrs_b)
            })
        buffer = []
        estado = atual

    buffer.append(d)
    ultima_t = t

# =========================
# % TEMPO CORRENDO
# =========================
pct_corrida = (tempo_corrida / tempo_total) if tempo_total else None

# =========================
# RECUPERAÇÃO FC (pós corrida)
# =========================
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

# =========================
# DETECÇÃO DE QUEBRA
# =========================
quebras = 0

for i in range(1, len(dados)):
    if dados[i]["spd"] and dados[i]["hr"] and dados[i-1]["spd"] and dados[i-1]["hr"]:
        if dados[i]["spd"] < dados[i-1]["spd"] and dados[i]["hr"] > dados[i-1]["hr"]:
            quebras += 1

# =========================
# CARDIAC DRIFT
# =========================
drift = None
if len(hrs) > 10:
    meio = len(hrs) // 2
    fc_inicio = media(hrs[:meio])
    fc_final = media(hrs[meio:])
    
    if fc_inicio:
        drift = (fc_final - fc_inicio) / fc_inicio

# =========================
# PICO DE PERFORMANCE (melhor janela)
# =========================
pico_eficiencia = max(eficiencia_janelas) if eficiencia_janelas else None

# =========================
# SCORE FINAL (0–10)
# =========================
score = 0

if eficiencia:
    if eficiencia > 0.03:
        score += 3
    elif eficiencia > 0.025:
        score += 2
    else:
        score += 1

if drift is not None:
    if drift < 0.03:
        score += 3
    elif drift < 0.06:
        score += 2
    else:
        score += 1

if quebras < 10:
    score += 2
else:
    score += 1

if desvio_vel and desvio_vel < 0.5:
    score += 2
else:
    score += 1

# =========================
# STATUS FISIOLÓGICO
# =========================
status = "indefinido"

if drift is not None:
    if drift > 0.06:
        status = "fadiga alta"
    elif drift > 0.03:
        status = "moderado"
    else:
        status = "estável"

# =========================
# QUALIDADE DE EXECUÇÃO
# =========================
qualidade_execucao = "boa" if desvio_vel and desvio_vel < 0.5 else "irregular"

# =========================
# PERFIL DA SESSÃO
# =========================
perfil = "constante"

if quebras > 15:
    perfil = "irregular"
elif drift is not None and drift < 0:
    perfil = "progressivo"
elif drift is not None and drift > 0.05:
    perfil = "regressivo"

# =========================
# OUTPUT
# =========================
resultado = {
    "resumo": {
        "dist_km": dist_km,
        "tempo_s": tempo,
        "fc_media": fc_media,
        "eficiencia": eficiencia,
        "desvio_vel": desvio_vel,
        "pct_corrida": pct_corrida,
        "recuperacao_fc": recuperacao_media,
        "quebras": quebras,
        "drift": drift,
        "pico_eficiencia": pico_eficiencia
    },
    "avaliacao": {
        "score_0_10": score,
        "status_fisiologico": status,
        "qualidade_execucao": qualidade_execucao,
        "perfil_sessao": perfil
    },
    "eficiencia_janelas": eficiencia_janelas,
    "blocos": blocos
}

with open("atividade_v3_5.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("🚀 V3.5 — ENGINE COMPLETA GERADA")