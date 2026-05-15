"""
LLM Provider Layer — Sentinel OS

Desacopla o Sentinel de qualquer SDK ou modelo específico.
Trocar de modelo: LLM_PROVIDER=openai → LLM_PROVIDER=ollama no .env

Arquitetura:
  ai_coach.py → get_provider() → [OpenAIProvider | OpenRouterProvider | OllamaProvider]
                               → ProviderResponse (normalizado, sem SDK leakage)
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolCall:
    """Chamada de ferramenta normalizada — sem SDK leakage."""
    id: str
    name: str
    arguments: dict


@dataclass
class ProviderMessage:
    """
    Mensagem normalizada — nunca expõe objeto de SDK.
    Use to_dict() para serializar. Evita bomba silenciosa do __dict__.
    """
    role: str
    content: Optional[str]
    tool_calls: list = field(default_factory=list)  # list[ToolCall]

    def to_dict(self) -> dict:
        """
        Serialização controlada — só campos necessários ao contexto.
        Campos futuros em ProviderMessage NÃO vazam para o provider.
        """
        d = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": str(tc.arguments)
                    }
                }
                for tc in self.tool_calls
            ]
        return d


@dataclass
class ProviderMetadata:
    """Telemetria de uma chamada ao LLM. Tipado — nunca dict genérico."""
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


@dataclass
class ProviderResponse:
    """Resposta normalizada de qualquer provider."""
    content: Optional[str]
    tool_calls: list          # list[ToolCall]
    raw_message: ProviderMessage
    metadata: ProviderMetadata


class LLMProvider(ABC):
    """Interface abstrata para qualquer LLM provider."""

    @abstractmethod
    def chat(
        self,
        messages: list,
        tools: list = None,
        temperature: float = 0.9,
        stream: bool = False,   # Assinatura futura — não implementada (Phase D)
    ) -> ProviderResponse:
        """Envia mensagens e retorna ProviderResponse normalizado."""
        pass


def get_provider(name: str = None) -> LLMProvider:
    """
    Factory: instancia o provider correto via LLM_PROVIDER do .env.

    Valores suportados:
      openai       → OpenAIProvider (padrão)
      openrouter   → OpenRouterProvider (Phase 2 — teste de modelos)
      ollama       → OllamaProvider (Phase 3 — soberania local)

    Fallback: definir FALLBACK_PROVIDER no .env (Phase 4).
    """
    provider_name = name or os.getenv("LLM_PROVIDER", "openai")

    if provider_name == "openai":
        from providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif provider_name == "openrouter":
        from providers.openrouter_provider import OpenRouterProvider
        return OpenRouterProvider()
    elif provider_name == "ollama":
        from providers.ollama_provider import OllamaProvider
        return OllamaProvider()
    else:
        raise ValueError(
            f"Provider '{provider_name}' não suportado. "
            "Valores válidos: openai | openrouter | ollama"
        )
