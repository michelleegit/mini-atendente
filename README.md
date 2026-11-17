# Mini Atendente

API de atendimento virtual para uma loja fictícia de eletrônicos, a **Loja Pixel**. O cliente envia uma mensagem, a API procura a resposta numa base de perguntas frequentes (FAQ) e responde. Quando não encontra uma resposta boa, a conversa é marcada como **transferida para atendimento humano**.

Opcionalmente, um modelo de linguagem escreve a resposta usando os trechos mais relevantes da FAQ como contexto (RAG). Se o modelo não estiver configurado ou falhar, a API continua respondendo com a busca simples.

## Funcionalidades

- Abrir conversas, enviar mensagens e consultar o histórico
- Busca na FAQ com a busca de texto do PostgreSQL, ignorando acentos e variações das palavras ("cartao" encontra "cartão", "entregas" encontra "entrega")
- Transferência para atendimento humano quando nenhuma pergunta da FAQ é relevante
- Resposta gerada por modelo de linguagem com base na FAQ (opcional), com fallback para a busca simples
- Listagem de conversas com filtros por cliente, status e limite
- 43 testes automatizados

## Stack

- **Python 3.12** e **FastAPI**
- **PostgreSQL 16**, com SQL puro (sem ORM) via **psycopg 3**
- **pytest**
- **Docker** e **Docker Compose**
- Modelo de linguagem via API compatível com a da OpenAI (padrão: Groq)

## Como funciona

```
Mensagem do cliente
        │
        ▼
Conversa já transferida? ── sim ──► "Sua conversa já está com um atendente humano"
        │ não
        ▼
Busca na FAQ (PostgreSQL full-text search)
        │
        ├── nenhum trecho relevante ──► transfere para humano
        │
        ▼
Modelo de linguagem configurado?
        │
        ├── não, ou falhou ──► responde com o trecho mais relevante da FAQ
        │
        ▼
Modelo escreve a resposta usando só os trechos da FAQ
        │
        ├── responde "TRANSFERIR" ──► transfere para humano
        │
        ▼
Resposta enviada ao cliente
```

## Como rodar

Pré-requisito: Docker com Docker Compose.

```bash
git clone https://github.com/michelleegit/mini-atendente.git
cd mini-atendente
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Documentação interativa (Swagger): http://localhost:8000/docs
- O banco fica exposto na porta **5433** do computador, para não conflitar com um PostgreSQL local na 5432

Na primeira subida, o banco é criado automaticamente com as tabelas e as 18 perguntas da FAQ (`sql/init.sql`). Para recriar o banco do zero:

```bash
docker compose down -v
docker compose up --build
```

### Resposta com modelo de linguagem (opcional)

Sem configuração nenhuma, o bot responde só com a busca na FAQ. Para ativar o modelo de linguagem, coloque uma chave de API no `.env`:

```
LLM_API_KEY=sua_chave
```

O padrão é o Groq (`openai/gpt-oss-120b`), que tem plano gratuito. Para usar outro provedor compatível com a API da OpenAI, como o Gemini, ajuste também `LLM_BASE_URL` e `LLM_MODEL` (veja exemplos no `.env.example`).

O arquivo `.env` está no `.gitignore` e nunca deve ir para o repositório.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Confirma que a API está no ar |
| POST | `/conversas` | Abre uma conversa |
| POST | `/conversas/{id}/mensagens` | O cliente envia uma mensagem e a API responde |
| GET | `/conversas/{id}` | Devolve a conversa com todas as mensagens |
| GET | `/conversas` | Lista conversas, com filtros opcionais `cliente`, `status` e `limite` |

### Exemplo de uso

Abrir uma conversa:

```bash
curl -X POST http://localhost:8000/conversas \
  -H "Content-Type: application/json" \
  -d '{"cliente": "ana"}'
