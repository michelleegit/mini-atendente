# Mini Atendente

API de atendimento virtual para uma loja fictícia. O cliente envia uma mensagem, a API procura a resposta numa base de perguntas frequentes e, quando não encontra uma resposta boa, marca a conversa como transferida para atendimento humano.

> Em construção.

## Stack

Python, FastAPI, PostgreSQL, pytest e Docker Compose.

## Como rodar

```bash
cp .env.example .env
docker compose up --build
```

A API sobe em http://localhost:8000 e a documentação em http://localhost:8000/docs.

## Testes

```bash
docker compose exec api pytest
```
