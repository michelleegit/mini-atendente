import pytest

from app.services.atendimento import buscar_na_faq, gerar_resposta


# Mensagens escritas do jeito que um cliente escreveria, e a pergunta da FAQ
# que a busca deve encontrar para cada uma
@pytest.mark.parametrize(
    "mensagem, pergunta_esperada",
    [
        ("Qual é o prazo de entrega?", "Qual é o prazo de entrega?"),
        ("da pra parcelar no cartao?", "Posso parcelar a compra?"),
        ("esqueci a senha", "Esqueci minha senha, como recupero?"),
        ("onde esta meu pedido", "Como acompanho meu pedido?"),
        ("o frete é gratis?", "Quanto custa o frete?"),
        ("quero trocar o produto", "Como faço para trocar um produto?"),
        ("tem nota fiscal?", "A loja emite nota fiscal?"),
    ],
)
def test_busca_encontra_a_pergunta_certa(conn, mensagem, pergunta_esperada):
    resultado = buscar_na_faq(conn, mensagem)

    assert resultado is not None
    assert resultado["pergunta"] == pergunta_esperada


@pytest.mark.parametrize(
    "mensagem",
    [
        "Vocês vendem geladeira?",
        "qual a capital da frança",
        "oi",
    ],
)
def test_mensagem_fora_da_base_transfere(conn, mensagem):
    _, status = gerar_resposta(conn, mensagem, "aberta")
    assert status == "transferida"


def test_busca_ignora_acentos(conn):
    com_acento = buscar_na_faq(conn, "posso parcelar no cartão?")
    sem_acento = buscar_na_faq(conn, "posso parcelar no cartao?")

    assert com_acento["id"] == sem_acento["id"]
