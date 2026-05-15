"""
Ollama Provider — Sentinel OS (Phase 3 — Soberania Local)

Permite rodar o Sentinel completamente local, sem depender de APIs externas.

Modelos recomendados:
  qwen2.5:14b     — melhor custo/benefício para raciocínio + tool calling
  deepseek-r1:14b — raciocínio avançado
  llama3.1:8b     — leve, para testes

Configuração (.env):
  LLM_PROVIDER=ollama
  AI_MODEL=qwen2.5:14b
  OLLAMA_HOST=http://localhost:11434

Referência: https://ollama.ai
"""

from core.llm_provider import LLMProvider, ProviderResponse


class OllamaProvider(LLMProvider):
    """Stub — implementação Phase 3 (soberania local)."""

    def __init__(self):
        raise NotImplementedError(
            "OllamaProvider: Phase 3 não implementado.\n"
            "Para usar: instalar Ollama, baixar modelo e implementar via HTTP API.\n"
            "Exemplo: ollama pull qwen2.5:14b\n"
        )

    def chat(self, messages, tools=None, temperature=0.9, stream=False) -> ProviderResponse:
        raise NotImplementedError
