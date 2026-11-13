import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.db import DATABASE_URL, get_conn
from app.main import app


@pytest.fixture
def conn():
    """Conexão usada por um teste inteiro.

    Tudo o que o teste grava fica dentro de uma transação que é desfeita
    (rollback) no final. Assim, os testes não sujam o banco e um não
    interfere no outro.
    """
    conexao = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    yield conexao
    conexao.rollback()
    conexao.close()


@pytest.fixture
def client(conn):
    """Cliente HTTP da API que usa a conexão de teste no lugar da normal."""

    def get_conn_de_teste():
        yield conn

    app.dependency_overrides[get_conn] = get_conn_de_teste
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


@pytest.fixture
def conversa(client):
    """Uma conversa recém-aberta, pronta para receber mensagens."""
    resposta = client.post("/conversas", json={"cliente": "cliente-teste"})
    return resposta.json()
