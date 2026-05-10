
import json

def find_val_in_json(obj, target, path=""):
    if obj == target:
        print(f"🎯 ACHEI! Caminho: {path} -> {obj}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            find_val_in_json(v, target, path + f".{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_val_in_json(v, target, path + f"[{i}]")

try:
    with open("scratch/summary_dump.json", "r") as f:
        data = json.load(f)
        print("🔍 Buscando 81 no sumário...")
        find_val_in_json(data, 81)
        print("\n🔍 Buscando 95 no sumário...")
        find_val_in_json(data, 95)
except Exception as e:
    print(f"❌ Erro: {e}")
