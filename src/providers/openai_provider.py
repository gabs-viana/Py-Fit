"""
OpenAI Provider — Sentinel OS

Encapsula TODO o SDK openai. Nenhum outro módulo importa openai diretamente.
Registra telemetria completa: tokens, latência, modelo.

Configuração (.env):
  LLM_PROVIDER=openai
  AI_MODEL=gpt-4o-mini
  OPENAI_API_KEY=sk-...
"""

import os
import json
import time

from openai import OpenAI
from core.llm_provider import (
    LLMProvider, ProviderResponse, ProviderMessage,
    ProviderMetadata, ToolCall
)


class OpenAIProvider(LLMProvider):
    """
    Provider para OpenAI API.
    Implementação real — única classe que conhece o SDK openai.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.provider_name = "openai"

    def chat(
        self,
        messages: list,
        tools: list = None,
        temperature: float = 0.9,
        stream: bool = False,
    ) -> ProviderResponse:
        """
        Chama a OpenAI API e retorna ProviderResponse normalizado.
        stream=False por enquanto — assinatura preparada para Phase D.
        """
        if stream:
            raise NotImplementedError("Streaming não implementado ainda (Phase D).")

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        t_start = time.time()
        response = self.client.chat.completions.create(**kwargs)
        latency_ms = int((time.time() - t_start) * 1000)

        msg = response.choices[0].message

        # Normaliza tool_calls do SDK → lista de ToolCall tipados
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                ))

        raw_message = ProviderMessage(
            role=msg.role,
            content=msg.content,
            tool_calls=tool_calls,
        )

        usage = response.usage
        metadata = ProviderMetadata(
            provider=self.provider_name,
            model=self.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_ms=latency_ms,
        )

        return ProviderResponse(
            content=msg.content,
            tool_calls=tool_calls,
            raw_message=raw_message,
            metadata=metadata,
        )
