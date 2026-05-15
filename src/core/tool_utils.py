"""
Tool Utilities — Sentinel OS

Funções de montagem de mensagens de tool result.
Separado do provider porque é lógica de CONVERSA, não de infraestrutura de IA.

Quando migrar para outros providers, apenas este arquivo verifica compatibilidade.
"""

import json


def build_tool_result_message(
    tool_call_id: str,
    name: str,
    result: dict | str,
) -> dict:
    """
    Monta a mensagem de resultado de tool no formato OpenAI-compatible.

    Args:
        tool_call_id: ID do tool_call retornado pelo provider
        name: Nome da função executada
        result: Resultado da função (dict ou str JSON)

    Returns:
        dict compatível com o contexto de mensagens do provider
    """
    if isinstance(result, dict):
        result_str = json.dumps(result, ensure_ascii=False)
    else:
        result_str = str(result)

    return {
        "tool_call_id": tool_call_id,
        "role": "tool",
        "name": name,
        "content": result_str,
    }
