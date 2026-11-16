from app.services.llm import SINAL_TRANSFERIR, gerar_resposta_llm

# Pontuação mínima (ts_rank) para considerar que a FAQ tem uma resposta boa.
# Abaixo disso, a conversa é transferida para um atendente humano.
LIMIAR_RELEVANCIA = 0.1

# Quantos trechos da FAQ são enviados ao modelo de linguagem como contexto
TRECHOS_PARA_O_MODELO = 3

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
# - ts_rank dá uma nota para cada pergunta da FAQ; ficam as de nota mais alta.
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
    LIMIT %(limite)s
"""


def buscar_trechos(conn, texto: str, limite: int) -> list[dict]:
    """Devolve as perguntas da FAQ mais parecidas com o texto, da melhor para a pior."""
    return conn.execute(SQL_BUSCA_FAQ, {"texto": texto, "limite": limite}).fetchall()


def buscar_na_faq(conn, texto: str) -> dict | None:
    """Devolve a pergunta da FAQ mais parecida com o texto, ou None."""
    trechos = buscar_trechos(conn, texto, limite=1)
    return trechos[0] if trechos else None


def gerar_resposta(conn, texto: str, status_atual: str) -> tuple[str, str]:
    """Decide a resposta do bot para a mensagem do cliente.

    Devolve (texto_da_resposta, novo_status_da_conversa).

    1. Busca na FAQ os trechos relevantes (a parte "R" de RAG).
    2. Se nenhum trecho for relevante, transfere para humano.
    3. Se houver modelo de linguagem configurado, ele escreve a resposta
       usando os trechos como contexto (a parte "G" de RAG).
    4. Se o modelo não estiver configurado ou falhar, usa a resposta do
       trecho mais relevante, como na busca simples.
    """
    if status_atual == "transferida":
        return RESPOSTA_JA_TRANSFERIDA, "transferida"

    trechos = [
        t
        for t in buscar_trechos(conn, texto, limite=TRECHOS_PARA_O_MODELO)
        if t["relevancia"] >= LIMIAR_RELEVANCIA
    ]

    if not trechos:
        return RESPOSTA_TRANSFERENCIA, "transferida"

    resposta_modelo = gerar_resposta_llm(texto, trechos)

    if resposta_modelo is None:
        return trechos[0]["resposta"], "aberta"

    if resposta_modelo.strip().upper().startswith(SINAL_TRANSFERIR):
        return RESPOSTA_TRANSFERENCIA, "transferida"

    return resposta_modelo, "aberta"
