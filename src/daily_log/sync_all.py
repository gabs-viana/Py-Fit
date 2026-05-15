import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Configuração de caminhos (pathlib)
ROOT_DIR = Path(__file__).resolve().parents[2]
INGESTION_DIR = ROOT_DIR / "src" / "ingestion"
DAILY_LOG_DIR = ROOT_DIR / "src" / "daily_log"
ANALYSIS_DIR = ROOT_DIR / "src" / "analysis"

# Pipeline Status Tracker
pipeline_status = {}

def run_step(name, command, critical=True):
    """Executa uma etapa do pipeline com captura de output."""
    print(f"\n--- 🚀 ETAPA: {name} ---")
    try:
        result = subprocess.run(
            [sys.executable] + [str(c) for c in command],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True
        )
        
        # Exibe output capturado
        if result.stdout:
            print(result.stdout.rstrip())
        if result.stderr:
            print(result.stderr.rstrip())
        
        if result.returncode != 0:
            pipeline_status[name] = "❌ ERRO"
            if critical:
                print(f"❌ Erro crítico na etapa {name}. Interrompendo fluxo.")
                return False
            else:
                print(f"⚠️ {name} falhou, mas não é crítico. Continuando em modo degradado.")
                return False
        
        pipeline_status[name] = "✅ OK"
        return True
    except Exception as e:
        pipeline_status[name] = "❌ EXCEÇÃO"
        print(f"❌ Exceção ao executar {name}: {e}")
        if critical:
            return False
        return False

def escolher_data_sync():
    """Permite escolher data para sincronização (alinhado com o daily.py)."""
    print("\nData alvo:")
    print("  0 - Hoje")
    print("  9 - Escolher manual (YYYY-MM-DD)")
    
    while True:
        val = input("Escolha: ").strip()
        if val == "0":
            return datetime.now().strftime("%Y-%m-%d")
        if val == "9":
            while True:
                data = input("Digite a data (YYYY-MM-DD): ").strip()
                try:
                    datetime.strptime(data, "%Y-%m-%d")
                    return data
                except:
                    print("Formato inválido.")
        print("Opção inválida.")

def exibir_resumo():
    """Exibe o resumo final do pipeline."""
    print("\n" + "═"*50)
    print("  📊 PIPELINE STATUS")
    print("═"*50)
    for etapa, status in pipeline_status.items():
        print(f"  {etapa:30s} {status}")
    print("═"*50)

def main():
    print("="*50)
    print("      🌪️  PY-FIT MASTER SYNC — INTEGRAÇÃO TOTAL")
    print("="*50)

    # 0. Escolher data alvo (alinhamento entre todas as etapas)
    target_date = escolher_data_sync()
    print(f"\n🎯 Data alvo: {target_date}")

    # 1. Extração Automática (Zepp Cloud)
    if not run_step("Extração Zepp Cloud", [INGESTION_DIR / "auto_daily_builder.py", target_date]):
        exibir_resumo()
        sys.exit(1)

    # 2. Sentinel Autônomo (O Guardião) — NÃO CRÍTICO
    run_step(
        "Sentinel Guardião (Pre-Review)",
        [ANALYSIS_DIR / "ai_coach.py", "--mode", "guard"],
        critical=False
    )

    # 3. Log Diário Interativo (Revisão Humana)
    # Execução direta para capturar código de saída específico (99 = Snapshot)
    print(f"\n--- 🚀 ETAPA: Revisão do Log Diário ---")
    daily_process = subprocess.run(
        [sys.executable, str(DAILY_LOG_DIR / "daily.py")],
        cwd=str(ROOT_DIR)
    )
    
    if daily_process.returncode == 99:
        pipeline_status["Revisão do Log Diário"] = "💾 SNAPSHOT"
        print("\n💾 Snapshot salvo com sucesso. O Veredito do Coach será gerado apenas no fechamento final (Opção 0).")
        print("Até mais tarde, Gabs!")
        exibir_resumo()
        sys.exit(0)
    elif daily_process.returncode != 0:
        pipeline_status["Revisão do Log Diário"] = "❌ ERRO"
        print(f"❌ Erro na etapa Revisão do Log Diário.")
        exibir_resumo()
        sys.exit(1)
    else:
        pipeline_status["Revisão do Log Diário"] = "✅ OK"

    # 4. Coach AI (O Mentor) — NÃO CRÍTICO
    run_step(
        "Veredito do Coach (Post-Review)",
        [ANALYSIS_DIR / "ai_coach.py", "--mode", "coach"],
        critical=False
    )

    # RESUMO FINAL
    exibir_resumo()
    print("✅ INTEGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("Seus dados fisiológicos e de treino estão sincronizados.")

if __name__ == "__main__":
    main()
