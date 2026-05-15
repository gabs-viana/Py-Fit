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
        # Ajuste de Sensibilidade: Se o CTL for muito baixo (< 10), o corpo está em reentrada.
        # Nesses casos, aceitamos TSB mais negativos (até -30) sem disparar alertas críticos.
        is_reentry = ctl < 10
        
        if acwr > 1.5: 
            status = "🚨 ALTÍSSIMO RISCO (Zona de Lesão)"
        elif 0.8 <= acwr <= 1.3: 
            status = "🟢 SWEET SPOT (Evolução Otimizada)"
        elif tsb < -20 and not is_reentry: 
            status = "🟡 FADIGA ACENTUADA (Necessário Tapering)"
        elif tsb < -35 and is_reentry:
            status = "🚨 ALERTA DE REENTRADA AGRESSIVA (Reduza o Ritmo)"
        elif tsb > 5: 
            status = "🚀 SUPERCOMPENSAÇÃO (Pronto para Recordes)"
        else: 
            status = "⚪ MANUTENÇÃO"
        
        return {
            "ctl": round(ctl, 1),
            "atl": round(atl, 1),
            "tsb": round(tsb, 1),
            "acwr": round(acwr, 2),
            "status": status
        }

    def forecast_performance(self, current_metrics, days=3):
        """Projeta o TSB para os próximos N dias assumindo repouso (Zero Load)."""
        forecast = []
        ctl = current_metrics["ctl"]
        atl = current_metrics["atl"]
        
        # Dias da semana em PT-BR
        dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        
        for i in range(1, days + 1):
            # Simulação de Decaimento (Load = 0)
            ctl = ctl * (1 - 1/42)
            atl = atl * (1 - 1/7)
            tsb = ctl - atl
            acwr = atl / max(1, ctl)
            
            # Formata a data com dia da semana (Ex: 14/05 - Qui)
            dt_obj = datetime.now() + timedelta(days=i)
            forecast_date = f"{dt_obj.strftime('%d/%m')} - {dias_semana[dt_obj.weekday()]}"
            
            forecast.append({
                "date": forecast_date,
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

    # Limites de segurança fisiológica por peso (bounds)
    WEIGHT_BOUNDS = {
        "sleep_impact":     (0.45, 0.55),  # Sono é determinante — mínimo alto por decisão do atleta
        "zepp_readiness":   (0.15, 0.45),
        "hrv_impact":       (0.10, 0.35),
        "biocharge_waking": (0.05, 0.20),
    }

    MIN_CALIBRATION_DAYS = 14
    MISMATCH_RATE_THRESHOLD = 0.30
    LEARNING_RATE = 0.02

    def calibrate_weights(self, historical_data, current_weights):
        """
        Ajusta os pesos baseando-se na correlação entre prontidão e performance real.
        
        Guard Clauses:
          - Mínimo de 14 dias de histórico para acionar calibração.
          - Taxa de mismatch > 30% para justificar ajuste.
        
        Returns:
          CalibrationResult dict com metadados de auditoria, ou None se calibração
          não foi acionada (amostra insuficiente ou sistema estável).
        """
        sample_size = len(historical_data)
        
        # ══════════════════════════════════════════════════════
        # GUARD CLAUSE 1: Massa estatística insuficiente
        # ══════════════════════════════════════════════════════
        if sample_size < self.MIN_CALIBRATION_DAYS:
            print(f"🧠 Calibração: N/A (amostra insuficiente — {sample_size}/{self.MIN_CALIBRATION_DAYS} dias)")
            return None

        # ══════════════════════════════════════════════════════
        # COLETA DE EVIDÊNCIAS: Pares (readiness, performance)
        # ══════════════════════════════════════════════════════
        mismatches_pessimista = []  # Sistema subestimou o atleta
        mismatches_otimista = []    # Sistema superestimou o atleta
        total_with_load = 0
        
        adjustments = {k: 0.0 for k in current_weights.keys()}

        for day in historical_data:
            readiness = day.get("readiness_index", {}).get("score", 70)
            workout = day.get("biometrics", {}).get("workout_info")
            load = workout.get("load", 0) if workout else 0

            if load > 0:
                total_with_load += 1
                ctl = day.get("longitudinal", {}).get("tsb", {}).get("ctl", 1)
                perf_ratio = load / max(1, ctl)
                date = day.get("date", "?")

                # Pessimismo: Readiness baixa (<70) mas performance alta (>1.2x CTL)
                if readiness < 70 and perf_ratio > 1.2:
                    mismatches_pessimista.append(date)
                    components = day.get("readiness_index", {}).get("components", {})
                    for comp, val in components.items():
                        if val and val < 60:
                            if comp == "sleep_impact": adjustments["sleep_impact"] -= self.LEARNING_RATE
                            elif comp == "hrv_impact": adjustments["hrv_impact"] -= self.LEARNING_RATE
                            elif comp == "recovery_impact": adjustments["zepp_readiness"] -= self.LEARNING_RATE

                # Otimismo: Readiness alta (>85) mas performance baixa (<0.5x CTL)
                elif readiness > 85 and perf_ratio < 0.5:
                    mismatches_otimista.append(date)
                    components = day.get("readiness_index", {}).get("components", {})
                    for comp, val in components.items():
                        if val and val > 80:
                            if comp == "sleep_impact": adjustments["sleep_impact"] -= self.LEARNING_RATE
                            elif comp == "hrv_impact": adjustments["hrv_impact"] -= self.LEARNING_RATE
                            elif comp == "recovery_impact": adjustments["zepp_readiness"] -= self.LEARNING_RATE

        # ══════════════════════════════════════════════════════
        # GUARD CLAUSE 2: Taxa de mismatch abaixo do threshold
        # ══════════════════════════════════════════════════════
        total_mismatches = len(mismatches_pessimista) + len(mismatches_otimista)
        mismatch_rate = total_mismatches / max(1, total_with_load)
        
        if total_with_load == 0:
            print(f"🧠 Calibração: N/A (nenhum dia com carga de treino no período)")
            return None

        if mismatch_rate < self.MISMATCH_RATE_THRESHOLD:
            print(f"🧠 Calibração: Sistema estável (mismatch {mismatch_rate:.0%} < threshold {self.MISMATCH_RATE_THRESHOLD:.0%})")
            return None

        # ══════════════════════════════════════════════════════
        # APLICAÇÃO DE AJUSTES (com bounds enforcement)
        # ══════════════════════════════════════════════════════
        previous_weights = current_weights.copy()
        new_weights = current_weights.copy()
        
        for k, adj in adjustments.items():
            new_weights[k] = new_weights[k] + adj
            # Clamp dentro dos bounds de segurança
            lo, hi = self.WEIGHT_BOUNDS.get(k, (0.05, 0.55))
            new_weights[k] = max(lo, min(hi, new_weights[k]))

        # Normaliza para soma = 1.0
        total = sum(new_weights.values())
        for k in new_weights:
            new_weights[k] = round(new_weights[k] / total, 3)

        # Determina direção predominante
        direction = "estável"
        if len(mismatches_pessimista) > len(mismatches_otimista):
            direction = "pessimista"
        elif len(mismatches_otimista) > len(mismatches_pessimista):
            direction = "otimista"

        # Log visual
        changed = {k: round(new_weights[k] - previous_weights[k], 3) for k in new_weights if abs(new_weights[k] - previous_weights[k]) > 0.001}
        if changed:
            changes_str = ", ".join([f"{k}: {v:+.3f}" for k, v in changed.items()])
            print(f"🧠 Calibração: Ajustando pesos ({direction}) → {changes_str}")
        else:
            print(f"🧠 Calibração: Mismatch detectado mas bounds impediram ajuste.")

        # ══════════════════════════════════════════════════════
        # RESULTADO COM METADADOS DE AUDITORIA
        # ══════════════════════════════════════════════════════
        from datetime import datetime as dt_now
        return {
            "new_weights": new_weights,
            "calibration_entry": {
                "date": dt_now.now().strftime("%Y-%m-%d"),
                "sample_size": sample_size,
                "days_with_load": total_with_load,
                "mismatch_rate": round(mismatch_rate, 2),
                "direction": direction,
                "adjustments": {k: round(v, 3) for k, v in adjustments.items() if abs(v) > 0.001},
                "previous_weights": previous_weights,
                "trigger": f"mismatch {mismatch_rate:.0%} > threshold {self.MISMATCH_RATE_THRESHOLD:.0%} ({total_mismatches}/{total_with_load} dias)"
            }
        }

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

    # ══════════════════════════════════════════════════════════════
    # NUTRITION INTELLIGENCE ENGINE
    # Fases A (aderência) + B (RNS) + C (longitudinal)
    # ══════════════════════════════════════════════════════════════

    def calculate_nutrition_adherence(self, nutrition_data, targets):
        """
        Fase A — Aderência Diária.

        Compara macros reais vs. metas personalizadas do atleta.
        Regra crítica: min(100, ...) — excesso não é bonificado.
        Calorias e Carbs excluídos (Phase D — requer calibração de TDEE).
        """
        if not nutrition_data or not targets:
            return None

        protein = nutrition_data.get("protein", 0) or 0
        water_litros = nutrition_data.get("water_litros", 0) or 0
        fiber = nutrition_data.get("fiber", 0) or 0

        protein_target = targets.get("protein_target_g", 130)
        water_target_ml = targets.get("water_target_ml", 3500)
        fiber_target = targets.get("fiber_target_g", 25)

        water_actual_ml = water_litros * 1000

        protein_adh = min(100, round((protein / max(1, protein_target)) * 100, 1))
        water_adh = min(100, round((water_actual_ml / max(1, water_target_ml)) * 100, 1))
        fiber_adh = min(100, round((fiber / max(1, fiber_target)) * 100, 1))

        return {
            "protein_g": round(protein, 1),
            "protein_target_g": protein_target,
            "protein_adherence_pct": protein_adh,
            "water_ml": round(water_actual_ml),
            "water_target_ml": water_target_ml,
            "water_adherence_pct": water_adh,
            "fiber_g": round(fiber, 1),
            "fiber_target_g": fiber_target,
            "fiber_adherence_pct": fiber_adh,
        }

    def calculate_rns(self, adherence):
        """
        Fase B — Recovery Nutrition Score (Experimental V1).

        Pesos: Proteína(40%) + Água(35%) + Fibra(25%)
        Carbs excluído: sem target calibrado ainda.

        NOTA DE ARQUITETURA: Os pesos desta versão são heurísticos.
        O sistema aprenderá quais fatores correlacionam mais com readiness
        via Fase C (longitudinal, guard clause de 14 dias).
        Este score NÃO influencia o Risk Score na versão atual.
        Integração ao Risk Score: Phase D (após ≥30 dias de dados + 3 dias consecutivos baixos).
        """
        if not adherence:
            return None

        protein_adh = adherence.get("protein_adherence_pct", 0)
        water_adh = adherence.get("water_adherence_pct", 0)
        fiber_adh = adherence.get("fiber_adherence_pct", 0)

        rns = round(
            (protein_adh * 0.40) +
            (water_adh * 0.35) +
            (fiber_adh * 0.25),
            1
        )

        if rns >= 85:
            status = "Ótimo"
        elif rns >= 70:
            status = "Adequado"
        elif rns >= 55:
            status = "Insuficiente"
        else:
            status = "Crítico"

        return {
            "score": rns,
            "status": status,
            "version": "1.0-experimental",
            "breakdown": {
                "protein_contribution": round(protein_adh * 0.40, 1),
                "water_contribution": round(water_adh * 0.35, 1),
                "fiber_contribution": round(fiber_adh * 0.25, 1),
            }
        }

    def correlate_nutrition_recovery(self, historical_data):
        """
        Fase C — Correlação Longitudinal Nutrição × Recuperação.

        Guard Clause: mínimo 14 dias com dados de nutrição e readiness.
        Detecta:
          - Delta de readiness entre dias com proteína baixa vs. alta
          - Déficit crônico de proteína (7+ dias consecutivos < 85% da meta)
        """
        sample_size = len(historical_data)

        if sample_size < self.MIN_CALIBRATION_DAYS:
            print(f"🥗 Correlação Nutricional: N/A (amostra insuficiente — {sample_size}/{self.MIN_CALIBRATION_DAYS} dias)")
            return None

        LOW_PROTEIN_THRESHOLD = 110   # ~85% de 130g
        HIGH_PROTEIN_THRESHOLD = 130

        low_protein_days = []    # proteína < 110g → abaixo da meta
        high_protein_days = []   # proteína >= 130g → na meta ou acima

        for day in historical_data:
            nutrition = day.get("nutrition", {}) or {}
            readiness = day.get("readiness_index", {}).get("score")
            protein = nutrition.get("protein", 0) or 0

            if readiness and protein > 0:
                entry = {"date": day.get("date", "?"), "readiness": readiness, "protein_g": protein}
                if protein < LOW_PROTEIN_THRESHOLD:
                    low_protein_days.append(entry)
                elif protein >= HIGH_PROTEIN_THRESHOLD:
                    high_protein_days.append(entry)

        avg_low = round(sum(d["readiness"] for d in low_protein_days) / len(low_protein_days), 1) if low_protein_days else None
        avg_high = round(sum(d["readiness"] for d in high_protein_days) / len(high_protein_days), 1) if high_protein_days else None

        # Detect chronic deficit: streak of days below LOW_PROTEIN_THRESHOLD
        chronic_deficit_streak = 0
        for day in sorted(historical_data, key=lambda x: x.get("date", ""), reverse=True):
            protein = (day.get("nutrition", {}) or {}).get("protein", 0) or 0
            if protein < LOW_PROTEIN_THRESHOLD:
                chronic_deficit_streak += 1
            else:
                break

        readiness_delta = round(avg_high - avg_low, 1) if (avg_high is not None and avg_low is not None) else None

        return {
            "sample_size": sample_size,
            "low_protein": {
                "days": len(low_protein_days),
                "avg_readiness": avg_low,
                "threshold_g": LOW_PROTEIN_THRESHOLD
            },
            "high_protein": {
                "days": len(high_protein_days),
                "avg_readiness": avg_high,
                "threshold_g": HIGH_PROTEIN_THRESHOLD
            },
            "readiness_delta_high_vs_low": readiness_delta,
            "chronic_deficit_detected": chronic_deficit_streak >= 7,
            "consecutive_low_protein_days": chronic_deficit_streak
        }

