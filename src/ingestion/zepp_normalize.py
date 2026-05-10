import csv
import os
import glob
from datetime import datetime, timedelta

class ZeppNormalizer:
    def __init__(self, zepp_path):
        self.zepp_path = zepp_path

    def _find_csv(self, subfolder):
        """Finds the CSV file in a given subfolder."""
        pattern = os.path.join(self.zepp_path, subfolder, "*.csv")
        files = glob.glob(pattern)
        return files[0] if files else None

    def get_sleep_data(self, date_str):
        """Extracts sleep data for a specific date."""
        csv_file = self._find_csv("SLEEP")
        if not csv_file:
            return None

        try:
            with open(csv_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("date") == date_str:
                        deep = int(row.get("deepSleepTime", 0))
                        rem = int(row.get("REMTime", 0))
                        shallow = int(row.get("shallowSleepTime", 0))
                        total_min = deep + rem + shallow
                        
                        if total_min == 0: return None
                        
                        return {
                            "total_hours": round(total_min / 60, 2),
                            "deep_sleep_pct": round((deep / total_min) * 100, 1),
                            "rem_sleep_pct": round((rem / total_min) * 100, 1),
                            "light_sleep_pct": round((shallow / total_min) * 100, 1),
                            "awake_hours": round(int(row.get("wakeTime", 0)) / 60, 2)
                        }
        except Exception as e:
            print(f"Error reading Zepp SLEEP: {e}")
        return None

    def get_activity_data(self, date_str):
        """Extracts steps and calories."""
        csv_file = self._find_csv("ACTIVITY")
        if not csv_file:
            return None

        try:
            with open(csv_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("date") == date_str:
                        return {
                            "steps": int(row.get("steps", 0)),
                            "calories": int(row.get("calories", 0))
                        }
        except Exception as e:
            print(f"Error reading Zepp ACTIVITY: {e}")
        return None

    def get_weight_data(self, date_str):
        """Extracts weight for the date or the most recent one."""
        csv_file = self._find_csv("BODY")
        if not csv_file:
            return None

        last_weight = None
        try:
            with open(csv_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # time format: 2026-05-04 09:27:32+0000
                    time_val = row.get("time")
                    if not time_val: continue
                    row_date = time_val.split(" ")[0]
                    weight = float(row["weight"]) if row["weight"] and row["weight"] != "null" else None
                    if weight:
                        last_weight = weight
                        if row_date == date_str:
                            return weight
        except Exception as e:
            print(f"Error reading Zepp BODY: {e}")
        return last_weight

    def get_rhr_data(self, date_str):
        """Calculates RHR as the minimum heart rate during sleep window."""
        csv_file = self._find_csv("HEARTRATE_AUTO")
        if not csv_file:
            return None

        hr_values = []
        try:
            with open(csv_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("date") == date_str:
                        # We want the HR during the night. 
                        # Usually RHR is best captured between 02:00 and 06:00.
                        time_str = row.get("time") # HH:MM
                        if not time_str: continue
                        hour = int(time_str.split(":")[0])
                        if 0 <= hour <= 7: # Broad sleep window
                            hr = int(row["heartRate"])
                            if hr > 30: # Filter outliers
                                hr_values.append(hr)
                
                if hr_values:
                    # Return the 5th percentile to avoid single-point glitches
                    hr_values.sort()
                    idx = max(0, int(len(hr_values) * 0.05))
                    return hr_values[idx]
        except Exception as e:
            print(f"Error reading Zepp HEARTRATE_AUTO: {e}")
        return None

    def normalize_day(self, date_str):
        """Aggregates all Zepp data."""
        sleep = self.get_sleep_data(date_str)
        activity = self.get_activity_data(date_str)
        weight = self.get_weight_data(date_str)
        rhr = self.get_rhr_data(date_str)

        if not sleep and not activity:
            return None

        return {
            "date": date_str,
            "sleep": sleep,
            "biometrics": {
                "steps": activity["steps"] if activity else None,
                "calories": activity["calories"] if activity else None,
                "rhr": rhr,
                "weight": weight
            }
        }