```

```json
{"id": 1, "cliente": "ana", "status": "aberta", "criada_em": "2026-11-16T20:00:00-03:00"}
```

Enviar uma mensagem:

```bash
curl -X POST http://localhost:8000/conversas/1/mensagens \
  -H "Content-Type: application/json" \
  -d '{"texto": "Qual é o prazo de entrega?"}'
```

```json
{
  "mensagem_cliente": {"id": 1, "conversa_id": 1, "autor": "cliente", "texto": "Qual é o prazo de entrega?", "criada_em": "..."},
  "resposta_bot": {"id": 2, "conversa_id": 1, "autor": "bot", "texto": "O prazo de entrega é de 3 a 7 dias úteis para capitais...", "criada_em": "..."},
  "status_conversa": "aberta"
}
```

Listar as conversas transferidas de um cliente:

```bash
curl "http://localhost:8000/conversas?cliente=ana&status=transferida"
```

### Códigos de resposta

| Código | Quando |
|---|---|
| 200 | Consulta feita com sucesso |
| 201 | Conversa ou mensagem criada |
| 404 | Conversa não encontrada |
| 422 | Dados inválidos: texto ou cliente vazio, status inexistente, limite fora de 1 a 100, id que não é número |

## Testes

Com a API no ar:

```bash
docker compose exec api pytest -v
```

Cada teste roda dentro de uma transação desfeita no final (rollback), usando `dependency_overrides` do FastAPI. Assim, os testes não sujam o banco e são independentes entre si. Os testes nunca chamam o modelo de linguagem de verdade: a chave é removida durante os testes e as respostas do modelo são simuladas com `monkeypatch`.

## Estrutura de pastas

```
mini-atendente/
├── app/
│   ├── main.py               # cria a API e registra as rotas
│   ├── db.py                 # conexão com o banco (uma por requisição)
│   ├── schemas.py            # modelos de entrada e saída (Pydantic)
│   ├── routes/
│   │   ├── health.py
│   │   └── conversas.py      # endpoints de conversa, em SQL puro
│   └── services/
│       ├── atendimento.py    # busca na FAQ e decisão da resposta
│       └── llm.py            # chamada ao modelo de linguagem
├── sql/init.sql              # tabelas, busca de texto e dados da FAQ
├── tests/                    # testes automatizados
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Decisões técnicas

- **SQL puro em vez de ORM:** as consultas ficam explícitas e fáceis de ler, incluindo a busca de texto e a listagem com `LEFT JOIN` e `GROUP BY`.
- **Validação também no banco:** restrições `CHECK` impedem status e autores inválidos e mensagens vazias, mesmo que a API falhe em validar.
- **Busca de texto do PostgreSQL:** uma coluna gerada (`tsvector`) com índice GIN guarda a versão pesquisável de cada pergunta, com peso maior para a pergunta do que para as palavras-chave. Uma configuração própria (`pt_sem_acento`) combina a extensão `unaccent` com o stemming em português.
- **Termos combinados com OU:** a mensagem do cliente não precisa conter todas as palavras de uma pergunta da FAQ. A pergunta com maior `ts_rank` é escolhida, desde que passe de uma relevância mínima.
- **O banco decide, o modelo escreve:** é a busca que define se existe resposta. O modelo só redige o texto a partir dos trechos encontrados, com instrução de não inventar informações. Isso reduz o risco de respostas inventadas.
- **Fallback:** se o modelo de linguagem falhar (rede, chave inválida, modelo desativado pelo provedor), o atendimento continua com a busca simples.
- **Provedor configurável:** o modelo é escolhido por variáveis de ambiente, então trocar de provedor ou de modelo não exige mudar o código.

## Limitações e próximos passos

- A busca simples compara palavras, não significados. Por exemplo, "vocês entregam no domingo?" recebe a resposta sobre prazo de entrega. Busca semântica com embeddings (por exemplo, `pgvector`) melhoraria a recuperação dos trechos.
- Não há autenticação: qualquer pessoa com acesso à API pode ler qualquer conversa.
- O atendente humano ainda não tem endpoints próprios para responder às conversas transferidas.