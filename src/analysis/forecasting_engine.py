import os
import json
from datetime import datetime, timedelta

class ForecastingEngine:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.pasta_semana = os.path.join(root_dir, "Daily Log", "Semana")
        self.pasta_consolidadas = os.path.join(root_dir, "Daily Log", "Semanas_consolidadas")

    def load_historical_loads(self):
        """
        Carrega as cargas diárias de treino (sport_load -> current) de todo o histórico.
        Retorna um dict onde a chave é a data (YYYY-MM-DD) e o valor é a carga.
        """
        cargas = {}
        # 1. Carregar das Semanas Consolidadas
        if os.path.exists(self.pasta_consolidadas):
            for semana_dir in os.listdir(self.pasta_consolidadas):
                caminho_semana = os.path.join(self.pasta_consolidadas, semana_dir)
                if not os.path.isdir(caminho_semana):
                    continue
                for arq in os.listdir(caminho_semana):
                    if arq.endswith(".json") and arq != "resumo.json" and not arq.startswith("contexto_"):
                        try:
                            with open(os.path.join(caminho_semana, arq), "r", encoding="utf-8") as f:
                                d = json.load(f)
                                dt_str = datetime.strptime(d["data"], "%d/%m/%Y").strftime("%Y-%m-%d")
                                # 1. Prioridade absoluta: Se não executou treino, carga produzida = 0
                                treino = d.get("treino", {})
                                bio = d.get("biometrics", {})
                                workout_info = bio.get("workout_info")
                                
                                if treino.get("executado") == "n":
                                    load = 0
                                elif workout_info and workout_info.get("load"):
                                    # 2. Usa a carga oficial calculada pela Zepp para aquele treino específico
                                    load = workout_info.get("load")
                                else:
                                    # 3. Fallback: Heurística por intensidade
                                    load = treino.get("intensidade", 0) * 10
                                
                                cargas[dt_str] = load
                        except Exception:
                            pass
                            
        # 2. Carregar da Semana Atual (pasta viva)
        if os.path.exists(self.pasta_semana):
            for arq in os.listdir(self.pasta_semana):
                if arq.endswith(".json"):
                    try:
                        with open(os.path.join(self.pasta_semana, arq), "r", encoding="utf-8") as f:
                            d = json.load(f)
                            dt_str = datetime.strptime(d["data"], "%d/%m/%Y").strftime("%Y-%m-%d")
                            treino = d.get("treino", {})
                            bio = d.get("biometrics", {})
                            workout_info = bio.get("workout_info")
                            
                            if treino.get("executado") == "n":
                                load = 0
                            elif workout_info and workout_info.get("load"):
                                load = workout_info.get("load")
                            else:
                                load = treino.get("intensidade", 0) * 10
                                    
                            cargas[dt_str] = load
                    except Exception:
                        pass
        return cargas

    def calculate_tsb(self, target_date=None, data_dict=None):
        """
        Calcula o TSB (Training Stress Balance) usando a lógica de 
        Média Móvel Exponencial (EWMA) - Padrão da Indústria.
        """
        if data_dict is None:
            data_dict = self.load_historical_loads()
            
        if not data_dict:
            return None, None, None
            
        datas_disponiveis = sorted(list(data_dict.keys()))
        if not datas_disponiveis:
            return None, None, None
            
        if target_date is None:
            target_date = datetime.strptime(datas_disponiveis[-1], "%Y-%m-%d")
            
        # Para EWMA, precisamos processar a sequência desde o início
        # até a data alvo para acumular o Fitness e a Fadiga.
        primeira_data = datetime.strptime(datas_disponiveis[0], "%Y-%m-%d")
        
        atl = 0
        ctl = 0
        
        # Iteramos dia a dia desde o início até o target_date
        curr_dt = primeira_data
        while curr_dt <= target_date:
            dt_str = curr_dt.strftime("%Y-%m-%d")
            carga_dia = data_dict.get(dt_str, 0) # Se não tem log, carga é 0 (descanso)
            
            # Constantes de decaimento (7 dias para fadiga, 42 para fitness)
            atl = atl + (carga_dia - atl) / 7
            ctl = ctl + (carga_dia - ctl) / 42
            
            curr_dt += timedelta(days=1)
            
        tsb = ctl - atl
        
        return round(atl, 1), round(ctl, 1), round(tsb, 1)

    def prever_proximos_dias(self, dias=3):
        """
        Simula os próximos X dias assumindo que não haverá treino (carga 0).
        Retorna uma lista de previsões com mensagens de alerta.
        """
        cargas = self.load_historical_loads()
        if not cargas:
            return []
            
        ultima_data_str = sorted(list(cargas.keys()))[-1]
        ultima_data = datetime.strptime(ultima_data_str, "%Y-%m-%d")
        
        previsoes = []
        for i in range(1, dias + 1):
            dia_futuro = ultima_data + timedelta(days=i)
            dia_futuro_str = dia_futuro.strftime("%Y-%m-%d")
            cargas[dia_futuro_str] = 0  # Assumindo descanso / decaimento
            
            atl, ctl, tsb = self.calculate_tsb(dia_futuro, cargas)
            
            if tsb > 5:
                status = "🚀 Supercompensação! Pico de performance."
            elif tsb < -15:
                status = "⚠️ Alto Risco de Lesão! Mantenha treinos leves (Tapering)."
            elif tsb >= 0:
                status = "✅ Frescor recuperado. Pronto para carga."
            else:
                status = "🟡 Absorvendo carga."
                
            previsoes.append({
                "data": dia_futuro.strftime("%d/%m/%Y"),
                "tsb": tsb,
                "status": status
            })
            
        return previsoes
