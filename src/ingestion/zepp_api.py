import requests
import json
import os
import uuid
import time
import base64
from datetime import datetime

class ZeppAPI:
    def __init__(self, config_path=None):
        if config_path is None:
            # Busca na pasta config/ na raiz do projeto
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
            config_path = os.path.join(root_dir, "config", "zepp_config.json")
            
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
        self.base_url = f"https://{self.config['host']}"
        # Headers de Fidelidade (Zepp 6.4.0)
        self.headers = {
            "User-Agent": "Zepp/6.4.0-play (SM-S908E; Android 11; Density/1.5)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }

    def fetch_data(self, endpoint, params=None, host_override=None):
        """Helper para chamadas GET com fidelidade mobile total."""
        host = host_override if host_override else self.base_url
        url = f"{host}{endpoint}"
        
        timestamp = str(int(time.time() * 1000))
        base_params = {
            "r": str(uuid.uuid4()),
            "t": timestamp,
            "userid": self.config["user_id"],
            "appid": "2882303761517383915",
            "callid": timestamp,
            "channel": "play",
            "country": "BR",
            "cv": "100491_6.4.0-play",
            "appname": "com.huami.midong",
            "appv": "100491_6.4.0-play",
            "appplatform": "android_phone",
            "device": "android_30",
            "device_type": "android_phone",
            "lang": "pt_BR",
            "timezone": "America/Sao_Paulo",
            "v": "2.0"
        }
        if params:
            base_params.update(params)
        
        # Inserindo tokens tanto no header quanto na URL para evitar 401
        self.headers["apptoken"] = self.config["app_token"]
        
        try:
            response = requests.get(url, headers=self.headers, params=base_params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Se der 401 aqui, tentamos o heartbeat de novo
            print(f"⚠️ Tentando reativar sessão para {endpoint}...")
            self.check_session()
            response = requests.get(url, headers=self.headers, params=base_params)
            if response.status_code == 200:
                return response.json()
            print(f"❌ Erro persistente na API Zepp ({endpoint}): {e}")
            return None

    def check_session(self):
        """Valida e 'aquece' a sessão no account-us3 antes de pedir dados."""
        url = f"https://account-us3.zepp.com/v1/client/users/{self.config['user_id']}/profile"
        params = {
            "app_token": self.config["app_token"],
            "timestamp": str(int(time.time() * 1000))
        }
        print("🔄 Validando sessão (Heartbeat)...")
        try:
            r = requests.get(url, headers=self.headers, params=params)
            if r.status_code == 200:
                print("✅ Sessão Ativa (Profile OK)")
                return True
        except:
            pass
        return False

    def get_daily_sleep(self, date_str):
        """Pega dados de sono para uma data YYYY-MM-DD."""
        endpoint = f"/users/{self.config['user_id']}/sleep"
        params = {
            "startDate": date_str,
            "endDate": date_str,
            "interval": "daily"
        }
        return self.fetch_data(endpoint, params)

    def get_steps_and_calories(self, date_str):
        """Pega passos e calorias ativas."""
        endpoint = "/v1/data/band_data.json"
        params = {
            "userid": self.config["user_id"],
            "from_date": date_str,
            "to_date": date_str,
            "source": "run.mifit.huami.com"
        }
        return self.fetch_data(endpoint, params)

    def get_heart_rate(self, date_str):
        """Pega dados de batimentos (RHR)."""
        endpoint = f"/users/{self.config['user_id']}/heartRate"
        params = {
            "startDate": date_str,
            "endDate": date_str
        }
        return self.fetch_data(endpoint, params)

    def debug_discovery(self, date_str):
        """Varre os eventos do dia para descobrir quais tipos existem (PAI, Biocharge, etc)."""
        endpoint = f"/users/{self.config['user_id']}/events"
        params = {
            "startDate": date_str,
            "endDate": date_str,
            "limit": 1000
        }
        data = self.fetch_data(endpoint, params)
        if data and "items" in data:
            types = set(item.get("eventType") for item in data["items"])
            print(f"🔍 Eventos encontrados para {date_str}: {types}")
            return data
        return None

    def get_stress_and_pai(self, date_str):
        """Pega PAI e Estresse do endpoint de eventos genéricos."""
        endpoint = f"/users/{self.config['user_id']}/events"
        params = {
            "startDate": date_str,
            "endDate": date_str
        }
        return self.fetch_data(endpoint, params)

    def get_biocharge(self, date_str):
        """Pega o Biocharge (Charge insights) detalhado do dia."""
        endpoint = "/v2/users/me/events" # v2/events costuma aceitar 'me' ou o ID
        params = {
            "startDate": date_str,
            "endDate": date_str,
            "eventType": "Charge",
            "subType": "insight_data"
        }
        return self.fetch_data(endpoint, params)

    def get_hrv_rmssd(self, date_str):
        """Pega o HRV (RMSSD) do dia."""
        endpoint = "/v2/users/me/events"
        params = {
            "startDate": date_str,
            "endDate": date_str,
            "eventType": "Hrv",
            "subType": "RMSSD"
        }
        return self.fetch_data(endpoint, params)

    def get_workout_history(self):
        """Lista o histórico de corridas."""
        endpoint = "/v1/sport/run/history.json"
        params = {
            "source": "run.mifit.huami.com"
        }
        return self.fetch_data(endpoint, params)

    def get_workout_detail(self, track_id):
        """Pega os detalhes brutos de um treino (GPS, HR por segundo, etc)."""
        endpoint = "/v1/sport/run/detail.json"
        params = {
            "trackid": track_id,
            "source": "run.mifit.huami.com"
        }
        return self.fetch_data(endpoint, params)

    def get_raw_file_info(self):
        """Lista arquivos brutos (ZIPs) de batimentos por segundo no storage COS."""
        endpoint = "/users/me/fileInfo/events"
        return self.fetch_data(endpoint)

    def get_unified_data(self, date_str):
        """Endpoint unificado de resumo detalhado."""
        endpoint = "/v1/data/band_data.json"
        params = {
            "from_date": date_str,
            "to_date": date_str,
            "query_type": "detail",
            "byteLength": "8"
        }
        data = self.fetch_data(endpoint, params)
        if data and "data" in data and data["data"]:
            item = data["data"][0]
            if "summary" in item:
                try:
                    # O sumário vem em Base64 na API Mi Fit
                    decoded_bytes = base64.b64decode(item["summary"])
                    item["summary_decoded"] = json.loads(decoded_bytes.decode('utf-8'))
                except Exception as e:
                    print(f"⚠️ Erro ao decodificar sumário Base64: {e}")
                    item["summary_decoded"] = {}
            return item
        return None

    def normalize_for_daily(self, date_str):
        """Consolida tudo no formato do Py-Fit usando a fonte unificada."""
        self.check_session()
        print(f"🔄 Buscando dados unificados na Zepp Cloud para {date_str}...")
        
        unified = self.get_unified_data(date_str)
        if not unified:
            print("⚠️ Nenhum dado unificado encontrado para esta data.")
            return None

        summary = unified.get("summary_decoded", {})
        
        # Normalização de Sono (Estratégia Multidirecional)
        sleep = None
        slp = summary.get("slp", {})
        
        # 1. Tenta o sumário unificado (dp=Deep, lt=Light, dt=REM, wk=Wake)
        deep = slp.get("dp", 0)
        rem = slp.get("rem", 0) or slp.get("dt", 0) # 'dt' é o REM no Bip 6!
        light = slp.get("lt", 0)
        wake = slp.get("wk", 0)
        total_min = deep + rem + light
        
        if total_min > 0:
            sleep = {
                "total_hours": round(total_min / 60, 2),
                "deep_sleep_pct": round((deep / total_min) * 100, 1),
                "rem_sleep_pct": round((rem / total_min) * 100, 1),
                "light_sleep_pct": round((light / total_min) * 100, 1),
                "awake_hours": round(wake / 60, 2)
            }

        # Extração de Oxigênio e Qualidade Respiratória (ODI)
        # O usuário achou em /users/3310868935/events/dateString?subType=odi
        odi_raw = self.fetch_data(f"/users/{self.config['user_id']}/events/dateString", {
            "eventType": "blood_oxygen",
            "subType": "odi",
            "from": f"{date_str}T00:00:00",
            "to": f"{date_str}T23:59:59"
        })
        spo2_score = None
        if odi_raw and "items" in odi_raw and odi_raw["items"]:
            spo2_score = odi_raw["items"][0].get("score")

        # Extração de métricas do sumário
        stp = summary.get("stp", {})
        steps = stp.get("ttl", 0)
        calories = stp.get("cal", 0)
        # Busca RHR via PAI (Muito mais preciso)
        pai_raw = self.get_pai_info(str(int(time.mktime(datetime.strptime(date_str, "%Y-%m-%d").timetuple()) * 1000)))
        rhr = 0
        pai = 0
        if pai_raw and "items" in pai_raw and pai_raw["items"]:
            # Pega o último evento de PAI do dia
            ultimo_evento = pai_raw["items"][-1]
            rhr = int(ultimo_evento.get("restHr", 0))
            pai = float(ultimo_evento.get("dailyPai", 0))

        # Se RHR continuar 0, tenta o sumário ou endpoint de HR
        if rhr == 0:
            rhr = summary.get("rhr", 0)
        
        if rhr == 0:
            hr_raw = self.fetch_data(f"/users/{self.config['user_id']}/heartRate", {"startDate": date_str, "endDate": date_str})
            if hr_raw and "items" in hr_raw and hr_raw["items"]:
                for item in hr_raw["items"]:
                    if "restingHeartRate" in item:
                        rhr = item["restingHeartRate"]
                        break

        # Estresse
        stress = summary.get("sts")
        
        # Fallback para Estresse se vier nulo
        if stress is None:
            stress_raw = self.fetch_data(f"/users/{self.config['user_id']}/stress", {"startDate": date_str, "endDate": date_str})
            if stress_raw and "items" in stress_raw and stress_raw["items"]:
                # Pega a média de estresse do dia
                stress = stress_raw["items"][0].get("avg")

        # Busca Métricas de Elite (Sport Load)
        load_raw = self.get_sport_load(date_str)
        sport_load = None
        if load_raw and "items" in load_raw and load_raw["items"]:
            item = load_raw["items"][0]
            sport_load = {
                "current": item.get("wtlSum"),
                "optimal_min": item.get("wtlSumOptimalMin"),
                "optimal_max": item.get("wtlSumOptimalMax"),
                "overreaching": item.get("wtlSumOverreaching")
            }

        return {
            "date": date_str,
            "sleep": sleep,
            "steps": steps,
            "calories": calories,
            "rhr": rhr,
            "pai": pai,
            "stress": stress,
            "spo2": spo2_score,
            "sport_load": sport_load,
            "api_source": "ZeppCloud"
        }

    def get_workout_history(self, start_month, end_month):
        """Pega o histórico de treinos (Corrida, Musculação, etc)."""
        endpoint = "/v1/sport/run/history.json"
        params = {
            "from": start_month, # Ex: "2026-04"
            "to": end_month,     # Ex: "2026-05"
            "type": "0"
        }
        return self.fetch_data(endpoint, params)

    def get_biocharge(self, date_str):
        """Pega o Biocharge / Readiness score."""
        endpoint = "/v1/user/manualData.json"
        params = {
            "type": "biocharge",
            "startDate": date_str,
            "endDate": date_str
        }
        return self.fetch_data(endpoint, params)

    def get_sport_load(self, date_str):
        """Pega a carga de treino (Sport Load / Training Load)."""
        endpoint = f"/watch/users/{self.config['user_id']}/WatchSportStatistics/SPORT_LOAD"
        params = {
            "startDay": date_str,
            "endDay": date_str,
            "userid": self.config["user_id"]
        }
        return self.fetch_data(endpoint, params)

    def get_vo2_max(self, start_day, end_day):
        """Pega o histórico de VO2 Max."""
        endpoint = f"/watch/users/{self.config['user_id']}/WatchSportStatistics/VO2_MAX"
        params = {
            "startDay": start_day,
            "endDay": end_day,
            "userid": self.config["user_id"]
        }
        return self.fetch_data(endpoint, params)

    def get_sport_stats(self):
        """Pega as estatísticas acumuladas de esporte (Carreira)."""
        endpoint = "/v2/sport/stat.json"
        params = {
            "type": "0", # 0 para pegar todos os tipos
            "v": "2.0"
        }
        return self.fetch_data(endpoint, params)

    def get_pai_info(self, start_ts, end_params=None):
        """Pega informações de PAI e Resting HR granular."""
        endpoint = f"/users/{self.config['user_id']}/events"
        params = {
            "limit": "3000",
            "subType": "PaiHealthInfo",
            "eventType": "PaiHealthInfo",
            "from": start_ts, # Timestamp em ms
            "to": str(int(time.time() * 1000)),
            "v": "2.0"
        }
        return self.fetch_data(endpoint, params)

    def get_workout_detail(self, track_id, source):
        """Pega os detalhes brutos de um treino específico (HR curva, GPS, etc)."""
        endpoint = "/v1/sport/run/detail.json"
        params = {
            "trackid": track_id,
            "source": source,
            "v": "2.0"
        }
        return self.fetch_data(endpoint, params)
