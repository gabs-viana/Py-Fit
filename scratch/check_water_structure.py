import os
import sys
import json
from datetime import datetime
import time

# Ajuste de path para achar os módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ingestion.zepp_api import ZeppAPI

def list_all_food():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    config_path = os.path.join(base_dir, "config", "zepp_config.json")
    api = ZeppAPI(config_path)
    
    for i in range(3):
        date_dt = datetime.now() - timedelta(days=i)
        date_str = date_dt.strftime("%Y-%m-%d")
        start_ts = int(time.mktime(date_dt.replace(hour=0, minute=0, second=0, microsecond=0).timetuple()) * 1000)
        end_ts = int(start_ts + 86400 * 1000 + 43200 * 1000)
        
        print(f"\n--- Checking Food for date: {date_str} ---")
        params = {
            "limit": 100,
            "subType": "real_data",
            "eventType": "Food",
            "from": start_ts,
            "to": end_ts,
            "reverse": "true"
        }
        data = api.fetch_data("/v2/users/me/events", params)
        if data and "items" in data:
            for item in data["items"]:
                samples = item.get("value", {}).get("samples", [])
                for s in samples:
                    name = s.get("foodName", "")
                    text = s.get("foodText", "")
                    print(f" - [{date_str}] Name: {name} | Text: {text}")
                    if "água" in name.lower() or "água" in text.lower() or "water" in name.lower():
                        print(f"⭐ FOUND WATER LOG: {json.dumps(s, indent=2)}")

if __name__ == "__main__":
    from datetime import timedelta
    list_all_food()
