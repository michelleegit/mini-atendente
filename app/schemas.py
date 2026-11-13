from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Entrada


class ConversaCriar(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cliente: str = Field(min_length=1, max_length=100, examples=["ana"])


class MensagemCriar(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    texto: str = Field(min_length=1, max_length=1000, examples=["Qual é o prazo de entrega?"])


# Saída


class MensagemSaida(BaseModel):
    id: int
    conversa_id: int
    autor: Literal["cliente", "bot"]
    texto: str
    criada_em: datetime


class ConversaSaida(BaseModel):
    id: int
    cliente: str
    status: Literal["aberta", "transferida"]
    criada_em: datetime


class ConversaDetalhe(ConversaSaida):
    mensagens: list[MensagemSaida]


class RespostaMensagem(BaseModel):
    mensagem_cliente: MensagemSaida
    resposta_bot: MensagemSaida
    status_conversa: Literal["aberta", "transferida"]
