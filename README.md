# Market Automation — Gerenciamento de Estoque Doméstico

Bot Telegram integrado a uma API FastAPI para registrar consumo de alimentos e alertar quando o estoque estiver baixo.

## Stack

- Python 3.12
- FastAPI + Uvicorn
- PostgreSQL 16
- SQLAlchemy 2 + Alembic
- Pydantic v2
- python-telegram-bot 21
- Docker + Docker Compose

## Como rodar

### 1. Configure o `.env`

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/inventory
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
DEBUG=false
```

> Para obter o token, fale com o [@BotFather](https://t.me/BotFather) no Telegram.
> Para obter o chat_id, envie uma mensagem para o bot e acesse:
> `https://api.telegram.org/bot<TOKEN>/getUpdates`

### 2. Suba os containers

```bash
docker compose up --build
```

### 3. Rode as migrations

```bash
docker compose exec api alembic revision --autogenerate -m "create initial tables"
docker compose exec api alembic upgrade head
```

### 4. Acesse a documentação da API

```
http://localhost:8000/docs
```

---

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Status da API |
| `POST` | `/products` | Cadastra produto no estoque |
| `GET` | `/products` | Lista todos os produtos |
| `GET` | `/products/{name}` | Busca produto pelo nome |
| `POST` | `/consume` | Registra consumo |
| `GET` | `/alerts` | Lista produtos com estoque baixo |

### Exemplo — cadastrar produto

```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "frango", "quantity": 2.0, "unit": "kg", "minimum_quantity": 0.5}'
```

### Exemplo — registrar consumo

```bash
curl -X POST http://localhost:8000/consume \
  -H "Content-Type: application/json" \
  -d '{"product_name": "frango", "quantity": 500, "unit": "g"}'
```

---

## Comandos do Bot Telegram

### Cadastrar produto

```
/add frango 2 kg 0.5
/add leite 2 l 0.5
/add ovos 12 un 2
```

### Ver estoque

```
/estoque
```

### Registrar consumo (linguagem natural)

```
consumi 1kg de frango
usei 500ml de leite
comi 2 ovos
gastei 200g de arroz
bebi 1 litro de suco
```

---

## Alertas automáticos

Quando o estoque de um produto atingir ou ficar abaixo do limite mínimo após um consumo, o bot envia automaticamente uma mensagem:

```
⚠️ Frango está acabando. Restam apenas 0.3kg (mínimo: 0.5kg).
```

---

## Rodar os testes

```bash
pip install pytest
pytest tests/ -v
```

---

## Arquitetura em Camadas

```
Controllers  →  recebem requests HTTP / mensagens Telegram
Services     →  regras de negócio
Repositories →  acesso ao banco de dados
Models       →  entidades ORM (SQLAlchemy)
Schemas      →  DTOs de entrada e saída (Pydantic)
Utils        →  parser de mensagens e conversão de unidades
```
