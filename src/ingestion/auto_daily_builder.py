import json
import os
import sys
from datetime import datetime

# Ajuste de path para achar os módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from normalize import TakeoutNormalizer
from zepp_normalize import ZeppNormalizer
from zepp_api import ZeppAPI
from analysis.longitudinal_engine import LongitudinalEngine

def find_zepp_folder(base_dir):
    """Finds a folder that looks like a Zepp export."""
    # Priority 1: Explicitly named ZeppExport
    path = os.path.join(base_dir, "ZeppExport")
    if os.path.exists(path) and os.path.isdir(path):
        if os.path.exists(os.path.join(path, "SLEEP")):
            return path
            
    # Priority 2: Numeric folder with underscore (default Zepp export name)
    for item in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, item)):
            if "_" in item and item.split("_")[0].isdigit():
                if os.path.exists(os.path.join(base_dir, item, "SLEEP")):
                    return os.path.join(base_dir, item)
    return None

def build_prefill(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    output_path = os.path.join(base_dir, "data", "prefill", "prefill_daily.json")
    
    print(f"--- Py-Fit Auto Builder ---")
    print(f"Target Date: {date_str}")
    
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
                    
                    data["longitudinal"] = {
                        "baselines_30d": baselines,
                        "trends": trends,
                        "fatigue_signatures": signatures,
                        "tsb": tsb_metrics,
                        "forecast": forecast
                    }
                    
                    # --- Aprendizado Adaptativo ---
                    history_dir = os.path.join(base_dir, "data", "history")
                    historical_data = []
                    # Carrega últimos 14 dias para aprendizado
                    if os.path.exists(history_dir):
                        files = sorted([f for f in os.listdir(history_dir) if f.startswith("daily_")], reverse=True)[:14]
                        for f in files:
                            try:
                                with open(os.path.join(history_dir, f), 'r', encoding='utf-8') as hf:
                                    historical_data.append(json.load(hf))
                            except: pass
                    
                    if historical_data:
                        new_weights = engine.calibrate_weights(historical_data, api.weights)
                        if new_weights != api.weights:
                            print(f"🧠 Adaptando pesos fisiológicos: {new_weights}")
                            weights_config = {
                                "current_weights": new_weights,
                                "learning_rate": 0.02,
                                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                                "version": "1.1"
                            }
                            with open(os.path.join(base_dir, "config", "pyfit_weights.json"), 'w') as wf:
                                json.dump(weights_config, wf, indent=2)
                except Exception as e:
                    print(f"⚠️ Erro ao processar tendências: {e}")
            else:
                print("⚠️ Zepp Cloud returned incomplete data. Falling back...")
                data = None
        except Exception as e:
            print(f"❌ Zepp Cloud Error: {e}")
            data = None

    # 2. Try Local Zepp Export (High Fidelity Backup)
    if not data:
        # Busca na pasta data/raw
        raw_dir = os.path.join(base_dir, "data", "raw")
        zepp_folder = find_zepp_folder(raw_dir)
        if zepp_folder:
            print(f"Found Local Zepp Export: {os.path.basename(zepp_folder)}")
            znorm = ZeppNormalizer(zepp_folder)
            data = znorm.normalize_day(date_str)
            if data:
                print("✅ SUCCESS: Data retrieved from Local Zepp Export.")
                data["confidence"] = 85 # High Fidelity but asynchronous
    
    # 3. Fallback to Takeout
    if not data:
        print(f"Zepp data not found. Falling back to Google Takeout...")
        takeout_path = os.path.join(base_dir, "data", "raw", "Takeout")
        if os.path.exists(takeout_path):
            tnorm = TakeoutNormalizer(takeout_path)
            data = tnorm.normalize_day(date_str)
            if data:
                print(f"SUCCESS: Data retrieved from Google Takeout.")
                data["confidence"] = 60 # Estimated / Fallback

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
