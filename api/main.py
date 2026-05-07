from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import glob

app = FastAPI(title="Py-Fit API")

# Habilitar CORS para permitir requisições do frontend local (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY_LOG_DIR = os.path.join(BASE_DIR, "Daily Log")
FIT_ANALYZER_DIR = os.path.join(BASE_DIR, "Fit Analyzer")

@app.get("/api/daily/semana_atual")
def get_semana_atual():
    pasta_semana = os.path.join(DAILY_LOG_DIR, "Semana")
    if not os.path.exists(pasta_semana):
        return []
        
    arquivos = sorted(glob.glob(os.path.join(pasta_semana, "*.json")))
    dados = []
    for arq in arquivos:
        try:
            with open(arq, "r", encoding="utf-8") as f:
                dados.append(json.load(f))
        except Exception as e:
            print(f"Erro ao ler {arq}: {e}")
            
    return dados

@app.get("/api/daily/consolidadas")
def get_semanas_consolidadas():
    pasta_consolidadas = os.path.join(DAILY_LOG_DIR, "Semanas_consolidadas")
    if not os.path.exists(pasta_consolidadas):
        return []
        
    # Buscar todas as pastas Semana_X
    pastas = glob.glob(os.path.join(pasta_consolidadas, "Semana_*"))
    resumos = []
    
    for pasta in sorted(pastas, key=lambda x: int(os.path.basename(x).split('_')[1])):
        resumo_path = os.path.join(pasta, "resumo.json")
        if os.path.exists(resumo_path):
            try:
                with open(resumo_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["semana_id"] = os.path.basename(pasta)
                    resumos.append(data)
            except Exception as e:
                print(f"Erro ao ler {resumo_path}: {e}")
                
    return resumos

@app.get("/api/daily/todos")
def get_todos_os_dias():
    dados = []
    
    # 1. Carregar das Semanas Consolidadas
    pasta_consolidadas = os.path.join(DAILY_LOG_DIR, "Semanas_consolidadas")
    if os.path.exists(pasta_consolidadas):
        pastas = glob.glob(os.path.join(pasta_consolidadas, "Semana_*"))
        for pasta in pastas:
            arquivos = glob.glob(os.path.join(pasta, "20*.json")) # Pega apenas os dias
            for arq in arquivos:
                try:
                    with open(arq, "r", encoding="utf-8") as f:
                        dados.append(json.load(f))
                except Exception as e:
                    print(f"Erro ao ler {arq}: {e}")

    # 2. Carregar da Semana Atual
    pasta_semana = os.path.join(DAILY_LOG_DIR, "Semana")
    if os.path.exists(pasta_semana):
        arquivos = glob.glob(os.path.join(pasta_semana, "20*.json"))
        for arq in arquivos:
            try:
                with open(arq, "r", encoding="utf-8") as f:
                    dados.append(json.load(f))
            except Exception as e:
                print(f"Erro ao ler {arq}: {e}")
                
    # Ordenar por data (DD/MM/YYYY) para YYYYMMDD para o sort
    def converte_data(d):
        try:
            partes = d["data"].split("/")
            if len(partes) == 3:
                return int(f"{partes[2]}{partes[1]}{partes[0]}")
        except:
            pass
        return 0
        
    dados.sort(key=converte_data)
    
    return dados

@app.get("/api/fit/runs")
def get_fit_runs():
    if not os.path.exists(FIT_ANALYZER_DIR):
        return []
        
    # Busca recursiva por todos os arquivos JSON dentro das subpastas de anos/meses
    arquivos = glob.glob(os.path.join(FIT_ANALYZER_DIR, "**", "*.json"), recursive=True)
    
    runs = []
    for arq in arquivos:
        # Ignorar arquivos temporarios que nao sejam de treinos e pastas Legacy
        if os.path.basename(arq) == "resumo.json": continue
        if "Legacy" in arq or "legacy" in arq: continue
        
        try:
            with open(arq, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Inclui o nome do arquivo para servir como chave unica
                data["id"] = os.path.basename(arq)
                runs.append(data)
        except Exception as e:
            print(f"Erro ao ler {arq}: {e}")
            
    # Ordena pelos mais recentes. O nome do arquivo começa com 'ZeppYYYYMMDD...'
    runs.sort(key=lambda r: r["id"], reverse=True)
    
    return runs
