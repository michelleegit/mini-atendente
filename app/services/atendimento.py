RESPOSTA_PROVISORIA = (
    "Recebemos sua mensagem! Em breve o atendente virtual vai responder "
    "com base nas perguntas frequentes da loja."
)


def gerar_resposta(conn, texto: str) -> tuple[str, str]:
    """Decide a resposta do bot para a mensagem do cliente.

    Devolve (texto_da_resposta, novo_status_da_conversa).

    Versão do dia 3: resposta fixa. No dia 4, esta função passa a buscar
    na FAQ e a transferir para humano quando não encontrar resposta boa.
    """
    return RESPOSTA_PROVISORIA, "aberta"
