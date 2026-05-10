import json
import csv
import os
from datetime import datetime, timedelta

class TakeoutNormalizer:
    def __init__(self, takeout_path):
        self.takeout_path = takeout_path
        self.daily_metrics_path = os.path.join(takeout_path, "Métricas de atividades diárias")
        self.sessions_path = os.path.join(takeout_path, "Todas as sessões")
        self.raw_data_path = os.path.join(takeout_path, "Todos os dados")

    def get_daily_csv_data(self, date_str):
        """Extracts metrics from the daily CSV file."""
        file_path = os.path.join(self.daily_metrics_path, f"{date_str}.csv")
        if not os.path.exists(file_path):
            return None

        metrics = {
            "steps": 0,
            "calories": 0,
            "weight": None,
            "min_hr": None
        }

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                hr_samples = []
                for row in reader:
                    # Steps
                    steps = row.get("Contagem de passos", "0")
                    if steps: metrics["steps"] += int(steps)
                    
                    # Calories
                    cals = row.get("Calorias (kcal)", "0")
                    if cals: metrics["calories"] += float(cals)
                    
                    # Weight (get the last non-empty one)
                    w = row.get("Peso médio (kg)")
                    if w: metrics["weight"] = float(w)
                    
                    # Heart Rate
                    min_hr = row.get("Frequência cardíaca mínima (bpm)")
                    if min_hr: hr_samples.append(float(min_hr))
                
                if hr_samples:
                    metrics["min_hr"] = min(hr_samples)
                    
        except Exception as e:
            print(f"Error reading CSV {date_str}: {e}")
            return None
            
        return metrics

    def get_sleep_data(self, date_str):
        """
        Parses sleep segments from raw Huami data.
        Maps: 4 -> Light, 5 -> Deep, 6 -> REM, 1 -> Awake
        """
        # We need to find segments that overlap with the sleep period of the target date
        # Target sleep is usually from night of (date - 1) to morning of (date)
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        sleep_file = os.path.join(self.raw_data_path, "raw_com.google.sleep.segment_com.huami.watch.h.json")
        if not os.path.exists(sleep_file):
            return None

        sleep_stats = {
            "total_hours": 0,
            "deep_sleep_pct": 0,
            "rem_sleep_pct": 0,
            "light_sleep_pct": 0,
            "awake_hours": 0
        }

        try:
            with open(sleep_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            segments = data.get("Data Points", [])
            
            # Stages mapping
            stages = {4: "light", 5: "deep", 6: "rem", 1: "awake"}
            durations = {"light": 0, "deep": 0, "rem": 0, "awake": 0}
            
            for pt in segments:
                start_ns = int(pt["startTimeNanos"])
                end_ns = int(pt["endTimeNanos"])
                val = pt["fitValue"][0]["value"]["intVal"]
                
                # Convert nanos to datetime
                start_dt = datetime.fromtimestamp(start_ns / 1e9)
                
                # Check if this segment belongs to the morning of the target date
                # We consider sleep from 20:00 previous day to 12:00 current day
                prev_day = target_date - timedelta(days=1)
                window_start = prev_day.replace(hour=20, minute=0)
                window_end = target_date.replace(hour=12, minute=0)
                
                if window_start <= start_dt <= window_end:
                    duration_sec = (end_ns - start_ns) / 1e9
                    stage = stages.get(val)
                    if stage:
                        durations[stage] += duration_sec
            
            total_sleep_sec = durations["light"] + durations["deep"] + durations["rem"]
            if total_sleep_sec > 0:
                sleep_stats["total_hours"] = round(total_sleep_sec / 3600, 2)
                sleep_stats["deep_sleep_pct"] = round((durations["deep"] / total_sleep_sec) * 100, 1)
                sleep_stats["rem_sleep_pct"] = round((durations["rem"] / total_sleep_sec) * 100, 1)
                sleep_stats["light_sleep_pct"] = round((durations["light"] / total_sleep_sec) * 100, 1)
                sleep_stats["awake_hours"] = round(durations["awake"] / 3600, 2)
            else:
                return None
                
        except Exception as e:
            print(f"Error reading sleep data: {e}")
            return None
            
        return sleep_stats

    def normalize_day(self, date_str):
        """Aggregates all data for a specific day."""
        csv_data = self.get_daily_csv_data(date_str)
        sleep_data = self.get_sleep_data(date_str)
        
        if not csv_data and not sleep_data:
            return None
            
        return {
            "date": date_str,
            "sleep": sleep_data,
            "biometrics": {
                "steps": csv_data.get("steps") if csv_data else None,
                "calories": round(csv_data.get("calories"), 0) if csv_data else None,
                "rhr": csv_data.get("min_hr") if csv_data else None,
                "weight": csv_data.get("weight") if csv_data else None
            }
        }

if __name__ == "__main__":
    # Test with a known date from the user's files
    norm = TakeoutNormalizer(r"d:\Gabs\Gabs-Dev\Corrida\Py-Fit\Takeout")
    res = norm.normalize_day("2026-03-05")
    print(json.dumps(res, indent=2))
