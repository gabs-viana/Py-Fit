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
        
        # 1. RHR e PAI (Vem do endpoint de events que já buscamos 3000 itens)
        # Para ser mais eficiente, buscamos via PaiHealthInfo range
        pai_data = self.api.get_pai_info(str(int(start_dt.timestamp() * 1000)))
        
        # 2. Stress Range
        stress_data = self.api.get_all_day_stress(start_str, end_str)
        
        # 3. Readiness e HRV Range
        readiness_raw = self.api.get_readiness_score(start_str, end_str)
        
        # Processamento
        rhrs = []
        hrvs = []
        stress_vals = []
        readiness_vals = []
        
        # Parse PAI/RHR
        if pai_data and "items" in pai_data:
            for item in pai_data["items"]:
                rhr = item.get("restHr")
                if rhr and int(rhr) > 0:
                    rhrs.append(int(rhr))
        
        # Parse Stress
        if stress_data and "items" in stress_data:
            for item in stress_data["items"]:
                val = item.get("value", {}).get("avgStress")
                if val and int(val) > 0:
                    stress_vals.append(int(val))
                    
        # Parse Readiness/HRV
        if readiness_raw and "readiness" in readiness_raw:
            items = readiness_raw["readiness"].get("items", [])
            for item in items:
                val = item.get("value", {})
                hrv = val.get("sleepHRV") or val.get("hrvScore")
                rdns = val.get("rdnsScore")
                if hrv: hrvs.append(int(hrv))
                if rdns: readiness_vals.append(int(rdns))

        # Cálculo das Médias (Baselines)
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

    def detect_fatigue_signature(self, trends):
        """Identifica assinaturas fisiológicas de fadiga ou recuperação."""
        signatures = []
        
        hrv_trend = trends.get("hrv", {}).get("direction")
        rhr_trend = trends.get("rhr", {}).get("direction")
        stress_trend = trends.get("stress", {}).get("direction")
        readiness_trend = trends.get("readiness", {}).get("direction")
        
        # 1. Fadiga Simpática (HRV Down + RHR Up + Stress Up)
        if hrv_trend == "down" and rhr_trend == "up":
            signatures.append("Fadiga Simpática: Sistema nervoso sobrecarregado.")
            
        # 2. Supercompensação (HRV Up + RHR Down)
        if hrv_trend == "up" and rhr_trend == "down":
            signatures.append("Supercompensação: Pronto para intensidade máxima.")
            
        # 3. Stress Social/Metabólico (Stress Up + HRV Down)
        if stress_trend == "up" and hrv_trend == "down":
            signatures.append("Estresse Sistêmico: Possível impacto de sono ruim ou inflamação.")

        # 4. OVERTRAINING / OVERREACHING
        if hrv_trend == "down" and readiness_trend == "down":
            signatures.append("🚨 ALERTA DE OVERTRAINING: Queda simultânea de HRV e Prontidão! Risco iminente de lesão/overreaching.")

        return signatures
