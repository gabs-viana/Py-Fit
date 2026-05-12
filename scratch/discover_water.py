import os
import sys
import json
from datetime import datetime

# Ajuste de path para achar os módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ingestion.zepp_api import ZeppAPI

def discover_water():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    config_path = os.path.join(base_dir, "config", "zepp_config.json")
    
    api = ZeppAPI(config_path)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"--- listing all v1 events for {date_str} ---")
    # Endpoint: /users/ID/events
    endpoint = f"/users/{api.config['user_id']}/events"
    params = {
        "startDate": date_str,
        "endDate": date_str
    }
    data = api.fetch_data(endpoint, params)
    if data and "items" in data:
        print(f"Found {len(data['items'])} items")
        types = {}
        for item in data["items"]:
            e_type = item.get("eventType")
            types[e_type] = types.get(e_type, 0) + 1
            item_str = json.dumps(item).lower()
            if any(x in item_str for x in ["water", "drink", "aqua", "ml", "liquid"]):
                 print(f"DEBUG: Found possible water event ({e_type}): {json.dumps(item, indent=2)}")
        
        print("Summary of types found:")
        for t, count in types.items():
            print(f" - {t}: {count}")
    else:
        print("No events found in v1")

if __name__ == "__main__":
    discover_water()
