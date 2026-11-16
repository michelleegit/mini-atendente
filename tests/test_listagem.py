def abrir(client, cliente):
    return client.post("/conversas", json={"cliente": cliente}).json()


def enviar(client, conversa_id, texto):
    client.post(f"/conversas/{conversa_id}/mensagens", json={"texto": texto})


def test_listar_por_cliente(client):
    abrir(client, "listagem-ana")
    abrir(client, "listagem-ana")
    abrir(client, "listagem-bruno")

    resposta = client.get("/conversas", params={"cliente": "listagem-ana"})

    assert resposta.status_code == 200
    conversas = resposta.json()
    assert len(conversas) == 2
    assert all(c["cliente"] == "listagem-ana" for c in conversas)


def test_listar_cliente_sem_conversas(client):
    resposta = client.get("/conversas", params={"cliente": "cliente-que-nao-existe"})

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_listar_mais_recentes_primeiro(client):
    primeira = abrir(client, "listagem-ordem")
    segunda = abrir(client, "listagem-ordem")

    conversas = client.get("/conversas", params={"cliente": "listagem-ordem"}).json()

    assert [c["id"] for c in conversas] == [segunda["id"], primeira["id"]]


def test_listar_conta_mensagens(client):
    com_mensagens = abrir(client, "listagem-contagem")
    sem_mensagens = abrir(client, "listagem-contagem")
    enviar(client, com_mensagens["id"], "Qual é o prazo de entrega?")
    enviar(client, com_mensagens["id"], "Esqueci minha senha")

    conversas = client.get("/conversas", params={"cliente": "listagem-contagem"}).json()
    por_id = {c["id"]: c for c in conversas}

    # Cada pergunta gera 2 mensagens: a do cliente e a do bot
    assert por_id[com_mensagens["id"]]["total_mensagens"] == 4
    assert por_id[com_mensagens["id"]]["ultima_mensagem_em"] is not None
    assert por_id[sem_mensagens["id"]]["total_mensagens"] == 0
    assert por_id[sem_mensagens["id"]]["ultima_mensagem_em"] is None


def test_listar_por_status(client):
    resolvida = abrir(client, "listagem-status")
    transferida = abrir(client, "listagem-status")
    enviar(client, resolvida["id"], "Qual é o prazo de entrega?")
    enviar(client, transferida["id"], "Vocês vendem geladeira?")

    resposta = client.get(
        "/conversas", params={"cliente": "listagem-status", "status": "transferida"}
    )

    assert resposta.status_code == 200
    assert [c["id"] for c in resposta.json()] == [transferida["id"]]


def test_listar_respeita_limite(client):
    for _ in range(3):
        abrir(client, "listagem-limite")

    resposta = client.get("/conversas", params={"cliente": "listagem-limite", "limite": 2})

    assert len(resposta.json()) == 2


def test_listar_com_status_invalido(client):
    resposta = client.get("/conversas", params={"status": "fechada"})
    assert resposta.status_code == 422


def test_listar_com_limite_fora_do_intervalo(client):
    assert client.get("/conversas", params={"limite": 0}).status_code == 422
    assert client.get("/conversas", params={"limite": 101}).status_code == 422
