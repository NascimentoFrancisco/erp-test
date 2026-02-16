# ARCHITECTURE - Sistema ERP (Módulo de Gestão de Pedidos)

## 1. Contexto e Objetivo

Este documento descreve a arquitetura da API de gestão de pedidos implementada com Django REST Framework, considerando o contexto do desafio técnico de nível pleno.

Foco deste documento:

- Padrões arquiteturais adotados
- Como o fluxo de dados funciona
- Decisões técnicas e compensações arquiteturais

Escopo funcional coberto:

- Clientes
- Produtos
- Pedidos
- Itens de pedido
- Histórico de status

## 2. Stack Técnica e Infraestrutura

Backend:

- Python 3.12
- Django 5
- Django REST Framework
- django-filter

Dados e performance:

- MySQL (persistência relacional)
- Redis (cache e rate limiting)

Documentação e DX:

- drf-spectacular (OpenAPI)
- RapiDoc (UI de docs)

Containerização:

- Docker + Docker Compose
- Dockerfile com multi-stage build

Testes:

- pytest + pytest-django

## 3. Padrões Arquiteturais Adotados

## 3.1 Arquitetura modular por domínio

A aplicação está organizada em apps Django independentes por contexto:

- `apps/customers`
- `apps/products`
- `apps/orders`
- `apps/core` (infraestrutura compartilhada)

Cada módulo segue a separação:

- `models.py`: estrutura e regras de persistência
- `serializers.py`: validação de entrada e corpo de saída
- `filters.py`: filtragem declarativa para listagens
- `views.py`: orquestração de casos de uso HTTP
- `urls.py`: exposição de rotas

## 3.2 Estilo arquitetural dominante

O projeto segue uma organização em camadas, comum no ecossistema Django/DRF:

- **Camada de entrada (HTTP):** ViewSets (views.py), responsáveis por receber as requisições e devolver as respostas.
- **Camada de regras e validações:** serializers e métodos das views, onde ficam as validações e parte das regras de negócio.
- **Camada de persistência:** ORM do Django, responsável por acessar e manipular os dados no banco.

Não há, no estado atual, uma camada separada de `Service` e `Repository` como abstrações formais. A lógica crítica fica principalmente em serializers e views.

## 3.3 SOLID na prática (estado atual)

- SRP: razoável separação entre serializers, views e models.
- OCP: ViewSets permitem extensão por actions sem quebrar contrato existente.
- DIP: parcialmente atendido; dependências ainda são concretas (ORM direto nas views/serializers).

Principal compensação arquitetural: menor volume de código estrutural e maior velocidade de entrega, ao custo de maior acoplamento ao framework.

## 4. Modelagem e Fluxo de Dados (Macro)

## 4.1 Entidades

- Customer
- Product
- Order
- OrderItem
- OrderStatusHistory

## 4.2 Relacionamentos

- `Customer (1) -> (N) Order`
- `Order (1) -> (N) OrderItem`
- `Product (1) -> (N) OrderItem`
- `Order (1) -> (N) OrderStatusHistory`

## 4.3 Soft delete

`Customer`, `Product` e `Order` herdam de `CoreModel`:

- UUID como PK
- `created_at`, `updated_at`
- `deleted_at`
- manager padrão filtrando apenas ativos (`deleted_at IS NULL`)

## 4.4 Integridade

- `unique` em campos críticos (ex.: `order_number`, `idempotency_key`, `document`, `sku`).
- FKs com `PROTECT` onde histórico precisa ser preservado (ex.: item -> produto).
- Índices em campos de busca frequente (`status`, `created_at`, `customer`, etc.).

## 4.5 Models por entidade (estrutura e justificativa)

Esta seção detalha os models definidos no projeto e o motivo de cada desenho, alinhado ao objetivo do módulo: consistência transacional, resiliência a falhas/retries e capacidade de crescimento.

### Core (base compartilhada)

#### `TimeStampedModel` (abstrato)

Campos:

- `created_at`
- `updated_at`

Motivo:

- padronizar rastreabilidade temporal em todas as entidades de negócio.
- reduzir duplicação de código.

