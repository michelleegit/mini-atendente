-- Mini Atendente: criação das tabelas e carga inicial da FAQ.
-- Este arquivo roda automaticamente na primeira vez que o container do banco sobe.

-- Busca de texto em português que ignora acentos ("cartao" encontra "cartão")
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE TEXT SEARCH CONFIGURATION pt_sem_acento (COPY = portuguese);
ALTER TEXT SEARCH CONFIGURATION pt_sem_acento
    ALTER MAPPING FOR hword, hword_part, word
    WITH unaccent, portuguese_stem;

-- Perguntas frequentes da loja
CREATE TABLE faq (
    id             SERIAL PRIMARY KEY,
    pergunta       TEXT NOT NULL,
    resposta       TEXT NOT NULL,
    palavras_chave TEXT NOT NULL DEFAULT '',
    -- Vetor de busca calculado automaticamente: a pergunta pesa mais (A)
    -- que as palavras-chave (B)
    busca          TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('pt_sem_acento', pergunta), 'A') ||
        setweight(to_tsvector('pt_sem_acento', palavras_chave), 'B')
    ) STORED
);

CREATE INDEX idx_faq_busca ON faq USING GIN (busca);

-- Uma conversa por atendimento
CREATE TABLE conversas (
    id        SERIAL PRIMARY KEY,
    cliente   VARCHAR(100) NOT NULL,
    status    VARCHAR(20)  NOT NULL DEFAULT 'aberta'
              CHECK (status IN ('aberta', 'transferida')),
    criada_em TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Mensagens trocadas dentro de cada conversa
CREATE TABLE mensagens (
    id          SERIAL PRIMARY KEY,
    conversa_id INTEGER     NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
    autor       VARCHAR(10) NOT NULL CHECK (autor IN ('cliente', 'bot')),
    texto       TEXT        NOT NULL CHECK (LENGTH(TRIM(texto)) > 0),
    criada_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para as consultas mais comuns
CREATE INDEX idx_conversas_cliente    ON conversas (cliente);
CREATE INDEX idx_mensagens_conversa   ON mensagens (conversa_id);

-- FAQ da loja fictícia "Loja Pixel", que vende eletrônicos e acessórios online
INSERT INTO faq (pergunta, resposta, palavras_chave) VALUES
('Qual é o prazo de entrega?',
 'O prazo de entrega é de 3 a 7 dias úteis para capitais e de 5 a 12 dias úteis para as demais cidades, contados a partir da confirmação do pagamento.',
 'prazo entrega chegar demora quanto tempo dias envio pedido'),

('Como acompanho meu pedido?',
 'Depois do envio, você recebe por e-mail o código de rastreio. Também é possível acompanhar em "Meus pedidos", na sua conta.',
 'rastreio rastrear acompanhar pedido código onde está chegou'),

('Quanto custa o frete?',
 'O frete é calculado pelo CEP na página do produto ou no carrinho. Compras acima de R$ 299 têm frete grátis para todo o Brasil.',
 'frete valor custo envio grátis cep'),

('Quais formas de pagamento são aceitas?',
 'Aceitamos Pix, boleto bancário e cartões de crédito das principais bandeiras.',
 'pagamento pagar pix boleto cartão crédito formas'),

('Posso parcelar a compra?',
 'Sim. No cartão de crédito, você pode parcelar em até 10 vezes sem juros, com parcela mínima de R$ 30.',
 'parcelar parcelamento parcelas vezes juros cartão'),

('Tem desconto no Pix?',
 'Sim. Pagamentos via Pix têm 5% de desconto, aplicado automaticamente no fechamento do pedido.',
 'desconto pix promoção abatimento'),

('Quanto tempo o boleto leva para compensar?',
 'O boleto é compensado em até 3 dias úteis após o pagamento. O prazo de entrega começa a contar depois da compensação.',
 'boleto compensar compensação pagamento confirmar'),

('Como faço para trocar um produto?',
 'Você tem até 30 dias após o recebimento para pedir a troca. Acesse "Meus pedidos", escolha o item e clique em "Solicitar troca". O produto deve estar na embalagem original.',
 'troca trocar substituir produto errado tamanho'),

('Como peço a devolução e o reembolso?',
 'Pelo direito de arrependimento, você pode devolver o produto em até 7 dias após o recebimento. O reembolso é feito na mesma forma de pagamento em até 10 dias úteis após recebermos o produto.',
 'devolução devolver reembolso dinheiro de volta arrependimento estorno'),

('Posso cancelar meu pedido?',
 'Pedidos ainda não enviados podem ser cancelados em "Meus pedidos". Se o pedido já foi enviado, recuse a entrega ou solicite a devolução após receber.',
 'cancelar cancelamento desistir pedido'),

('Os produtos têm garantia?',
 'Todos os produtos têm garantia de 12 meses contra defeitos de fabricação: 3 meses de garantia legal e 9 meses de garantia do fabricante.',
 'garantia defeito quebrou estragou conserto assistência'),

('Meu produto chegou com defeito, o que faço?',
 'Sentimos muito! Abra uma solicitação em "Meus pedidos" em até 7 dias após o recebimento, com fotos do defeito. Faremos a troca sem custo de frete.',
 'defeito defeituoso quebrado veio danificado avariado não funciona'),

('Como altero o endereço de entrega?',
 'O endereço pode ser alterado em "Meus pedidos" enquanto o pedido ainda não foi enviado. Depois do envio, não é possível alterar.',
 'endereço alterar mudar entrega trocar endereço'),

('A loja emite nota fiscal?',
 'Sim. A nota fiscal eletrônica é enviada por e-mail no momento do envio do pedido e também fica disponível em "Meus pedidos".',
 'nota fiscal nf nfe documento'),

('Como crio uma conta?',
 'Clique em "Entrar" no topo do site e depois em "Criar conta". Basta informar nome, e-mail, CPF e uma senha.',
 'conta cadastro cadastrar criar registrar'),

('Esqueci minha senha, como recupero?',
 'Na tela de login, clique em "Esqueci minha senha". Você vai receber no e-mail um link para criar uma nova senha.',
 'senha esqueci recuperar redefinir login acesso'),

('Existe loja física?',
 'Não. A Loja Pixel funciona somente online, com entrega para todo o Brasil.',
 'loja física endereço retirar retirada presencial'),

('Qual é o horário de atendimento?',
 'O atendimento humano funciona de segunda a sexta, das 9h às 18h, e aos sábados, das 9h às 13h. O atendente virtual responde a qualquer hora.',
 'horário atendimento funcionamento falar atendente humano');
