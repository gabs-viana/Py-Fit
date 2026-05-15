"""
OpenRouter Provider — Sentinel OS (Phase 2)

Permite testar Qwen, DeepSeek, Llama via OpenRouter sem mudança de interface.

Configuração (.env):
  LLM_PROVIDER=openrouter
  AI_MODEL=qwen/qwen-2.5-72b-instruct
  OPENROUTER_API_KEY=sk-or-...

Referência: https://openrouter.ai/docs
"""

from core.llm_provider import LLMProvider, ProviderResponse


class OpenRouterProvider(LLMProvider):
    """Stub — implementação Phase 2."""

    def __init__(self):
        raise NotImplementedError(
            "OpenRouterProvider: Phase 2 não implementado.\n"
            "Para usar: configurar OPENROUTER_API_KEY e implementar usando openai SDK apontando para https://openrouter.ai/api/v1\n"
        )

    def chat(self, messages, tools=None, temperature=0.9, stream=False) -> ProviderResponse:
        raise NotImplementedError
