from datetime import datetime, timedelta

class LongitudinalEngine:
    def __init__(self, api_client):
        self.api = api_client

    def get_historical_baselines(self, target_date, days=30):
        """Calcula as métricas base (Baselines) dos últimos N dias."""
        end_dt = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)
        start_dt = end_dt - timedelta(days=days-1)
        
        start_str = start_dt.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")
        
        print(f"📊 Analisando tendências históricas de {start_str} até {end_str}...")
        
        # 1. RHR e PAI
        pai_data = self.api.get_pai_info(str(int(start_dt.timestamp() * 1000)))
        
        # 2. Stress Range
        stress_data = self.api.get_all_day_stress(start_str, end_str)
        
        # 3. Readiness e HRV Range
        readiness_raw = self.api.get_readiness_score(start_str, end_str)
        
        rhrs = []
        hrvs = []
        stress_vals = []
        readiness_vals = []
        
        if pai_data and "items" in pai_data:
            for item in pai_data["items"]:
                rhr = item.get("restHr")
                if rhr and int(rhr) > 0:
                    rhrs.append(int(rhr))
        
        if stress_data and "items" in stress_data:
            for item in stress_data["items"]:
                val = item.get("value", {}).get("avgStress")
                if val and int(val) > 0:
                    stress_vals.append(int(val))
                    
        if readiness_raw and "readiness" in readiness_raw:
            items = readiness_raw["readiness"].get("items", [])
            for item in items:
                val = item.get("value", {})
                hrv = val.get("sleepHRV") or val.get("hrvScore")
                rdns = val.get("rdnsScore")
                if hrv: hrvs.append(int(hrv))
                if rdns: readiness_vals.append(int(rdns))

        baselines = {
            "hrv": round(sum(hrvs) / len(hrvs), 1) if hrvs else None,
            "rhr": round(sum(rhrs) / len(rhrs), 1) if rhrs else None,
            "stress": round(sum(stress_vals) / len(stress_vals), 1) if stress_vals else None,
            "readiness": round(sum(readiness_vals) / len(readiness_vals), 1) if readiness_vals else None
        }
        
        return baselines, {
            "hrv_list": hrvs,
            "rhr_list": rhrs,
            "stress_list": stress_vals,
            "readiness_list": readiness_vals
        }

    def analyze_trends(self, today_data, baselines):
        """Compara hoje com as baselines e gera as tendências."""
        trends = {}
        biometrics = today_data.get("biometrics", {})
        
        metrics = [
            ("hrv", biometrics.get("hrv")),
            ("rhr", biometrics.get("rhr")),
            ("stress", biometrics.get("stress")),
            ("readiness", biometrics.get("readiness"))
        ]
        
        for key, current in metrics:
            base = baselines.get(key)
            if current and base:
                diff_pct = ((current - base) / base) * 100
                trends[key] = {
                    "current": current,
                    "baseline": base,
                    "diff_pct": round(diff_pct, 1),
                    "direction": "up" if diff_pct > 2 else ("down" if diff_pct < -2 else "stable")
                }
        
        return trends

    def get_tsb_metrics(self, target_date):
        """Calcula as métricas de TSB (Training Stress Balance) com foco em ACWR."""
        end_dt = datetime.strptime(target_date, "%Y-%m-%d")
        # Janela de 42 dias para o CTL (Padrão Global)
        start_dt = end_dt - timedelta(days=41)
        
        start_str = start_dt.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")
        
        print(f"📈 Calculando TSB (Stress Balance) desde {start_str}...")
        
        endpoint = f"/watch/users/{self.api.config['user_id']}/WatchSportStatistics/SPORT_LOAD"
        params = {
            "startDay": start_str,
            "endDay": end_str,
            "userid": self.api.config["user_id"]
        }
        raw_load = self.api.fetch_data(endpoint, params)
        
        load_map = {}
        if raw_load and "items" in raw_load:
            for item in raw_load["items"]:
                day = item.get("dayId")
                load_map[day] = item.get("currnetDayTrainLoad", 0)
        
        loads = []
        for i in range(42):
            day_str = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            loads.append(load_map.get(day_str, 0))
            
        atl = 0
        ctl = 0
        for load in loads:
            atl = atl + (load - atl) / 7
            ctl = ctl + (load - ctl) / 42
            
        tsb = ctl - atl
        acwr = atl / max(1, ctl)
        
        # Status Elite (ACWR é o parâmetro principal de risco)
        if acwr > 1.5: status = "🚨 ALTÍSSIMO RISCO (Zona de Lesão)"
        elif 0.8 <= acwr <= 1.3: status = "🟢 SWEET SPOT (Evolução Otimizada)"
        elif tsb < -20: status = "🟡 FADIGA ACENTUADA (Necessário Tapering)"
        elif tsb > 5: status = "🚀 SUPERCOMPENSAÇÃO (Pronto para Recordes)"
        else: status = "⚪ MANUTENÇÃO"
        
        return {
            "ctl": round(ctl, 1),
            "atl": round(atl, 1),
            "tsb": round(tsb, 1),
            "acwr": round(acwr, 2),
            "status": status
        }

    def forecast_performance(self, current_metrics, days=5):
        """Projeta o TSB para os próximos N dias assumindo repouso (Zero Load)."""
        forecast = []
        ctl = current_metrics["ctl"]
        atl = current_metrics["atl"]
        
        for i in range(1, days + 1):
            # Simulação de Decaimento (Load = 0)
            ctl = ctl * (1 - 1/42)
            atl = atl * (1 - 1/7)
            tsb = ctl - atl
            acwr = atl / max(1, ctl)
            
            forecast.append({
                "day": i,
                "tsb": round(tsb, 1),
                "acwr": round(acwr, 2)
            })
            
        # Calcula Carga Máxima Recomendada para amanhã (ACWR Limit 1.3)
        # ACWR_tomorrow = (ATL_today * (6/7) + NEW_LOAD * (1/7)) / CTL_tomorrow
        # Isolando NEW_LOAD para ACWR = 1.3
        ctl_tomorrow = current_metrics["ctl"] * (1 - 1/42)
        limit_load = (1.3 * ctl_tomorrow - (current_metrics["atl"] * 6/7)) * 7
        
        return {
            "rest_projection": forecast,
            "max_safe_load_tomorrow": round(max(0, limit_load), 0)
        }

    def calibrate_weights(self, historical_data, current_weights):
        """
        Ajusta os pesos baseando-se na correlação entre prontidão e performance real.
        """
        learning_rate = 0.02 # Mudança gradual para evitar instabilidade
        adjustments = {k: 0 for k in current_weights.keys()}
        
        # Analisa os últimos dias de dados processados
        for day in historical_data:
            readiness = day.get("readiness_index", {}).get("score", 70)
            workout = day.get("biometrics", {}).get("workout_info", {})
            load = workout.get("load", 0) if workout else 0
            
            if load > 0:
                # Performance Ratio: Quão acima da média (CTL) o treino foi?
                ctl = day.get("longitudinal", {}).get("tsb", {}).get("ctl", 1)
                perf_ratio = load / max(1, ctl)
                
                # Mismatch Check: Readiness baixa (<70) mas performance alta (>1.2x CTL)
                if readiness < 70 and perf_ratio > 1.2:
                    # O sistema foi muito pessimista. Precisamos identificar quem 'mentiu'.
                    components = day.get("readiness_index", {}).get("components", {})
                    for comp, val in components.items():
                        if val and val < 60: # Este componente estava baixo, mas o treino foi bom
                            # Reduz o peso deste componente mentiroso
                            if comp == "sleep_impact": adjustments["sleep_impact"] -= learning_rate
                            elif comp == "hrv_impact": adjustments["hrv_impact"] -= learning_rate
                            elif comp == "recovery_impact": adjustments["zepp_readiness"] -= learning_rate
                
                # Mismatch Check: Readiness alta (>85) mas performance baixa (<0.5x CTL)
                elif readiness > 85 and perf_ratio < 0.5:
                    # O sistema foi muito otimista.
                    components = day.get("readiness_index", {}).get("components", {})
                    for comp, val in components.items():
                        if val and val > 80: # Este componente estava alto, mas o treino foi ruim
                            # Reduz o peso deste componente excessivamente otimista
                            if comp == "sleep_impact": adjustments["sleep_impact"] -= learning_rate
                            elif comp == "hrv_impact": adjustments["hrv_impact"] -= learning_rate
                            elif comp == "recovery_impact": adjustments["zepp_readiness"] -= learning_rate

        # Aplica ajustes e normaliza para soma = 1.0
        new_weights = current_weights.copy()
        for k, v in adjustments.items():
            new_weights[k] = max(0.05, new_weights[k] + v) # Mínimo de 5% de peso
            
        total = sum(new_weights.values())
        for k in new_weights:
            new_weights[k] = round(new_weights[k] / total, 3)
            
        return new_weights

    def detect_fatigue_signature(self, trends, tsb_metrics=None):
        """Identifica assinaturas fisiológicas cruzando biometria e carga."""
        signatures = []
        
        hrv_trend = trends.get("hrv", {}).get("direction")
        rhr_trend = trends.get("rhr", {}).get("direction")
        readiness_trend = trends.get("readiness", {}).get("direction")
        
        tsb = tsb_metrics.get("tsb", 0) if tsb_metrics else 0
        acwr = tsb_metrics.get("acwr", 0) if tsb_metrics else 1.0
        
        # 1. Fadiga de Carga (TSB Down + ACWR High + HRV Down)
        if tsb < -15 and acwr > 1.3 and hrv_trend == "down":
            signatures.append("Fadiga de Impacto: Carga acumulada muito rápida. Alto risco de estresse sistêmico.")
            
        # 2. Desequilíbrio Simpático (HRV Down + RHR Up)
        if hrv_trend == "down" and rhr_trend == "up":
            signatures.append("Desequilíbrio Simpático: O corpo está lutando para recuperar o básico.")
            
        # 3. Supercompensação (HRV Up + RHR Down + TSB Positivo)
        if hrv_trend == "up" and rhr_trend == "down" and tsb >= 0:
            signatures.append("Janela de Performance: Momento ideal para teste de carga ou prova.")
            
        # 4. ALERTA CRÍTICO: Overtraining / Crash
        if tsb < -25 and hrv_trend == "down" and readiness_trend == "down":
            signatures.append("🚨 COLAPSO IMINENTE: TSB, HRV e Prontidão em queda livre. Pise no freio IMEDIATAMENTE.")
            
        return signatures