#### `CoreModel` (abstrato)

Campos:

- `id` (UUID, PK)
- `deleted_at` (soft delete)

Managers:

- `objects` (somente ativos)
- `all_objects` (ativos + deletados)

Motivo:

- UUID melhora distribuição/segurança de identificadores em API pública.
- soft delete preserva histórico sem perder integridade referencial.
- separação `objects`/`all_objects` evita expor deletados por padrão.

### Customers

#### `Customer`

Campos principais:

- `name`
- `document` (único, validado)
- `email` (único)
- `phone`
- `address`
- `is_active`
- herdados de `CoreModel` (`id`, `created_at`, `updated_at`, `deleted_at`)

Motivo:

- `document` e `email` únicos evitam duplicidade de cadastro.
- `is_active` atende regra de negócio de cliente ativo/inativo sem excluir histórico.
- herança de `CoreModel` permite soft delete e auditoria temporal.

### Products

#### `Product`

Campos principais:

- `sku` (único)
- `name`
- `description`
- `price`
- `stock_quantity`
- `is_active`
- herdados de `CoreModel`

Motivo:

- `sku` único garante identificação operacional estável do item.
- `stock_quantity` é `PositiveIntegerField` para impedir estoque negativo por tipo.
- `is_active` permite descontinuar produto sem perder referência histórica.

### Orders

#### `Order`

Campos principais:

- `order_number` (único, gerado automaticamente)
- `customer` (FK para `Customer`, `PROTECT`)
- `status` (enum)
- `total_amount`
- `idempotency_key` (única)
- `observations`
- herdados de `CoreModel`

Motivo:

- `order_number` único facilita rastreabilidade funcional para negócio.
- `idempotency_key` garante resiliência a retry de cliente (não duplica pedido).
- `customer` com `PROTECT` preserva integridade histórica de pedidos.
- `status` como enum reduz estados inválidos e melhora consistência de fluxo.

#### `OrderItem`

Campos principais:

- `order` (FK para `Order`, `CASCADE`)
- `product` (FK para `Product`, `PROTECT`)
- `quantity`
- `unit_price`
- `subtotal`
- `created_at`, `updated_at`

Motivo:

- `unit_price` armazena snapshot do preço no momento da compra.
- `subtotal` persistido evita recálculo e garante consistência histórica.
- `product` com `PROTECT` impede perder referência de item vendido.
- `order` com `CASCADE` remove itens somente quando o pedido for removido fisicamente.

#### `OrderStatusHistory`

Campos principais:

- `order` (FK para `Order`, `CASCADE`)
- `previous_status`
- `new_status`
- `changed_by`
- `reason`
- `created_at`

Motivo:

- trilha de auditoria de transições de status.
- suporte à análise operacional (quem alterou, quando alterou e por que alterou).
- separação em tabela dedicada evita sobrecarregar a entidade `Order` com log interno.

## 5. Fluxo de Requisição HTTP

1. Request entra por `config/urls.py` em `/api/v1/...`.
2. `RequestLoggingMiddleware` resolve/gera `X-Correlation-ID`.
3. DRF aplica throttling global (`ClientOrIPRateThrottle`) com backend Redis.
4. ViewSet resolve action/serializer e executa validações.
5. ORM interage com MySQL.
6. Response é retornada com cabeçalho `X-Correlation-ID`.
7. Log JSON é emitido com status, latência, IP e correlation id.

## 6. Fluxo de Dados por Endpoint (Detalhado)

## 6.1 Customers

### POST `/api/v1/customers/`

Fluxo:

1. Payload entra via `CustomerModelSerializer`.
2. DRF valida campos obrigatórios e unicidade (`document`, `email`).
3. ORM cria `Customer`.
4. Retorna `201` com objeto criado.

Regras:

- documento validado por validator customizado
- `is_active` default true

### GET `/api/v1/customers/`

Fluxo:

1. Queryset base: `Customer.objects` (ativos por soft delete manager).
2. Filtros com `CustomerFilter` (`document`, `email`, `is_active`).
3. Paginação por `PersonalPagination`.
4. Retorna `200` com envelope paginado.

