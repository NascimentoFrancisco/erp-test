# ERP Basic - API de Gestao de Pedidos

## Sobre o projeto

Este projeto e uma API REST para gerenciamento de:

- clientes
- produtos
- pedidos
- itens de pedido
- historico de status de pedidos

A aplicacao foi desenvolvida com Django + DRF, com persistencia em MySQL e suporte a cache/rate limit com Redis.

## Stack

- Python 3.12
- Django 5
- Django REST Framework
- django-filter
- MySQL
- Redis
- drf-spectacular (OpenAPI)
- Pytest
- Docker / Docker Compose

## Estrutura principal

```text
src/
|--apps/
| |--core/
  |--customers/
  |--products/
  |--orders/
  config/
tests/
```

## Variaveis de ambiente

Use `.env.example` como base:

```bash
cp .env.example .env.dev
```

Variaveis importantes:

- `DJANGO_SECRET_KEY`
- `DEBUG`
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`
- `DATABASE_HOST`
- `DATABASE_PORT`
- `REDIS_URL`
- `API_RATE_LIMIT_PER_HOUR`
- `LOG_LEVEL`
- `AUTO_SEED_ON_STARTUP`

## Como rodar com Docker (recomendado)

### 1. Build e subida dos containers

```bash
./dev.sh
```

Ou manualmente:

```bash
docker compose --env-file .env.dev -f docker-compose.dev.yml build
docker compose --env-file .env.dev -f docker-compose.dev.yml up -d
```

### 2. Acessar a API

- Base URL: `http://127.0.0.1:8000/api/v1/`
- Documentacao interativa: `http://127.0.0.1:8000/`
- Schema OpenAPI: `http://127.0.0.1:8000/docs/schema/`

## Como rodar localmente (sem Docker)

### 1. Instalar dependencias

```bash
poetry install
```

### 2. Configurar ambiente

Defina as variaveis do `.env.dev` no seu ambiente.

### 3. Executar migracoes

```bash
poetry run python src/manage.py migrate
```

### 4. (Opcional) Rodar seed inicial

```bash
poetry run python src/manage.py seed_initial_data
```

### 5. Iniciar servidor

```bash
poetry run python src/manage.py runserver 0.0.0.0:8000
```

## Seed de desenvolvimento

Quando `DEBUG=true` e `AUTO_SEED_ON_STARTUP=true`, o seed inicial e executado automaticamente no startup do container.

Comando manual:

```bash
poetry run python src/manage.py seed_initial_data
```

## Comandos basicos

### Rodar testes

```bash
poetry run pytest
```

Rodar apenas um modulo:

```bash
poetry run pytest tests/orders -q
```

### Formatacao e qualidade

```bash
poetry run black .
poetry run isort .
poetry run flake8 .
```

## Endpoints principais

### Customers

- `GET /api/v1/customers/`
- `POST /api/v1/customers/`
- `GET /api/v1/customers/<id>/`
- `PATCH /api/v1/customers/<id>/`
- `DELETE /api/v1/customers/<id>/` (soft delete)

Filtros:

- `document`
- `email`
- `is_active`

### Products

- `GET /api/v1/products/`
- `POST /api/v1/products/`
- `GET /api/v1/products/<id>/`
- `PATCH /api/v1/products/<id>/`
- `PATCH /api/v1/products/<id>/stock/`

Filtros:

- `sku`
- `name`
- `name_like`
- `is_active`

### Orders

- `GET /api/v1/orders/`
- `POST /api/v1/orders/`
- `GET /api/v1/orders/<id>/`
- `DELETE /api/v1/orders/<id>/`
- `PATCH /api/v1/orders/<id>/status/`
- `GET /api/v1/orders/<id>/items/`
- `GET /api/v1/orders/<id>/status-history/`

Filtros:

- `order_number`
- `customer`
- `status`
- `is_active`

## Exemplos de uso rapido

Listar pedidos confirmados:

```bash
curl "http://127.0.0.1:8000/api/v1/orders/?status=CONFIRMED"
```

Buscar produto por nome parcial:

```bash
curl "http://127.0.0.1:8000/api/v1/products/?name_like=notebook"
```

Filtrar clientes ativos:

```bash
curl "http://127.0.0.1:8000/api/v1/customers/?is_active=true"
```
