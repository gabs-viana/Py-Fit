import os
import sys
import json

ROOT_DIR = r"d:\Gabs\Gabs-Dev\Corrida\Py-Fit"
sys.path.append(os.path.join(ROOT_DIR, "src"))

from ingestion.zepp_api import ZeppAPI

api = ZeppAPI()
date_str = "2026-05-12"

endpoints = [
    "SPORT_LOAD",
    "VO2_MAX",
    "TRAINING_LOAD",
    "EPOC",
    "TRAINING_STATUS"
]

results = {}
for ep in endpoints:
    url = f"/watch/users/{api.config['user_id']}/WatchSportStatistics/{ep}"
    params = {"startDay": date_str, "endDay": date_str, "userid": api.config['user_id']}
    try:
        results[ep] = api.fetch_data(url, params)
    except:
        results[ep] = "Error/Not Found"

print(json.dumps(results, indent=4))
