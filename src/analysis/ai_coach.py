import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Ajuste de path para achar os módulos internos (src/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Carrega variáveis de ambiente (.env)
load_dotenv()

# Provider Layer — Sentinel nunca importa OpenAI diretamente
from core.llm_provider import get_provider
from core.tool_utils import build_tool_result_message
provider = get_provider()

# Caminhos de arquivos
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROMPT_PATH = os.path.join(ROOT_DIR, "Docs", "COACH_PROMPT.md")
PREFILL_DATA_PATH = os.path.join(ROOT_DIR, "data", "prefill", "prefill_daily.json")
FINAL_DATA_DIR = os.path.join(ROOT_DIR, "Daily Log", "Semana")
BRAIN_PATH = os.path.join(ROOT_DIR, "data", "database", "athlete_brain.json")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sugerir_remanejamento_treino",
            "description": "Sugere fortemente uma alteração no treino de amanhã devido a fadiga (TSB negativo) ou risco de lesão (ACWR > 1.5).",
            "parameters": {
                "type": "object",
                "properties": {
                    "novo_treino": {
                        "type": "string",
                        "description": "O tipo de treino recomendado para amanhã (ex: 'Descanso', 'Recovery Run', 'Mobilidade')."
                    },
                    "justificativa": {
                        "type": "string",
                        "description": "A justificativa sádico-construtiva de por que a carga deve ser reduzida."
                    }
                },
                "required": ["novo_treino", "justificativa"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ajustar_meta_agua",
            "description": "Ajusta a meta de hidratação para o dia seguinte se houver perda de suor detectada ou baixa ingestão.",
            "parameters": {
                "type": "object",
                "properties": {
                    "litros": {
                        "type": "number",
                        "description": "A nova meta de hidratação em litros (ex: 3.5)."
                    },
                    "justificativa": {
                        "type": "string",
                        "description": "Por que a meta foi aumentada."
                    }
                },
                "required": ["litros", "justificativa"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emitir_alerta_sistemico",
            "description": "Emite um alerta crítico (vermelho) que será forçado na tela do usuário antes dele preencher o log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mensagem": {
                        "type": "string",
                        "description": "A mensagem de alerta de risco."
                    }
                },
                "required": ["mensagem"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_padrao_fisiologico",
            "description": "Sugere uma HIPÓTESE sobre um padrão recorrente na biologia do Gabs. O sistema validará estatisticamente. NUNCA registre com base em evento único — use apenas quando observar recorrência.",
            "parameters": {
                "type": "object",
                "properties": {
                    "padrao": {
                        "type": "string",
                        "description": "Descrição clara do padrão (ex: 'HRV reduz em D+1 após futebol')."
                    },
                    "tipo": {
                        "type": "string",
                        "enum": ["recuperacao", "sono", "nutricao", "treino", "estresse"],
                        "description": "Categoria fisiológica do padrão."
                    },
                    "impacto_observado": {
                        "type": "number",
                        "description": "Magnitude do efeito observado (ex: -14 para queda de HRV de 14ms)."
                    },
                    "evidencia": {
                        "type": "string",
                        "description": "Dados que sustentam a hipótese (ex: 'HRV 73→59 após futebol em 14/05')."
                    }
                },
                "required": ["padrao", "tipo", "impacto_observado", "evidencia"]
            }
        }
    }
]

# =========================
# RISK SCORE ENGINE
# =========================
def calcular_risk_score(today_data):
    """Score composto de risco multi-fatorial. Retorna (score, breakdown)."""
    risk = 0
    breakdown = []
    
    # Extrai dados (suporta formato prefill e formato daily)
    perf = today_data.get("performance", {}) or today_data.get("longitudinal", {}).get("tsb", {})
    wearable = today_data.get("wearable", {}) or today_data.get("biometrics", {})
    sono = today_data.get("sono", {}) or today_data.get("sleep", {})
    estado = today_data.get("estado", {})
    
    acwr = perf.get("acwr", 0) or 0
    tsb = perf.get("tsb", 0) or 0
    hrv = wearable.get("hrv_ms", 0) or wearable.get("hrv", 0) or 0
    rhr = wearable.get("rhr", 0) or 0
    sono_hrs = sono.get("horas", 0) or sono.get("total_hours", 0) or 0
    stress = estado.get("estresse", 0) or wearable.get("stress", 0) or 0
    
    # ACWR (peso alto)
    if acwr > 1.5:
        risk += 4
        breakdown.append(f"ACWR {acwr} > 1.5 (+4)")
    elif acwr > 1.3:
        risk += 2
        breakdown.append(f"ACWR {acwr} > 1.3 (+2)")
    
    # TSB (peso alto)
    if tsb < -20:
        risk += 3
        breakdown.append(f"TSB {tsb} < -20 (+3)")
    elif tsb < -10:
        risk += 1
        breakdown.append(f"TSB {tsb} < -10 (+1)")
    
    # HRV (comparação com baseline ~65ms)
    if hrv > 0 and hrv < 50:
        risk += 2
        breakdown.append(f"HRV {hrv} < 50ms (+2)")
    elif hrv > 0 and hrv < 60:
        risk += 1
        breakdown.append(f"HRV {hrv} < 60ms (+1)")
    
    # RHR (comparação com baseline ~55bpm)
    if rhr > 62:
        risk += 2
        breakdown.append(f"RHR {rhr} > 62bpm (+2)")
    elif rhr > 58:
        risk += 1
        breakdown.append(f"RHR {rhr} > 58bpm (+1)")
    
    # Sono
    if sono_hrs > 0 and sono_hrs < 5.5:
        risk += 2
        breakdown.append(f"Sono {sono_hrs}h < 5.5h (+2)")
    elif sono_hrs > 0 and sono_hrs < 6.5:
        risk += 1
        breakdown.append(f"Sono {sono_hrs}h < 6.5h (+1)")
    
    # Stress
    if stress > 70:
        risk += 1
        breakdown.append(f"Stress {stress} > 70 (+1)")
    
    return risk, breakdown

# =========================
# ATHLETE BRAIN ENGINE V2.5
# =========================
def carregar_brain():
    """Carrega o Athlete Brain do disco."""
    if not os.path.exists(BRAIN_PATH):
        return {"athlete_name": "Gabs", "schema_version": "2.5", "learned_patterns": []}
    try:
        with open(BRAIN_PATH, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"athlete_name": "Gabs", "schema_version": "2.5", "learned_patterns": []}

def salvar_brain(data):
    """Persiste o Athlete Brain no disco."""
    with open(BRAIN_PATH, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def calcular_status(obs, contra, conf):
    """Lifecycle: hipótese → emergente → confirmado. Decay se contra-evidências > 40%."""
    if obs == 0:
        return "hipotese", conf
    taxa_contra = contra / obs if obs > 0 else 0
    if taxa_contra > 0.4:
        return "hipotese", max(0.1, conf * 0.7)  # Decay
    if obs >= 7 and conf >= 0.6:
        return "confirmado", conf
    if obs >= 3:
        return "emergente", conf
    return "hipotese", conf

def salvar_no_brain(args):
    """Upsert inteligente: incrementa observações se padrão existir, cria se novo."""
    data = carregar_brain()
    hoje = datetime.now().strftime("%Y-%m-%d")
    padrao_texto = args["padrao"]
    tipo = args.get("tipo", "recuperacao")
    impacto = args.get("impacto_observado", 0)
    evidencia_txt = args.get("evidencia", "")
    
    # Busca padrão existente (match por texto similar)
    existente = None
    for p in data["learned_patterns"]:
        if p["padrao"].lower() == padrao_texto.lower():
            existente = p
            break
    
    if existente:
        # UPSERT: incrementa observação
        existente["observacoes"] += 1
        existente["confirmacoes"] += 1
        existente["ultima_ocorrencia"] = hoje
        # Recalcula impacto médio
        n = existente["observacoes"]
        existente["impacto_medio"] = round(
            ((existente["impacto_medio"] * (n - 1)) + impacto) / n, 2
        )
        # Recalcula confiança
        existente["confianca"] = round(
            existente["confirmacoes"] / existente["observacoes"], 2
        )
        # Lifecycle
        existente["status"], existente["confianca"] = calcular_status(
            existente["observacoes"], existente["contra_evidencias"], existente["confianca"]
        )
        # Adiciona evidência datada
        existente["evidencias"].append({"data": hoje, "impacto": impacto, "nota": evidencia_txt})
        print(f"🧠 [Brain] Padrão atualizado: '{padrao_texto}' → {existente['status']} ({existente['observacoes']} obs, confiança {existente['confianca']})")
    else:
        # NOVO: cria como hipótese
        brain_id = f"brain_{len(data['learned_patterns']) + 1:03d}"
        novo = {
            "id": brain_id,
            "padrao": padrao_texto,
            "tipo": tipo,
            "status": "hipotese",
            "observacoes": 1,
            "confirmacoes": 1,
            "contra_evidencias": 0,
            "confianca": 0.3,
            "impacto_medio": impacto,
            "primeira_ocorrencia": hoje,
            "ultima_ocorrencia": hoje,
            "evidencias": [{"data": hoje, "impacto": impacto, "nota": evidencia_txt}]
        }
        data["learned_patterns"].append(novo)
        print(f"🧠 [Brain] Nova hipótese registrada: '{padrao_texto}' (confiança inicial: 0.3)")
    
    salvar_brain(data)

def buscar_padroes_relevantes(today_data):
    """Mini-retrieval: retorna padrões relevantes para o contexto do dia, com scoring híbrido."""
    data = carregar_brain()
    patterns = data.get("learned_patterns", [])
    if not patterns:
        return ""
    
    # Extrai contexto do dia atual
    treino_hoje = ""
    if isinstance(today_data, dict):
        treino_hoje = (today_data.get("treino", {}).get("planejado", "") or "").lower()
        hrv = today_data.get("wearable", {}).get("hrv_ms", 0) or 0
        sono_hrs = today_data.get("sono", {}).get("horas", 0) or 0
        stress = today_data.get("estado", {}).get("estresse", 0) or 0
    else:
        hrv, sono_hrs, stress = 0, 0, 0
    
    scored = []
    for p in patterns:
        score = 0.0
        
        # Treino match (0.4)
        if treino_hoje and treino_hoje in p["padrao"].lower():
            score += 0.4
        
        # Biometria match (0.4) — prioriza padrões de sono/HRV se marcadores estão fora
        if p["tipo"] == "sono" and sono_hrs < 6.5:
            score += 0.4
        elif p["tipo"] == "recuperacao" and hrv < 60:
            score += 0.4
        elif p["tipo"] == "estresse" and stress > 60:
            score += 0.4
        elif p["tipo"] == "nutricao":
            score += 0.15  # Sempre um pouco relevante
        
        # Categoria match (0.1)
        if p["tipo"] == "treino":
            score += 0.1
        
        # Recência (0.1) — padrões recentes valem mais
        recencia_factor = 1.0
        try:
            dias_desde = (datetime.now() - datetime.strptime(p["ultima_ocorrencia"], "%Y-%m-%d")).days
            if dias_desde <= 7:
                score += 0.1
                recencia_factor = 1.0
            elif dias_desde <= 30:
                score += 0.05
                recencia_factor = 0.9
            elif dias_desde <= 90:
                recencia_factor = 0.7
            else:
                recencia_factor = 0.5
        except:
            pass
        
        # Status boost — confirmados valem mais
        if p["status"] == "confirmado":
            score *= 1.3
        elif p["status"] == "emergente":
            score *= 1.1
        
        # Aplica fator de recência na confiança exibida
        confianca_real = round(p["confianca"] * recencia_factor, 2)
        
        if score > 0.1:  # Threshold mínimo
            scored.append((score, p, confianca_real))
    
    # Top 5 mais relevantes
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:5]
    
    if not top:
        return ""
    
    brain_text = "\n🧠 MEMÓRIA FISIOLÓGICA RELEVANTE (Athlete Brain):\n"
    for score, p, confianca_real in top:
        status_icon = {"hipotese": "❓", "emergente": "📊", "confirmado": "✅"}.get(p["status"], "❓")
        brain_text += (
            f"- {status_icon} [{p['status'].upper()}] {p['padrao']} "
            f"(confiança ajustada: {confianca_real}, obs: {p['observacoes']}, "
            f"impacto médio: {p['impacto_medio']})\n"
        )
    
    return brain_text

def get_coach_insight(mode="coach"):
    try:
        with open(PROMPT_PATH, "r", encoding='utf-8') as f:
            system_prompt = f.read()
    except Exception as e:
        return f"❌ Erro ao carregar o prompt: {e}", []
    
    # Define fonte de dados baseada no modo
    data_path = PREFILL_DATA_PATH
    if mode == "coach":
        date_str = datetime.now().strftime("%Y%m%d")
        final_path = os.path.join(FINAL_DATA_DIR, f"{date_str}.json")
        if os.path.exists(final_path):
            data_path = final_path
            print(f"📊 Analisando dados REVISADOS: {os.path.basename(final_path)}")

    if not os.path.exists(data_path):
        return f"❌ Erro: Dados ({mode}) não encontrados.", []
        
    try:
        with open(data_path, "r", encoding='utf-8') as f:
            today_data = json.load(f)
    except Exception as e:
        return f"❌ Erro ao ler dados: {e}", []
        
    print(f"🧠 Consultando o Protocolo Sentinel (Modo: {mode.upper()})...")
    
    # Risk Score Engine (Diagnóstico Multi-Fatorial)
    risk_score, risk_breakdown = calcular_risk_score(today_data)
    risk_label = "BAIXO" if risk_score < 4 else ("MODERADO" if risk_score < 6 else "CRÍTICO")
    print(f"🎯 Risk Score: {risk_score} ({risk_label})")
    if risk_breakdown:
        for r in risk_breakdown:
            print(f"   → {r}")
    
    # Injeta Risk Score nos dados para o Sentinel
    today_data["_risk_score"] = {
        "score": risk_score,
        "label": risk_label,
        "breakdown": risk_breakdown
    }

    # Injeta RNS como métrica PARALELA (não integrada ao Risk Score — Phase D)
    rns_data = today_data.get("nutrition_analysis", {}).get("rns") if isinstance(today_data.get("nutrition_analysis"), dict) else None
    if rns_data:
        today_data["_rns"] = rns_data
        print(f"🥗 RNS: {rns_data['score']}/100 ({rns_data['status']}) [paralelo ao Risk Score]")
    
    # Retrieval contextual do Athlete Brain
    brain_content = buscar_padroes_relevantes(today_data)
    
    # Injeta instrução específica de modo no topo do prompt
    rns_instruction = ""
    if rns_data:
        rns_instruction = (
            f"\nRNS (Recovery Nutrition Score): {rns_data['score']}/100 ({rns_data['status']}) "
            f"[v{rns_data['version']}] — "
            "Métrica PARALELA ao Risk Score. Reporta o status do abastecimento do hardware (combustível). "
            "Não influencia o Risk Score. Mencione-o separadamente no diagnóstico como dimensão nutricional."
        )

    mode_instructions = ""
    if mode == "guard":
        mode_instructions = (
            "VOCÊ ESTÁ NO MODO GUARDIÃO (PRÉ-REVISÃO).\n"
            "REGRAS CRÍTICAS:\n"
            f"1. O RISK SCORE atual é {risk_score} ({risk_label}). Se < 4, responda APENAS: 'SISTEMA ESTÁVEL'.\n"
            "2. Se risk_score >= 4, sugira remanejamento seguindo a estrutura: 'Sugestão de Remanejamento do Treino de amanhã: [Nome]'.\n"
            "3. Resolva conflitos de agenda cientificamente e proponha a nova sequência semanal.\n"
            f"4. Seja minimalista. Não faça análise clínica agora.{rns_instruction}"
        )
    else:
        mode_instructions = (
            "VOCÊ ESTÁ NO MODO MENTOR (PÓS-REVISÃO).\n"
            "REGRAS CRÍTICAS:\n"
            f"1. O RISK SCORE do dia é {risk_score} ({risk_label}). Use-o para contextualizar sua análise.\n"
            "2. Execute a análise clínica completa usando os 9 blocos obrigatórios.\n"
            f"3. Os dados já foram validados. Foque em aprendizado e projeção.{rns_instruction}"
        )


    messages = [
        {"role": "system", "content": f"{mode_instructions}\n{brain_content}\n\n{system_prompt}"},
        {"role": "user", "content": f"Aqui estão meus dados: {json.dumps(today_data, indent=2)}"}
    ]

    actions_taken = []

    try:
        pr = provider.chat(messages, tools=TOOLS)
        meta = pr.metadata
        print(f"📡 [{meta.provider}:{meta.model}] {meta.input_tokens}→{meta.output_tokens} tokens | {meta.latency_ms}ms")

        # O Coach decidiu usar alguma ferramenta?
        if pr.tool_calls:
            messages.append(pr.raw_message.to_dict())  # to_dict() — sem __dict__ bomb

            for tc in pr.tool_calls:
                print(f"⚙️ [Tool Calling] O Coach acionou: {tc.name}")
                actions_taken.append({
                    "action": tc.name,
                    "args": tc.arguments
                })

                # Feedback simulado para a IA continuar o texto
                messages.append(build_tool_result_message(
                    tc.id, tc.name,
                    {"status": "success", "message": "Ação registrada no sistema. Aguardando aprovação do usuário."}
                ))

                # Persistência imediata se for aprendizado de padrão
                if tc.name == "registrar_padrao_fisiologico":
                    salvar_no_brain(tc.arguments)

            # Segunda chamada para gerar o texto final após usar as tools
            final_pr = provider.chat(messages)
            meta2 = final_pr.metadata
            print(f"📡 [{meta2.provider}:{meta2.model}] {meta2.input_tokens}→{meta2.output_tokens} tokens | {meta2.latency_ms}ms")
            final_text = final_pr.content
        else:
            final_text = pr.content

        return final_text, actions_taken

    except Exception as e:
        if "api_key" in str(e).lower():
            return "❌ Erro: API Key inválida ou ausente no arquivo .env.", []
        return f"❌ Erro na API: {e}", []

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["guard", "coach"], default="coach")
    args = parser.parse_args()

    insight, actions = get_coach_insight(mode=args.mode)
    
    # Exibição discreta para Sistema Estável no modo Guard
    if args.mode == "guard" and insight.strip() == "SISTEMA ESTÁVEL":
        print(f"\n🛡️  Sentinel: {insight.strip()} (Nenhuma intervenção necessária)")
    else:
        print("\n" + "═"*50)
        print(f" 🔥 O VEREDITO DO SENTINEL ({args.mode.upper()}) 🔥")
        print("═"*50)
        print(insight)
        print("═"*50 + "\n")

    # 1. Salva como Markdown no Histórico (Apenas no modo Coach final)
    if args.mode == "coach":
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            history_path = os.path.join(ROOT_DIR, "data", "history", f"coach_{date_str}.md")
            with open(history_path, "w", encoding='utf-8') as f:
                f.write(f"# 📜 Veredito do Coach - {date_str}\n\n")
                f.write(insight)
            print(f"✅ Veredito salvo em: {history_path}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar histórico MD: {e}")

    # 2. Injeta no ai_state.json as ações do AI (Apenas no modo Guard)
    if args.mode == "guard":
        try:
            ai_state_path = os.path.join(ROOT_DIR, "data", "prefill", "ai_state.json")
            state_data = {
                "coach_insight": insight,
                "ai_actions": actions,
                "date_generated": datetime.now().strftime("%Y-%m-%d")
            }
            with open(ai_state_path, "w", encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            print(f"⚠️  {len(actions)} ações sistêmicas foram salvas em ai_state.json para a próxima revisão.")
        except Exception as e:
            print(f"⚠️ Erro ao salvar ai_state: {e}")
