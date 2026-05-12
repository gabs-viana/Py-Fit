import os
import sys
import json

ROOT_DIR = r"d:\Gabs\Gabs-Dev\Corrida\Py-Fit"
sys.path.append(os.path.join(ROOT_DIR, "src"))

from ingestion.zepp_api import ZeppAPI

api = ZeppAPI()
# Usando a data de hoje para ver os 3, 16 e 13 que o user citou
date_str = "2026-05-12"
load_raw = api.get_sport_load(date_str)

print(json.dumps(load_raw, indent=4))
