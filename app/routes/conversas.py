from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_conn
from app.schemas import (
    ConversaCriar,
    ConversaDetalhe,
    ConversaResumo,
    ConversaSaida,
    MensagemCriar,
    RespostaMensagem,
)
from app.services.atendimento import gerar_resposta

router = APIRouter(prefix="/conversas", tags=["conversas"])


def buscar_conversa(conn, conversa_id: int) -> dict:
    """Busca a conversa pelo id ou responde 404 se ela não existir."""
    conversa = conn.execute(
        "SELECT id, cliente, status, criada_em FROM conversas WHERE id = %s",
        (conversa_id,),
    ).fetchone()
    if conversa is None:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return conversa


@router.post("", response_model=ConversaSaida, status_code=status.HTTP_201_CREATED)
def abrir_conversa(dados: ConversaCriar, conn=Depends(get_conn)):
    """Abre uma nova conversa para o cliente."""
    return conn.execute(
        """
        INSERT INTO conversas (cliente)
        VALUES (%s)
        RETURNING id, cliente, status, criada_em
        """,
        (dados.cliente,),
    ).fetchone()


@router.post(
    "/{conversa_id}/mensagens",
    response_model=RespostaMensagem,
    status_code=status.HTTP_201_CREATED,
)
def enviar_mensagem(conversa_id: int, dados: MensagemCriar, conn=Depends(get_conn)):
    """Registra a mensagem do cliente e devolve a resposta do bot."""
    conversa = buscar_conversa(conn, conversa_id)

    sql_mensagem = """
        INSERT INTO mensagens (conversa_id, autor, texto)
        VALUES (%s, %s, %s)
        RETURNING id, conversa_id, autor, texto, criada_em
    """

    mensagem_cliente = conn.execute(
        sql_mensagem, (conversa_id, "cliente", dados.texto)
    ).fetchone()

    texto_bot, novo_status = gerar_resposta(conn, dados.texto, conversa["status"])

    resposta_bot = conn.execute(
        sql_mensagem, (conversa_id, "bot", texto_bot)
    ).fetchone()

    conn.execute(
        "UPDATE conversas SET status = %s WHERE id = %s",
        (novo_status, conversa_id),
    )

    return {
        "mensagem_cliente": mensagem_cliente,
        "resposta_bot": resposta_bot,
        "status_conversa": novo_status,
    }


@router.get("/{conversa_id}", response_model=ConversaDetalhe)
def ler_conversa(conversa_id: int, conn=Depends(get_conn)):
    """Devolve a conversa com todas as mensagens, em ordem de envio."""
    conversa = buscar_conversa(conn, conversa_id)
    mensagens = conn.execute(
        """
        SELECT id, conversa_id, autor, texto, criada_em
        FROM mensagens
        WHERE conversa_id = %s
        ORDER BY criada_em, id
        """,
        (conversa_id,),
    ).fetchall()
    return {**conversa, "mensagens": mensagens}


@router.get("", response_model=list[ConversaResumo])
def listar_conversas(
    cliente: str | None = Query(default=None, min_length=1, max_length=100),
    status_conversa: Literal["aberta", "transferida"] | None = Query(
        default=None, alias="status"
    ),
    limite: int = Query(default=20, ge=1, le=100),
    conn=Depends(get_conn),
):
    """Lista conversas, das mais recentes para as mais antigas.

    Filtros opcionais: cliente e status. Cada conversa vem com o total de
    mensagens e a data da última mensagem.
    """
    return conn.execute(
        """
        SELECT
            c.id,
            c.cliente,
            c.status,
            c.criada_em,
            COUNT(m.id)      AS total_mensagens,
            MAX(m.criada_em) AS ultima_mensagem_em
        FROM conversas c
        LEFT JOIN mensagens m ON m.conversa_id = c.id
        WHERE (%(cliente)s::text IS NULL OR c.cliente = %(cliente)s)
          AND (%(status)s::text  IS NULL OR c.status  = %(status)s)
        GROUP BY c.id
        ORDER BY c.criada_em DESC, c.id DESC
        LIMIT %(limite)s
        """,
        {"cliente": cliente, "status": status_conversa, "limite": limite},
    ).fetchall()
