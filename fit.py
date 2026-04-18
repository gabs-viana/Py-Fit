from fitparse import FitFile
import json
from datetime import datetime

fitfile = FitFile('Zepp20260414180951.fit')

registros = []

# =========================
# EXTRAÇÃO + NORMALIZAÇÃO
# =========================
for record in fitfile.get_messages('record'):
    data = {}

    for d in record:
        value = d.value

        if isinstance(value, datetime):
            value = value.isoformat()

        data[d.name] = value

    registros.append(data)

# =========================
# LIMPEZA + CAMPOS IMPORTANTES
# =========================
dados = []
for r in registros:
    if "timestamp" not in r:
        continue

    dados.append({
        "t": r.get("timestamp"),
        "hr": r.get("heart_rate"),
        "cad": r.get("cadence"),
        "spd": r.get("speed"),
        "alt": r.get("altitude"),
    })

# =========================
# DISTÂNCIA + TEMPO REAL
# =========================
dist_acumulada = 0
tempo_total = 0
ultima_t = None

for d in dados:
    if d["t"] is None:
        d["dist_calc"] = dist_acumulada
        continue

    t_atual = datetime.fromisoformat(d["t"])

    if ultima_t is not None:
        delta = (t_atual - ultima_t).total_seconds()

        # tempo real
        tempo_total += delta

        # distância só se tiver velocidade
        if d["spd"] is not None:
            dist_acumulada += d["spd"] * delta

    d["dist_calc"] = dist_acumulada
    ultima_t = t_atual

dist_total = dist_acumulada

# =========================
# ESTATÍSTICAS
# =========================
hrs = [d["hr"] for d in dados if d["hr"] is not None]
spds = [d["spd"] for d in dados if d["spd"] is not None]
cads = [d["cad"] for d in dados if d["cad"] is not None]

def media(lista):
    return sum(lista)/len(lista) if lista else None

def safe_max(lista):
    return max(lista) if lista else None

# pace correto
pace_medio = (tempo_total / (dist_total/1000)) if dist_total else None

# =========================
# SPLITS POR KM (TEMPO REAL)
# =========================
splits = []
km_atual = 1
inicio_idx = 0

for i, d in enumerate(dados):
    if d["dist_calc"] >= km_atual * 1000:
        trecho = dados[inicio_idx:i]

        # tempo real do trecho
        tempo_km = 0
        ultima_t_split = None

        for x in trecho:
            if x["t"] is None:
                continue

            t_split = datetime.fromisoformat(x["t"])

            if ultima_t_split is not None:
                tempo_km += (t_split - ultima_t_split).total_seconds()

            ultima_t_split = t_split

        hr_km = media([x["hr"] for x in trecho if x["hr"] is not None])
        cad_km = media([x["cad"] for x in trecho if x["cad"] is not None])

        splits.append({
            "km": km_atual,
            "pace_s": tempo_km,
            "fc_media": hr_km,
            "cad_media": cad_km
        })

        km_atual += 1
        inicio_idx = i

# =========================
# ZONAS DE FC
# =========================
fc_max = safe_max(hrs)

zonas = {"z1":0,"z2":0,"z3":0,"z4":0,"z5":0}

for h in hrs:
    if not fc_max:
        continue

    perc = h / fc_max

    if perc < 0.6:
        zonas["z1"] += 1
    elif perc < 0.7:
        zonas["z2"] += 1
    elif perc < 0.8:
        zonas["z3"] += 1
    elif perc < 0.9:
        zonas["z4"] += 1
    else:
        zonas["z5"] += 1

# =========================
# DOWNSAMPLE INTELIGENTE (~5s real)
# =========================
serie_reduzida = []
ultima_t = None

for d in dados:
    if d["t"] is None:
        continue

    t_atual = datetime.fromisoformat(d["t"])

    if ultima_t is None or (t_atual - ultima_t).total_seconds() >= 5:
        serie_reduzida.append(d)
        ultima_t = t_atual

# =========================
# OUTPUT FINAL
# =========================
resultado = {
    "resumo": {
        "tempo_s": tempo_total,
        "distancia_m": dist_total,
        "pace_medio_s_km": pace_medio,
        "fc_media": media(hrs),
        "fc_max": fc_max,
        "vel_media": media(spds),
        "cad_media": media(cads)
    },
    "splits": splits,
    "zonas_fc": zonas,
    "serie_reduzida": serie_reduzida
}

with open('atividade_processada.json', 'w', encoding='utf-8') as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print("🔥 JSON PROFISSIONAL NIVEL STRAVA GERADO!")