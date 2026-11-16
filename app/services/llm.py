"""Geração de resposta com modelo de linguagem (RAG).

Usa o formato de chat compatível com a API da OpenAI, que é aceito por vários
provedores (Groq, Gemini, OpenAI e outros). O provedor é escolhido pelas
variáveis de ambiente LLM_BASE_URL, LLM_MODEL e LLM_API_KEY.
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

# Resposta que o modelo deve dar quando os trechos não respondem a pergunta
SINAL_TRANSFERIR = "TRANSFERIR"

INSTRUCOES = f"""Você é o atendente virtual da Loja Pixel, uma loja online de eletrônicos.
Responda à pergunta do cliente usando SOMENTE as informações dos trechos da FAQ abaixo.
Responda em português, de forma curta e cordial, em no máximo 3 frases.
Não invente prazos, valores, políticas ou informações que não estejam nos trechos.
Se os trechos não forem suficientes para responder, responda apenas: {SINAL_TRANSFERIR}"""

TEMPO_LIMITE_SEGUNDOS = 10


def montar_contexto(trechos: list[dict]) -> str:
    """Junta os trechos da FAQ num texto só, para mandar ao modelo."""
    return "\n\n".join(
        f"Pergunta: {t['pergunta']}\nResposta: {t['resposta']}" for t in trechos
    )


def gerar_resposta_llm(pergunta_cliente: str, trechos: list[dict]) -> str | None:
    """Pede ao modelo uma resposta baseada nos trechos da FAQ.

    Devolve None quando não há chave configurada ou quando a chamada falha.
    Nesses casos, quem chamou deve usar a busca simples como alternativa.
    """
    chave = os.getenv("LLM_API_KEY")
    if not chave:
        return None

    url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    modelo = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    corpo = {
        "model": modelo,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": INSTRUCOES},
            {
                "role": "user",
                "content": (
                    f"Trechos da FAQ:\n{montar_contexto(trechos)}\n\n"
                    f"Pergunta do cliente: {pergunta_cliente}"
                ),
            },
        ],
    }

    try:
        resposta = httpx.post(
            f"{url}/chat/completions",
            json=corpo,
            headers={"Authorization": f"Bearer {chave}"},
            timeout=TEMPO_LIMITE_SEGUNDOS,
        )
        resposta.raise_for_status()
        texto = resposta.json()["choices"][0]["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as erro:
        logger.warning("Falha ao gerar resposta com o modelo: %s", erro)
        return None

    return texto or None
