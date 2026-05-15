import json
import os
import sys
from datetime import datetime

# Ajuste de path para achar os módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from zepp_api import ZeppAPI
from analysis.longitudinal_engine import LongitudinalEngine


def build_prefill(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    output_path = os.path.join(base_dir, "data", "prefill", "prefill_daily.json")
    
    print(f"--- Py-Fit Auto Builder ---")
    print(f"Target Date: {date_str}")
    
    data = None
    # 1. Try Zepp API (Direct Cloud - THE GOLDEN PATH)
    config_path = os.path.join(base_dir, "config", "zepp_config.json")
    if os.path.exists(config_path):
        try:
            print("Trying Zepp Cloud API...")
            api = ZeppAPI(config_path)
            data = api.normalize_for_daily(date_str)
            if data and data.get("sleep"):
                print("✅ SUCCESS: Data retrieved directly from Zepp Cloud.")
                data["confidence"] = 98 # Golden Standard
                
                # Inteligência Longitudinal
                try:
                    engine = LongitudinalEngine(api)
                    baselines, _ = engine.get_historical_baselines(date_str, days=30)
                    trends = engine.analyze_trends(data, baselines)
                    tsb_metrics = engine.get_tsb_metrics(date_str)
                    forecast = engine.forecast_performance(tsb_metrics)
                    signatures = engine.detect_fatigue_signature(trends, tsb_metrics)
                    
                    # --- Plano e Remanejamentos ---
                    training_plan = {}
                    remanejamentos = {}
                    plan_path = os.path.join(base_dir, "config", "training_plan.json")
                    rem_path = os.path.join(base_dir, "data", "database", "remanejamentos.json")
                    
                    if os.path.exists(plan_path):
                        with open(plan_path, 'r', encoding='utf-8') as pf:
                            training_plan = json.load(pf)
                    if os.path.exists(rem_path):
                        with open(rem_path, 'r', encoding='utf-8') as rf:
                            remanejamentos = json.load(rf)
                    
                    data["longitudinal"] = {
                        "baselines_30d": baselines,
                        "trends": trends,
                        "fatigue_signatures": signatures,
                        "tsb": tsb_metrics,
                        "forecast": forecast,
                        "training_plan": training_plan,
                        "remanejamentos": remanejamentos
                    }
                    
                    # --- Aprendizado Adaptativo (Auto-Weight Calibration V2) ---
                    history_dir = os.path.join(base_dir, "data", "history")
                    historical_data = []
                    # Carrega últimos 30 dias para aprendizado (mínimo efetivo: 14)
                    if os.path.exists(history_dir):
                        files = sorted([f for f in os.listdir(history_dir) if f.startswith("daily_")], reverse=True)[:30]
                        for f in files:
                            try:
                                with open(os.path.join(history_dir, f), 'r', encoding='utf-8') as hf:
                                    historical_data.append(json.load(hf))
                            except: pass
                    
                    if historical_data:
                        result = engine.calibrate_weights(historical_data, api.weights)
                        if result is not None:
                            new_weights = result["new_weights"]
                            entry = result["calibration_entry"]
                            print(f"🧠 Adaptando pesos fisiológicos: {new_weights}")
                            
                            # Carrega config existente para preservar log
                            weights_path = os.path.join(base_dir, "config", "pyfit_weights.json")
                            existing_config = {}
                            if os.path.exists(weights_path):
                                try:
                                    with open(weights_path, 'r', encoding='utf-8') as rf:
                                        existing_config = json.load(rf)
                                except: pass
                            
                            # Append ao calibration_log (mantém histórico)
                            cal_log = existing_config.get("calibration_log", [])
                            cal_log.append(entry)
                            # Mantém apenas os últimos 50 registros
                            cal_log = cal_log[-50:]
                            
                            weights_config = {
                                "current_weights": new_weights,
                                "learning_rate": engine.LEARNING_RATE,
                                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                                "version": "2.0",
                                "bounds": dict(engine.WEIGHT_BOUNDS),
                                "calibration_log": cal_log
                            }
                            with open(weights_path, 'w', encoding='utf-8') as wf:
                                json.dump(weights_config, wf, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"⚠️ Erro ao processar tendências: {e}")

                # --- Nutrition Intelligence Engine (Fases A + B + C) ---
                nutrition_targets_path = os.path.join(base_dir, "config", "nutrition_targets.json")
                if os.path.exists(nutrition_targets_path):
                    try:
                        with open(nutrition_targets_path, 'r', encoding='utf-8') as tf:
                            targets = json.load(tf)

                        nutrition_raw = data.get("nutrition", {})
                        adherence = engine.calculate_nutrition_adherence(nutrition_raw, targets)
                        rns = engine.calculate_rns(adherence)

                        # Fase C: correlação longitudinal (14d guard clause)
                        nutrition_correlation = engine.correlate_nutrition_recovery(historical_data) if historical_data else None

                        data["nutrition_analysis"] = {
                            "adherence": adherence,
                            "rns": rns,
                            "longitudinal_correlation": nutrition_correlation
                        }

                        if rns:
                            print(f"🥗 RNS: {rns['score']}/100 ({rns['status']}) [v{rns['version']}]")
                        if adherence:
                            print(f"   → Proteína: {adherence['protein_g']}g / {adherence['protein_target_g']}g ({adherence['protein_adherence_pct']}%)")
                            print(f"   → Água: {adherence['water_ml']}ml / {adherence['water_target_ml']}ml ({adherence['water_adherence_pct']}%)")
                    except Exception as e:
                        print(f"⚠️ Erro no Nutrition Engine: {e}")

            else:
                print("⚠️ Zepp Cloud returned incomplete data. Falling back...")
                data = None
        except Exception as e:
            print(f"❌ Zepp Cloud Error: {e}")
            data = None


    if data:
        # Mapeamento para o Schema do daily.py
        # Consolidação Final
        biometrics = data.get("biometrics", {})
        prefill_data = {
            "date": date_str,
            "readiness_index": data.get("readiness_index"),
            "sleep": {
                "total_hours": data["sleep"].get("total_hours"),
                "rem_sleep_pct": data["sleep"].get("rem_sleep_pct"),
                "deep_sleep_pct": data["sleep"].get("deep_sleep_pct"),
                "light_sleep_pct": data["sleep"].get("light_sleep_pct"),
                "score": data["sleep"].get("score"),
                "insight": data["sleep"].get("insight")
            },
            "nutrition": {
                "calories_in": data.get("nutrition", {}).get("calories_in"),
                "protein": data.get("nutrition", {}).get("protein"),
                "carbs": data.get("nutrition", {}).get("carbs"),
                "fat": data.get("nutrition", {}).get("fat"),
                "fiber": data.get("nutrition", {}).get("fiber"),
                "water_litros": data.get("nutrition", {}).get("water_litros"),
                "meal_logs": data.get("nutrition", {}).get("meal_logs")
            },
            "biometrics": {
                "steps": biometrics.get("steps"),
                "weight": biometrics.get("weight"),
                "bmi": biometrics.get("bmi"),
                "rhr": biometrics.get("rhr"),
                "hrv": biometrics.get("hrv"),
                "readiness": biometrics.get("readiness"),
                "biocharge_waking": biometrics.get("biocharge_waking"),
                "biocharge_current": biometrics.get("biocharge_current"),
                "calories": biometrics.get("calories"),
                "stress": biometrics.get("stress"),
                "pai": biometrics.get("pai"),
                "pai_gain": biometrics.get("pai_gain"),
                "workout_detected": biometrics.get("workout_detected"),
                "workout_info": biometrics.get("workout_info"),
                "sport_load": biometrics.get("sport_load")
            },
            "api_source": data.get("api_source"),
            "longitudinal": data.get("longitudinal"),
            "data_quality": {
                "confidence_score": data.get("confidence", 0),
                "source_fidelity": data.get("api_source", "Unknown"),
                "completeness_check": {
                    "has_hrv": bool(biometrics.get("hrv")),
                    "has_sleep": bool(data.get("sleep")),
                    "has_workout": bool(biometrics.get("workout_detected"))
                }
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(prefill_data, f, indent=2)
            
        # Salva no histórico para aprendizado contínuo
        history_path = os.path.join(base_dir, "data", "history", f"daily_{date_str}.json")
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(prefill_data, f, indent=2)
        print(f"✅ Prefill generated at {output_path}")
        return True
    else:
        print(f"❌ ERROR: No data found for {date_str} in any source.")
        return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    build_prefill(target)