### GET `/api/v1/customers/:id`

Fluxo:

1. `get_object_or_404` por UUID.
2. Retorna `200` com dados do cliente.

### PATCH `/api/v1/customers/:id`

Fluxo:

1. Busca por UUID.
2. Serializer aplica validação parcial.
3. Persiste campos alterados.
4. Retorna `200`.

### DELETE `/api/v1/customers/:id`

Fluxo:

1. Busca por UUID.
2. Executa `soft_delete()`.
3. Retorna `204`.

## 6.2 Products

### POST `/api/v1/products/`

Fluxo:

1. Valida payload com `ProductModelSerializer`.
2. Cria produto.
3. Retorna `201`.

### GET `/api/v1/products/`

Fluxo:

1. Queryset base: produtos ativos (soft delete manager).
2. Filtros `ProductFilter`: `sku`, `name`, `name_like`, `is_active`.
3. Paginação padrão.
4. Retorna `200`.

### GET `/api/v1/products/:id`

Fluxo:

1. Busca por UUID.
2. Retorna `200`.

### PATCH `/api/v1/products/:id`

Fluxo:

1. Busca por UUID.
2. Atualização parcial via serializer.
3. Retorna `200`.

### PATCH `/api/v1/products/:id/stock/`

Fluxo:

1. Busca produto.
2. Valida `stock_quantity >= 0` com `ProductStockUpdateSerializer`.
3. Aplica `update_stock`.
4. Retorna `200` com estado atualizado.

## 6.3 Orders

### POST `/api/v1/orders/` (fluxo crítico)

Fluxo interno:

1. Payload validado por `OrderCreateSerializer`:
   - `customer_id` deve existir e estar ativo
   - `items` não pode ser vazio
   - `quantity` > 0 por item
2. Idempotência:
   - busca `Order` por `idempotency_key`
   - se existir, retorna pedido existente
3. Se não existir, entra em `transaction.atomic()`.
4. Para cada item:
   - lock pessimista no produto com `select_for_update()`
   - valida produto ativo e estoque suficiente
5. Cria `Order`.
6. Debita estoque com update atômico (`F("stock_quantity") - quantity`).
7. Cria `OrderItem` com snapshot de preço (`unit_price`) e `subtotal`.
8. Calcula e persiste `total_amount`.
9. Retorna `201` (ou `200` em repetição idempotente).

Garantias de negócio:

- Reserva de estoque atômica
- Falha parcial = rollback total
- Proteção à corrida de concorrência por lock em linha

### GET `/api/v1/orders/`

Fluxo:

1. Queryset base:
   - normal: `Order.objects` (ativos)
   - se `is_active` presente: `Order.all_objects` (ativos + deletados)
2. Filtros `OrderFilter`:
   - `order_number` (icontains)
   - `customer` (UUID)
   - `status` (choices)
   - `is_active` (mapeado para `deleted_at`)
3. Paginação padrão.
4. Retorna `200`.

### GET `/api/v1/orders/:id`

Fluxo:

1. Busca por UUID.
2. Retorna `200` com detalhe do pedido.

### PATCH `/api/v1/orders/:id/status`

Fluxo:

1. Busca pedido.
2. Valida transição via `OrderStatusUpdateSerializer`:
   - PENDING -> CONFIRMED/CANCELED
   - CONFIRMED -> SEPARATED/CANCELED
   - SEPARATED -> SHIPPED
   - SHIPPED -> DELIVERED
3. Em transação:
   - atualiza status no pedido
   - registra `OrderStatusHistory` com `previous_status`, `new_status`, `changed_by`, `reason`
4. Retorna `200`.

### DELETE `/api/v1/orders/:id`

Fluxo:

1. Busca pedido.
2. Valida cancelamento apenas em `PENDING` ou `CONFIRMED`.
3. Em transação:
   - lock nos itens
   - devolução de estoque item a item
   - status -> `CANCELED`
4. Retorna `204`.

### GET `/api/v1/orders/:id/items/`

Fluxo:

1. Busca pedido.
2. Lista `OrderItem` do pedido com `select_related("product")`.
3. Retorna `200`.

### GET `/api/v1/orders/:id/status-history/`

Fluxo:

1. Busca pedido.
2. Lista histórico ordenado por `created_at`.
3. Retorna `200`.

## 7. Regras Críticas e Como Foram Implementadas

## 7.1 Controle de estoque

Atendido com:

- `transaction.atomic()`
- `select_for_update()` nos produtos
- update com `F()` para evitar race conditions
- rollback automático em exceção

## 7.2 Transições de status

Atendido com:

- mapa de transições válidas (`VALID_TRANSITIONS`)
- rejeição de transições inválidas via `ValidationError`
- persistência do histórico de mudança

## 7.3 Idempotência

Atendido com:

- `idempotency_key` única no banco
- short-circuit para retorno de pedido existente

## 7.4 Validações de negócio

Atendido com:

- cliente ativo obrigatório
- produto ativo e estoque suficiente
- quantidade mínima por item
- preço unitário capturado do produto no momento da compra

## 8. Observabilidade e Operação

## 8.1 Logs estruturados

- Formatter JSON custom
- Níveis: INFO, WARN (warning), ERROR
- Correlation ID propagado por middleware

## 8.2 Rate limiting

- Throttle por usuário autenticado (quando existir) ou por IP
- Backend de controle via Redis
- taxa configurável por env: `API_RATE_LIMIT_PER_HOUR`

## 8.3 Paginação e filtros

- Paginação padrão em listagens (`total`, `page`, `page_size`, `total_pages`, `results`)
- Filtros declarativos via django-filter

## 9. DevOps e Ambiente

Implementado:

- Dockerfile multi-stage
- docker-compose para API + MySQL + Redis
- `.env.example`
- seed de desenvolvimento automático (DEBUG + `AUTO_SEED_ON_STARTUP`)

Ponto de atenção:

- `docker-compose` referencia `/health` no healthcheck da API, mas endpoint dedicado de health não está exposto no roteamento atual.

## 10. Testes e Cobertura de Cenários

Coberto na suite:

- criação/listagem/atualização dos módulos
- concorrência de estoque (cenário 10 unidades vs 2 pedidos simultâneos de 8)
- idempotência de criação de pedido
- falha atômica em falta de estoque
- filtros e paginação
- histórico de status

## 11. Decisões Técnicas e Trade-offs

## 11.1 DRF ViewSet + Serializer em vez de Service/Repository formal

Decisão:

- manter arquitetura mais simples e idiomática Django

Benefício:

- maior produtividade e menor boilerplate

Trade-off:

- regras de negócio ficam espalhadas entre serializer e view
- menor isolamento para testes unitários puros de domínio

## 11.2 MySQL + Redis

Decisão:

- MySQL para consistência transacional
- Redis para concerns transversais de desempenho/controle

Benefício:

- ACID no core de pedidos
- throttling rápido e distribuído

Trade-off:

- maior complexidade operacional (mais componentes)

## 11.3 Soft delete no modelo base

Decisão:

- remover logicamente em vez de delete físico

Benefício:

- preserva histórico

Trade-off:

- consultas precisam considerar `deleted_at`
- necessidade de `all_objects` em casos específicos (ex.: filtro `is_active=false`)

## 11.4 Idempotência no endpoint de pedidos

Decisão:

- chave de idempotência persistida em banco

Benefício:

- resiliência a retries de cliente

Trade-off:

- exige disciplina de clientes para enviar chave estável

## 11.5 Status history sem event bus externo

Decisão:

- persistir histórico síncrono em tabela relacional

Benefício:

- simples de operar e auditar

Trade-off:

- não implementa event sourcing completo nem publicação assíncrona de domain events externos

## 12. Aderência ao Enunciado (Resumo objetivo)

Atendido:

- DRF + MySQL + Redis
- docker/multi-stage
- CRUD principal e fluxos críticos de pedido
- idempotência
- transições de status com histórico
- soft delete
- paginação
- filtros
- rate limit
- logs estruturados com correlation id
- testes cobrindo cenários centrais
