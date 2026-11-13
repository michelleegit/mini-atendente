CONVERSA_INEXISTENTE = 999999


# POST /conversas


def test_abrir_conversa(client):
    resposta = client.post("/conversas", json={"cliente": "ana"})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["cliente"] == "ana"
    assert corpo["status"] == "aberta"
    assert isinstance(corpo["id"], int)


def test_abrir_conversa_com_cliente_vazio(client):
    resposta = client.post("/conversas", json={"cliente": ""})
    assert resposta.status_code == 422


def test_abrir_conversa_com_cliente_so_de_espacos(client):
    resposta = client.post("/conversas", json={"cliente": "   "})
    assert resposta.status_code == 422


def test_abrir_conversa_sem_cliente(client):
    resposta = client.post("/conversas", json={})
    assert resposta.status_code == 422


# POST /conversas/{id}/mensagens


def test_enviar_pergunta_da_faq(client, conversa):
    resposta = client.post(
        f"/conversas/{conversa['id']}/mensagens",
        json={"texto": "Qual é o prazo de entrega?"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["mensagem_cliente"]["autor"] == "cliente"
    assert corpo["mensagem_cliente"]["texto"] == "Qual é o prazo de entrega?"
    assert corpo["resposta_bot"]["autor"] == "bot"
    assert "dias úteis" in corpo["resposta_bot"]["texto"]
    assert corpo["status_conversa"] == "aberta"


def test_enviar_mensagem_vazia(client, conversa):
    resposta = client.post(
        f"/conversas/{conversa['id']}/mensagens", json={"texto": ""}
    )
    assert resposta.status_code == 422


def test_enviar_mensagem_so_de_espacos(client, conversa):
    resposta = client.post(
        f"/conversas/{conversa['id']}/mensagens", json={"texto": "    "}
    )
    assert resposta.status_code == 422


def test_enviar_mensagem_para_conversa_inexistente(client):
    resposta = client.post(
        f"/conversas/{CONVERSA_INEXISTENTE}/mensagens",
        json={"texto": "Qual é o prazo de entrega?"},
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Conversa não encontrada"


def test_pergunta_fora_da_base_transfere_para_humano(client, conversa):
    resposta = client.post(
        f"/conversas/{conversa['id']}/mensagens",
        json={"texto": "Vocês vendem geladeira?"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status_conversa"] == "transferida"
    assert "atendente humano" in corpo["resposta_bot"]["texto"]


def test_conversa_transferida_nao_volta_para_a_faq(client, conversa):
    url = f"/conversas/{conversa['id']}/mensagens"
    client.post(url, json={"texto": "Vocês vendem geladeira?"})

    # Mesmo uma pergunta que existe na FAQ não é mais respondida pelo bot
    resposta = client.post(url, json={"texto": "Qual é o prazo de entrega?"})

    corpo = resposta.json()
    assert corpo["status_conversa"] == "transferida"
    assert "já está com um atendente humano" in corpo["resposta_bot"]["texto"]


# GET /conversas/{id}


def test_ler_conversa_com_mensagens_em_ordem(client, conversa):
    url = f"/conversas/{conversa['id']}/mensagens"
    client.post(url, json={"texto": "Qual é o prazo de entrega?"})
    client.post(url, json={"texto": "Esqueci minha senha"})

    resposta = client.get(f"/conversas/{conversa['id']}")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["id"] == conversa["id"]
    assert [m["autor"] for m in corpo["mensagens"]] == ["cliente", "bot", "cliente", "bot"]
    assert corpo["mensagens"][0]["texto"] == "Qual é o prazo de entrega?"
    assert corpo["mensagens"][2]["texto"] == "Esqueci minha senha"


def test_ler_conversa_nova_sem_mensagens(client, conversa):
    resposta = client.get(f"/conversas/{conversa['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["mensagens"] == []


def test_ler_conversa_mostra_status_transferida(client, conversa):
    client.post(
        f"/conversas/{conversa['id']}/mensagens",
        json={"texto": "Vocês vendem geladeira?"},
    )

    resposta = client.get(f"/conversas/{conversa['id']}")
    assert resposta.json()["status"] == "transferida"


def test_ler_conversa_inexistente(client):
    resposta = client.get(f"/conversas/{CONVERSA_INEXISTENTE}")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Conversa não encontrada"


def test_ler_conversa_com_id_que_nao_e_numero(client):
    resposta = client.get("/conversas/abc")
    assert resposta.status_code == 422
