import os
import sys
import subprocess
from datetime import datetime

# Configuração de caminhos
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INGESTION_DIR = os.path.join(ROOT_DIR, "src", "ingestion")
DAILY_LOG_DIR = os.path.join(ROOT_DIR, "src", "daily_log")

def run_step(name, command):
    print(f"\n--- 🚀 ETAPA: {name} ---")
    try:
        # Usa o mesmo interpretador python atual
        result = subprocess.run([sys.executable] + command, cwd=ROOT_DIR)
        if result.returncode != 0:
            print(f"❌ Erro na etapa {name}. Interrompendo fluxo.")
            return False
        return True
    except Exception as e:
        print(f"❌ Exceção ao executar {name}: {e}")
        return False

def main():
    print("="*50)
    print("      🌪️ PY-FIT MASTER SYNC — INTEGRAÇÃO TOTAL")
    print("="*50)

    # 1. Extração Automática (Zepp Cloud)
    # Pega a data de hoje por padrão
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not run_step("Extração Zepp Cloud", [os.path.join(INGESTION_DIR, "auto_daily_builder.py"), today]):
        sys.exit(1)

    # 2. Log Diário Interativo (Revisão Humana)
    if not run_step("Revisão do Log Diário", [os.path.join(DAILY_LOG_DIR, "daily.py")]):
        sys.exit(1)

    print("\n" + "="*50)
    print("✅ INTEGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("Seus dados fisiológicos e de treino estão sincronizados.")
    print("="*50)

if __name__ == "__main__":
    main()
