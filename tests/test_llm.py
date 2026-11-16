import httpx

from app.services import atendimento, llm

TRECHO = {
    "id": 1,
    "pergunta": "Qual é o prazo de entrega?",
    "resposta": "O prazo de entrega é de 3 a 7 dias úteis.",
    "relevancia": 0.6,
}


class RespostaFalsa:
    """Imita a resposta HTTP do provedor de modelo de linguagem."""

    def __init__(self, texto):
        self.texto = texto

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self.texto}}]}


# Integração com o provedor (app/services/llm.py)


def test_sem_chave_nao_chama_o_modelo(monkeypatch):
    def nao_deveria_ser_chamado(*args, **kwargs):
        raise AssertionError("o modelo não deveria ser chamado sem chave")

    monkeypatch.setattr(llm.httpx, "post", nao_deveria_ser_chamado)

    assert llm.gerar_resposta_llm("Qual o prazo?", [TRECHO]) is None


def test_envia_os_trechos_e_devolve_o_texto_do_modelo(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "chave-de-teste")
    chamadas = []

    def post_falso(url, json, headers, timeout):
        chamadas.append({"url": url, "json": json, "headers": headers})
        return RespostaFalsa("  Chega em 3 a 7 dias úteis!  ")

    monkeypatch.setattr(llm.httpx, "post", post_falso)

    resposta = llm.gerar_resposta_llm("Qual o prazo?", [TRECHO])

    assert resposta == "Chega em 3 a 7 dias úteis!"
    assert chamadas[0]["url"].endswith("/chat/completions")
    assert chamadas[0]["headers"]["Authorization"] == "Bearer chave-de-teste"
    mensagem_usuario = chamadas[0]["json"]["messages"][1]["content"]
    assert TRECHO["resposta"] in mensagem_usuario
    assert "Qual o prazo?" in mensagem_usuario


def test_falha_de_rede_devolve_none(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "chave-de-teste")

    def post_que_falha(*args, **kwargs):
        raise httpx.ConnectError("sem internet")

    monkeypatch.setattr(llm.httpx, "post", post_que_falha)

    assert llm.gerar_resposta_llm("Qual o prazo?", [TRECHO]) is None


# Decisão do atendimento (app/services/atendimento.py)


def test_usa_a_resposta_do_modelo(conn, monkeypatch):
    monkeypatch.setattr(
        atendimento, "gerar_resposta_llm", lambda texto, trechos: "Resposta do modelo"
    )

    texto, status = atendimento.gerar_resposta(conn, "Qual o prazo de entrega?", "aberta")

    assert texto == "Resposta do modelo"
    assert status == "aberta"


def test_modelo_pede_transferencia(conn, monkeypatch):
    monkeypatch.setattr(
        atendimento, "gerar_resposta_llm", lambda texto, trechos: "TRANSFERIR"
    )

    texto, status = atendimento.gerar_resposta(conn, "Qual o prazo de entrega?", "aberta")

    assert texto == atendimento.RESPOSTA_TRANSFERENCIA
    assert status == "transferida"


def test_modelo_indisponivel_usa_a_busca_simples(conn, monkeypatch):
    monkeypatch.setattr(atendimento, "gerar_resposta_llm", lambda texto, trechos: None)

    texto, status = atendimento.gerar_resposta(conn, "Qual o prazo de entrega?", "aberta")

    assert "3 a 7 dias úteis" in texto
    assert status == "aberta"


def test_sem_trecho_relevante_nem_chama_o_modelo(conn, monkeypatch):
    def nao_deveria_ser_chamado(texto, trechos):
        raise AssertionError("o modelo não deveria ser chamado")

    monkeypatch.setattr(atendimento, "gerar_resposta_llm", nao_deveria_ser_chamado)

    _, status = atendimento.gerar_resposta(conn, "Vocês vendem geladeira?", "aberta")

    assert status == "transferida"


def test_modelo_recebe_varios_trechos(conn, monkeypatch):
    recebidos = []

    def modelo_falso(texto, trechos):
        recebidos.extend(trechos)
        return "ok"

    monkeypatch.setattr(atendimento, "gerar_resposta_llm", modelo_falso)

    atendimento.gerar_resposta(conn, "posso pagar com boleto ou pix?", "aberta")

    assert 1 < len(recebidos) <= atendimento.TRECHOS_PARA_O_MODELO
