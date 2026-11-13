# Pontuação mínima (ts_rank) para considerar que a FAQ tem uma resposta boa.
# Abaixo disso, a conversa é transferida para um atendente humano.
LIMIAR_RELEVANCIA = 0.1

RESPOSTA_TRANSFERENCIA = (
    "Não encontrei uma resposta para a sua pergunta. "
    "Vou transferir você para um atendente humano, que vai responder em breve."
)

RESPOSTA_JA_TRANSFERIDA = (
    "Sua conversa já está com um atendente humano. "
    "Aguarde, que ele vai responder em breve."
)

# Busca de texto do PostgreSQL:
# - plainto_tsquery transforma o texto do cliente em termos de busca
#   (tira palavras como "o", "de", "qual" e reduz "entregas" para "entreg");
# - o replace troca E (&) por OU (|), para não exigir que todas as palavras
#   do cliente apareçam na mesma pergunta da FAQ;
# - ts_rank dá uma nota para cada pergunta da FAQ; fica a de nota mais alta.
SQL_BUSCA_FAQ = """
    WITH consulta AS (
        SELECT replace(
            plainto_tsquery('pt_sem_acento', %(texto)s)::text, '&', '|'
        )::tsquery AS termos
    )
    SELECT f.id, f.pergunta, f.resposta, ts_rank(f.busca, c.termos) AS relevancia
    FROM faq f, consulta c
    WHERE f.busca @@ c.termos
    ORDER BY relevancia DESC, f.id
    LIMIT 1
"""


def buscar_na_faq(conn, texto: str) -> dict | None:
    """Devolve a pergunta da FAQ mais parecida com o texto, ou None."""
    return conn.execute(SQL_BUSCA_FAQ, {"texto": texto}).fetchone()


def gerar_resposta(conn, texto: str, status_atual: str) -> tuple[str, str]:
    """Decide a resposta do bot para a mensagem do cliente.

    Devolve (texto_da_resposta, novo_status_da_conversa).
    """
    if status_atual == "transferida":
        return RESPOSTA_JA_TRANSFERIDA, "transferida"

    melhor = buscar_na_faq(conn, texto)

    if melhor is None or melhor["relevancia"] < LIMIAR_RELEVANCIA:
        return RESPOSTA_TRANSFERENCIA, "transferida"

    return melhor["resposta"], "aberta"
