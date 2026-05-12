import os
import sys

ROOT_DIR = r"d:\Gabs\Gabs-Dev\Corrida\Py-Fit"
sys.path.append(os.path.join(ROOT_DIR, "src"))

from analysis.forecasting_engine import ForecastingEngine

engine = ForecastingEngine(ROOT_DIR)
cargas = engine.load_historical_loads()

print(f"Cargas encontradas ({len(cargas)}):")
for dt, val in sorted(cargas.items()):
    print(f"  {dt}: {val}")

atl, ctl, tsb = engine.calculate_tsb()
print(f"\nFinal -> ATL: {atl}, CTL: {ctl}, TSB: {tsb}")

previsoes = engine.prever_proximos_dias(3)
print("\nPrevisões:")
for p in previsoes:
    print(f"  {p}")
