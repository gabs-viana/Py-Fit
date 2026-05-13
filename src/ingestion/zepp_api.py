import requests
import json
import os
import uuid
import time
import base64
from datetime import datetime, timedelta

class ZeppAPI:
    def __init__(self, config_path=None):
        if config_path is None:
            # Busca na pasta config/ na raiz do projeto
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
            config_path = os.path.join(root_dir, "config", "zepp_config.json")
            
        self.config_path = config_path
        self.config = {}
        
        # 1. Tenta carregar do arquivo local
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                try:
                    self.config = json.load(f)
                except json.JSONDecodeError:
                    print(f"⚠️ Erro ao ler {self.config_path}. Usando variáveis de ambiente.")
        
        # 2. Fallback para variáveis de ambiente (Open Core Security)
        self.config["host"] = self.config.get("host") or os.getenv("ZEPP_HOST", "api-mifit-us3.zepp.com")
        self.config["user_id"] = self.config.get("user_id") or os.getenv("ZEPP_USER_ID")
        self.config["app_token"] = self.config.get("app_token") or os.getenv("ZEPP_APP_TOKEN")
        self.config["login_token"] = self.config.get("login_token") or os.getenv("ZEPP_LOGIN_TOKEN")

        if not self.config.get("user_id") or not self.config.get("app_token"):
            print("❌ ATENÇÃO: Credenciais Zepp não encontradas (zepp_config.json ou Env Vars).")
            
        # Carrega pesos adaptativos
        weights_path = os.path.join(os.path.dirname(self.config_path), "pyfit_weights.json")
        try:
            with open(weights_path, "r") as f:
                self.weights = json.load(f)["current_weights"]
        except Exception:
            self.weights = {
                "sleep_impact": 0.40,
                "zepp_readiness": 0.30,
                "hrv_impact": 0.20,
                "biocharge_waking": 0.10
            }
            
        self.base_url = f"https://{self.config['host']}"
        # Headers de Alta Fidelidade (Zepp 10.2.5 - Clone Real do POCO)
        self.headers = {
            "User-Agent": "Zepp/10.2.5 (SM-N976N; Android 9; Density/2.0)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "appplatform": "android_phone",
            "appname": "com.huami.midong",
            "channel": "normal",
            "country": "BR",
            "lang": "pt_BR",
            "timezone": "America/Sao_Paulo"
        }

    def get_common_params(self, params=None):
        """Monta os parâmetros padrão exigidos pela Zepp."""
        # CORREÇÃO CRÍTICA DE DRIFT: 
        # O sistema está reportando timestamp 24h à frente. 
        # Ajustamos subtraindo 1 dia (86400s) para sincronizar com a Zepp.
        now = datetime.now()
        call_id = str(int((now.timestamp() - 86400) * 1000))
        
        base_params = {
            "r": str(uuid.uuid4()),
            "t": call_id,
            "userid": self.config["user_id"],
            "appid": "2882303761517383915",
            "callid": call_id,
            "channel": "normal",
            "country": "BR",
            "cv": "151830_10.2.5",
            "appname": "com.huami.midong",
            "appv": "100491_6.4.0-play",
            "appplatform": "android_phone",
            "device": "android_33",
            "device_type": "android_phone",
            "lang": "pt_BR",
            "timezone": "America/Sao_Paulo",
            "vn": "4.0.17",
            "vb": "20240101",
            "v": "2.0"
        }
        if params:
            base_params.update(params)
        return base_params

    def fetch_data(self, endpoint, params=None):
        """Faz a requisição para a API da Zepp Cloud."""
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else endpoint
        
        base_params = self.get_common_params(params)
        
        # Inserindo tokens tanto no header quanto na URL para evitar 401
        self.headers["apptoken"] = self.config["app_token"]
        
        try:
            response = requests.get(url, headers=self.headers, params=base_params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️ Erro ao buscar dados ({endpoint}): {e}. Tentando renovar a sessão (Session Replay)...")
            if self.renew_session():
                # Atualiza o token nos headers
                self.headers["apptoken"] = self.config["app_token"]
                response = requests.get(url, headers=self.headers, params=base_params)
                if response.status_code == 200:
                    return response.json()
            print(f"❌ Erro persistente na API Zepp ({endpoint}) após tentativa de renovação.")
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

    def save_config(self):
        """Salva as configurações atualizadas (como os novos tokens) no disco."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            print("💾 Tokens atualizados e salvos com sucesso no zepp_config.json")
        except Exception as e:
            print(f"❌ Erro ao salvar zepp_config.json: {e}")

    def renew_session(self):
        """Renova o login_token e o app_token simulando o tráfego legítimo (Session Replay)."""
        print("🔄 Iniciando processo de renovação de sessão (Session Replay)...")
        
        # 1. Renovar o login_token
        renew_url = "https://api-mifit-us3.zepp.com/v1/client/renew_login_token"
        ts = str(int(time.time() * 1000))
        dn = "api-mifit.zepp.com,api-user.zepp.com,api-mifit.zepp.com,api-watch.zepp.com,app-analytics.zepp.com,auth.zepp.com,api-analytics.zepp.com"
        source = "com.huami.watch.hmwatchmanager:10.2.5:151830"
        
        renew_params = {
            "os_version": "vnull",
            "dn": dn,
            "login_token": self.config.get("login_token", ""),
            "source": source,
            "timestamp": ts
        }
        
        renew_headers = {
            "User-Agent": "Zepp/10.2.5 (SM-N976N; Android 9; Density/2.0)",
            "appname": "com.huami.midong",
            "appplatform": "android_phone",
            "v": "2.0",
            "vn": "10.2.5",
            "cv": "151830_10.2.5",
            "Connection": "Keep-Alive"
        }

        try:
            r1 = requests.get(renew_url, headers=renew_headers, params=renew_params)
            r1.raise_for_status()
            r1_data = r1.json()
            
            if r1_data.get("result") == "ok":
                new_login_token = r1_data["token_info"]["login_token"]
                print("✅ login_token renovado com sucesso.")
                self.config["login_token"] = new_login_token
            else:
                print("❌ Falha ao renovar login_token:", r1_data)
                return False
                
            # 2. Obter novo app_token usando o novo login_token
            app_token_url = "https://api-mifit-us3.zepp.com/v1/client/app_tokens"
            ts2 = str(int(time.time() * 1000))
            app_token_params = {
                "os_version": "vnull",
                "dn": dn,
                "login_token": new_login_token,
                "source": source,
                "timestamp": ts2
            }
            
            r2 = requests.get(app_token_url, headers=renew_headers, params=app_token_params)
            r2.raise_for_status()
            r2_data = r2.json()
            
            if r2_data.get("result") == "ok":
                new_app_token = r2_data["token_info"]["app_token"]
                user_id = r2_data["token_info"]["user_id"]
                print("✅ app_token renovado com sucesso.")
                
                self.config["app_token"] = new_app_token
                self.config["user_id"] = user_id
                
                # Salva a configuração atualizada
                self.save_config()
                return True
            else:
                print("❌ Falha ao renovar app_token:", r2_data)
                return False
                
        except Exception as e:
            print(f"❌ Exceção durante a renovação da sessão: {e}")
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

    def get_sleep_insights(self, date_str):
        """Pega os insights de sono (Sleep Score e texto do dia)."""
        endpoint = "/aura/insight/sleep/daily"
        params = {
            "date": date_str
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



    def get_readiness_score(self, date_str, end_date=None):
        """Busca Readiness Score e HRV (RMSSD). Mapeado via watch_score."""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        endpoint = "/v2/users/me/events"
        
        if end_date:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
            start_ts = int(time.mktime(dt.timetuple()) * 1000)
            end_ts = int((time.mktime(dt_end.timetuple()) + 86400) * 1000)
        else:
            start_ts = int((time.mktime(dt.timetuple()) - 43200) * 1000)
            end_ts = int((time.mktime(dt.timetuple()) + 86400 + 43200) * 1000)
        
        # 1. Busca Biocharge (real_data)
        bio_params = {
            "from": start_ts,
            "to": end_ts,
            "eventType": "Charge",
            "subType": "real_data",
            "reverse": "true",
            "limit": 500
        }
        bio_data = self.fetch_data(endpoint, bio_params)
        
        # 2. Busca Readiness "Gold Standard" (watch_score)
        readiness_params = {
            "from": start_ts,
            "to": end_ts,
            "eventType": "readiness",
            "subType": "watch_score",
            "reverse": "true",
            "limit": 300
        }
        readiness_data = self.fetch_data(endpoint, readiness_params)
        
        if end_date:
            return {"bio": bio_data, "readiness": readiness_data}

        # Lógica legado para dia único
        bio_current = None
        bio_waking = None
        if bio_data and "items" in bio_data and bio_data["items"]:
            samples = bio_data["items"][0].get("value", {}).get("samples", [])
            if samples:
                for s in reversed(samples):
                    if s.get("total", 255) < 255:
                        bio_current = s["total"]
                        break
                morning = [s["total"] for s in samples if 21600000 < s.get("s",0) < 39600000 and s.get("total", 255) < 255]
                if morning: bio_waking = max(morning)
        
        hrv = None
        readiness = None
        if readiness_data and "items" in readiness_data and readiness_data["items"]:
            val = readiness_data["items"][0].get("value", {})
            hrv = val.get("sleepHRV") or val.get("hrvScore")
            readiness = val.get("rdnsScore")
            
        return {
            "biocharge_current": bio_current,
            "biocharge_waking": bio_waking,
            "readiness": readiness,
            "hrv": hrv
        }

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

    def get_all_day_stress(self, date_str, end_date=None):
        """Busca o estresse diário (sumário gerado pela nuvem)."""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        endpoint = "/v2/users/me/events"

        if end_date:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
            start_ts = int(time.mktime(dt.timetuple()) * 1000)
            end_ts = int((time.mktime(dt_end.timetuple()) + 86400) * 1000)
        else:
            start_ts = int((time.mktime(dt.timetuple()) - 43200) * 1000)
            end_ts = int((time.mktime(dt.timetuple()) + 86400 + 43200) * 1000)
        
        params = {
            "limit": 500 if end_date else 20,
            "subType": "all_day_stress",
            "eventType": "all_day_stress",
            "from": start_ts,
            "to": end_ts,
            "reverse": "true"
        }
        return self.fetch_data(endpoint, params=params)

    def get_single_stress(self, date_str):
        """Busca medições de estresse avulsas (pontuais)."""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        start_ts = int((time.mktime(dt.timetuple()) - 43200) * 1000)
        end_ts = int((time.mktime(dt.timetuple()) + 86400 + 43200) * 1000)
        
        endpoint = "/v2/users/me/events"
        params = {
            "limit": 100,
            "subType": "single_stress",
            "eventType": "single_stress",
            "from": start_ts,
            "to": end_ts,
            "reverse": "true"
        }
        return self.fetch_data(endpoint, params=params)

    def get_daily_nutrition(self, date_str):
        """Busca registros de alimentação e macros do dia (com margem ampliada para drift)."""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        # Janela de 48h (dia anterior e dia posterior) para garantir captura com drift de relógio
        start_ts = int((dt - timedelta(days=1)).timestamp() * 1000)
        end_ts = int((dt + timedelta(days=1)).timestamp() * 1000)
        
        endpoint = "/v2/users/me/events"
        params = {
            "limit": 100,
            "subType": "real_data",
            "eventType": "Food",
            "from": start_ts,
            "to": end_ts,
            "reverse": "true"
        }
        return self.fetch_data(endpoint, params=params)

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

    def get_weight_records(self, date_str):
        """Busca histórico de peso com headers cirúrgicos."""
        url = f"https://api-mifit-us3.zepp.com/users/{self.config['user_id']}/members/-1/weightRecords"
        headers = {
            "Authorization": f"Bearer {self.config['app_token']}",
            "apptoken": self.config["app_token"],
            "User-Agent": "Zepp/10.2.5 (SM-N976N; Android 9; Density/2.0)"
        }
        try:
            r = requests.get(url, headers=headers, params={"limit": 5}, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            pass
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
        print(f"📊 Sumário decodificado: {list(summary.keys())}")
        
        # Normalização de Sono (Estratégia Multidirecional)
        sleep = None
        slp = summary.get("slp", {})
        
        # 1. Tenta o sumário unificado (dp=Deep, lt=Light, dt=REM, wk=Wake)
        deep = slp.get("dp", 0)
        rem = slp.get("rem", 0) or slp.get("dt", 0) # 'dt' é o REM no Bip 6!
        light = slp.get("lt", 0)
        wake = slp.get("wk", 0)
        total_min = deep + rem + light
        
        # 2. Tenta os Insights (mais preciso para o Texto)
        insights = self.get_sleep_insights(date_str)
        sleep_score = None
        sleep_text = ""
        if insights and "sleepList" in insights and insights["sleepList"]:
            curr = insights["sleepList"][0]
            # O Aura Insight às vezes traz um score diferente.
            sleep_text = insights.get("content", "")

        # 3. Prioridade Total: Sumário Unificado (Aonde achamos o 81!)
        unified = self.get_unified_data(date_str)
        if unified and "summary_decoded" in unified:
            summary = unified["summary_decoded"]
            slp_summary = summary.get("slp", {})
            # A chave 'ss' é o padrão ouro
            sleep_score = slp_summary.get("ss") or slp_summary.get("score") or summary.get("ss")
        
        # Fallback para o Aura Insight se o sumário falhar
        if not sleep_score and insights and "sleepList" in insights and insights["sleepList"]:
            sleep_score = insights["sleepList"][0].get("score") or insights["sleepList"][0].get("dp")

        if total_min > 0:
            sleep = {
                "total_hours": round(total_min / 60, 2),
                "deep_sleep_pct": round((deep / total_min) * 100, 1),
                "rem_sleep_pct": round((rem / total_min) * 100, 1),
                "light_sleep_pct": round((light / total_min) * 100, 1),
                "awake_hours": round(wake / 60, 2),
                "score": sleep_score,
                "insight": sleep_text
            }

        # Extração de métricas do sumário
        stp = summary.get("stp", {})
        steps = stp.get("ttl", 0)
        calories = stp.get("cal", 0)

        # Busca RHR e PAI via endpoint específico (Muito mais preciso)
        timestamp = str(int(time.mktime(datetime.strptime(date_str, "%Y-%m-%d").timetuple()) * 1000))
        pai_raw = self.get_pai_info(timestamp)
        rhr = 0
        pai = 0
        pai_gain = 0
        if pai_raw and "items" in pai_raw and pai_raw["items"]:
            ultimo_evento = pai_raw["items"][-1]
            rhr = int(ultimo_evento.get("restHr", 0))
            pai = float(ultimo_evento.get("totalPai", 0) or ultimo_evento.get("dailyPai", 0))
            if len(pai_raw["items"]) > 1:
                penultimo = pai_raw["items"][-2]
                pai_gain = pai - float(penultimo.get("totalPai", 0))

        # Busca Readiness e Biocharge (Combo HRV incluso)
        readiness_data = self.get_readiness_score(date_str)
        hrv = readiness_data.get("hrv")
        
        # Busca Peso e BMI
        weight_data = self.get_weight_records(date_str)
        weight = None
        bmi = None
        if weight_data:
            items = []
            if isinstance(weight_data, list): items = weight_data
            elif isinstance(weight_data, dict): items = weight_data.get("items", [])
            
            if items:
                # Pega o mais recente e verifica se é de HOJE (date_str)
                latest = items[0]
                gen_time = latest.get("generatedTime")
                if gen_time:
                    # Converte generatedTime (segundos) para data YYYY-MM-DD
                    record_date = datetime.fromtimestamp(gen_time).strftime("%Y-%m-%d")
                    if record_date == date_str:
                        w_summary = latest.get("summary", {})
                        weight = w_summary.get("weight")
                        bmi = w_summary.get("bmi")
                    else:
                        print(f"⚖️ Peso ignorado: Registro mais recente é de {record_date} (esperado {date_str})")

        # Busca Estresse (Estratégia Híbrida: Sumário -> Média de Pontuais)
        stress = None
        stress_raw = self.get_all_day_stress(date_str)
        if stress_raw and "items" in stress_raw and stress_raw["items"]:
            stress = int(stress_raw["items"][0].get("value", {}).get("avgStress", 0))
        
        if stress is None or stress == 0:
            single_raw = self.get_single_stress(date_str)
            if single_raw and "items" in single_raw and single_raw["items"]:
                # Calcula média das medições do dia
                vals = [int(i.get("value", {}).get("value", 0)) for i in single_raw["items"]]
                if vals: stress = int(sum(vals) / len(vals))

        # Fallbacks
        if rhr == 0: rhr = summary.get("rhr", 0)
        if stress is None or stress == 0: stress = summary.get("sts")
        
        # Busca Sport Load (Elite Metrics)
        load_raw = self.get_sport_load(date_str)
        sport_load = None
        if load_raw and "items" in load_raw and load_raw["items"]:
            item = load_raw["items"][0]
            sport_load = {
                "current": item.get("wtlSum"),
                "optimal_min": item.get("wtlSumOptimalMin"),
                "optimal_max": item.get("wtlSumOptimalMax"),
                "status": item.get("wtlStatus")
            }

        # Busca Nutrição (Macros, Logs e ÁGUA)
        nutrition_raw = self.get_daily_nutrition(date_str)
        
        # Tenta também o endpoint de 'Drink' e 'Water' caso existam
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        start_ts = int(dt.timestamp() * 1000)
        end_ts = int((dt.timestamp() + 86400 + 21600) * 1000)
        
        drink_raw = self.fetch_data("/v2/users/me/events", {"eventType": "Drink", "subType": "real_data", "from": start_ts, "to": end_ts})
        water_raw = self.fetch_data("/v2/users/me/events", {"eventType": "Water", "subType": "real_data", "from": start_ts, "to": end_ts})

        nutrition = {
            "calories_in": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "water_litros": 0,
            "meal_logs": []
        }
        
        water_ml = 0
        
        # Processa Nutrição Tradicional
        if nutrition_raw and "items" in nutrition_raw:
            meal_texts = set()
            for item in nutrition_raw["items"]:
                samples = item.get("value", {}).get("samples", [])
                for s in samples:
                    f_name = (s.get("foodName") or "").lower()
                    f_text = (s.get("foodText") or "").lower()
                    
                    if "água" in f_name or "água" in f_text or "water" in f_name:
                        water_ml += s.get("measureWeight", 0)
                        continue
                    
                    nutrition["calories_in"] += s.get("energy", 0)
                    nutrition["protein"] += s.get("protein", 0)
                    nutrition["carbs"] += s.get("carbohydrates", 0)
                    nutrition["fat"] += s.get("fatTotal", 0)
                    nutrition["fiber"] += s.get("fiber", 0)
                    if s.get("foodText"): meal_texts.add(s.get("foodText").strip())
            nutrition["meal_logs"] = list(meal_texts)

        # Processa Eventos de Drink/Water específicos
        for raw in [drink_raw, water_raw]:
            if raw and "items" in raw:
                for item in raw["items"]:
                    val = item.get("value", {})
                    # A Zepp costuma salvar ml em 'value' ou dentro de samples
                    water_ml += val.get("value") or val.get("ml") or val.get("quantity", 0)
                    samples = val.get("samples", [])
                    for s in samples:
                        water_ml += s.get("ml") or s.get("value") or s.get("quantity", 0)

        nutrition["water_litros"] = round(water_ml / 1000, 2)
        # Rounding
        for k in ["calories_in", "protein", "carbs", "fat", "fiber"]:
            nutrition[k] = round(nutrition[k], 1)

        print(f"✅ Debug Final: Steps={steps}, Weight={weight}, RHR={rhr}, PAI={pai}, Stress={stress}, CalIn={nutrition['calories_in']}")

        # Algoritmo Py-Fit Readiness Score (V2)
        pyfit_score = 0
        if sleep and readiness_data:
            s_score = sleep.get("score", 70) or 70
            r_score = readiness_data.get("readiness", 70) or 70
            h_val = hrv or 70
            b_val = readiness_data.get("biocharge_waking", 70) or 70
            
            # Cálculo ponderado ADAPTATIVO
            pyfit_score = (
                (s_score * self.weights.get("sleep_impact", 0.40)) + 
                (r_score * self.weights.get("zepp_readiness", 0.30)) + 
                (min(h_val, 100) * self.weights.get("hrv_impact", 0.20)) + 
                (b_val * self.weights.get("biocharge_waking", 0.10))
            )
            
            # Penalidade de Carga (Overtraining Check)
            if sport_load and sport_load.get("current", 0) > sport_load.get("optimal_max", 1000):
                pyfit_score -= 10
        
        pyfit_score = round(max(0, min(100, pyfit_score)), 1)
        
        # Definição de Status
        status = "Recuperado"
        if pyfit_score < 60: status = "Fadigado"
        elif pyfit_score < 80: status = "Moderado"
        elif pyfit_score >= 90: status = "Elite"

        # Detecção de Treino
        has_workout, workout_info = self.check_workout_on_date(date_str)

        # Retorno consolidado
        return {
            "date": date_str,
            "readiness_index": {
                "score": pyfit_score,
                "status": status,
                "components": {
                    "sleep_impact": sleep.get("score") if sleep else None,
                    "hrv_impact": hrv,
                    "recovery_impact": readiness_data.get("readiness")
                }
            },
            "sleep": sleep,
            "nutrition": nutrition,
            "biometrics": {
                "steps": steps,
                "weight": weight,
                "bmi": bmi,
                "rhr": rhr,
                "hrv": hrv,
                "readiness": readiness_data.get("readiness"),
                "biocharge_waking": readiness_data.get("biocharge_waking"),
                "biocharge_current": readiness_data.get("biocharge_current"),
                "calories": calories,
                "stress": stress,
                "pai": pai,
                "pai_gain": round(pai_gain, 1),
                "workout_detected": has_workout,
                "workout_info": workout_info,
                "sport_load": sport_load
            },
            "api_source": "ZeppCloud"
        }

    def get_workout_history(self, count=20):
        """Pega a lista de treinos recentes via histórico oficial."""
        endpoint = "/v1/sport/run/history.json"
        params = {
            "count": count,
            "userid": self.config["user_id"],
            "appid": "2882303761517383915",
            "v": "2.0"
        }
        return self.fetch_data(endpoint, params=params)

    def check_workout_on_date(self, date_str):
        """Verifica se houve treino na data específica e mapeia o tipo."""
        print(f"🏃‍♂️ Verificando histórico de treinos para {date_str}...")
        history = self.get_workout_history()
        
        # Mapeamento de tipos comuns Zepp/Amazfit
        SPORT_TYPES = {
            1: "Corrida (Rua)",
            6: "Corrida/Caminhada",
            7: "Caminhada",
            8: "Ciclismo",
            18: "Futebol",
            52: "Musculação",
            16: "Treino Livre"
        }

        if not history or "data" not in history or "summary" not in history["data"]:
            return False, None

        for workout in history["data"]["summary"]:
            ts = int(workout.get("end_time", 0))
            if ts > 0:
                w_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                if w_date == date_str:
                    w_type = workout.get("type", 0)
                    type_name = SPORT_TYPES.get(w_type, f"Outro ({w_type})")
                    
                    print(f"✅ Treino detectado: {type_name} as {datetime.fromtimestamp(ts).strftime('%H:%M')}")
                    
                    return True, {
                        "type_id": w_type,
                        "type_name": type_name,
                        "calories": float(workout.get("calorie", 0)),
                        "duration_min": round(int(workout.get("run_time", 0)) / 60, 1),
                        "distance_km": round(float(workout.get("dis", 0)) / 1000, 2) if workout.get("dis") else 0,
                        "avg_hr": float(workout.get("avg_heart_rate", 0)),
                        "load": int(workout.get("exercise_load", 0))
                    }
        return False, None

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
