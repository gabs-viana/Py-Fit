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
                
                # Inteligência Longitudinal
                try:
                    engine = LongitudinalEngine(api)
                    baselines, _ = engine.get_historical_baselines(date_str, days=30)
                    trends = engine.analyze_trends(data, baselines)
                    signatures = engine.detect_fatigue_signature(trends)
                    
                    data["longitudinal"] = {
                        "baselines_30d": baselines,
                        "trends": trends,
                        "fatigue_signatures": signatures
                    }
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
    
    # 3. Fallback to Takeout
    if not data:
        print(f"Zepp data not found. Falling back to Google Takeout...")
        takeout_path = os.path.join(base_dir, "data", "raw", "Takeout")
        if os.path.exists(takeout_path):
            tnorm = TakeoutNormalizer(takeout_path)
            data = tnorm.normalize_day(date_str)
            if data:
                print(f"SUCCESS: Data retrieved from Google Takeout.")

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
            "nutrition": data.get("nutrition", {}),
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
            "longitudinal": data.get("longitudinal")
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(prefill_data, f, indent=2)
        print(f"✅ Prefill generated at {output_path}")
        return True
    else:
        print(f"❌ ERROR: No data found for {date_str} in any source.")
        return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    build_prefill(target)
