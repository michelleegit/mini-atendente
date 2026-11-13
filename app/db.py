import os

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    """Abre uma conexão por requisição e garante que ela seja fechada no final.

    Se a requisição terminar sem erro, as alterações são confirmadas (commit).
    Se der erro, são desfeitas (rollback).
    """
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn
