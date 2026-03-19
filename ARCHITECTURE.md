# Documentação Técnica — Market Automation

Guia completo do código, arquitetura e fluxos da aplicação.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura em Camadas](#2-arquitetura-em-camadas)
3. [Estrutura de Pastas](#3-estrutura-de-pastas)
4. [Camada: Infrastructure](#4-camada-infrastructure)
5. [Camada: Models](#5-camada-models)
6. [Camada: Schemas](#6-camada-schemas)
7. [Camada: Repositories](#7-camada-repositories)
8. [Camada: Services](#8-camada-services)
9. [Camada: Controllers](#9-camada-controllers)
10. [Camada: Telegram](#10-camada-telegram)
11. [Camada: Utils](#11-camada-utils)
12. [Fluxos Completos](#12-fluxos-completos)
13. [Variáveis de Ambiente](#13-variáveis-de-ambiente)
14. [Testes](#14-testes)

---

## 1. Visão Geral

O **Market Automation** é uma aplicação backend que combina uma **API REST (FastAPI)** com um **bot Telegram** para gerenciar estoque doméstico de alimentos.

O usuário pode:
- Cadastrar produtos no estoque via API ou pelo comando `/add` no Telegram
- Registrar consumo enviando frases naturais como `"consumi 1kg de frango"` no Telegram
- Consultar o estoque com `/estoque`
- Receber alertas automáticos quando um produto ficar abaixo do mínimo

Ambos — API e bot — rodam dentro do **mesmo container Docker**, compartilhando o banco PostgreSQL.

---

## 2. Arquitetura em Camadas

```
┌─────────────────────────────────────────────────┐
│               INTERFACE (Entrada)               │
│   HTTP Request          Mensagem Telegram        │
└────────────┬────────────────────┬───────────────┘
             │                    │
             ▼                    ▼
┌────────────────────┐  ┌────────────────────────┐
│    Controllers     │  │   Telegram Handlers    │
│  (FastAPI routes)  │  │  (bot commands/msgs)   │
└────────┬───────────┘  └──────────┬─────────────┘
         │                         │
         └────────────┬────────────┘
                      ▼
         ┌────────────────────────┐
         │        Services        │
         │   (regras de negócio)  │
         └────────────┬───────────┘
                      ▼
         ┌────────────────────────┐
         │      Repositories      │
         │   (acesso ao banco)    │
         └────────────┬───────────┘
                      ▼
         ┌────────────────────────┐
         │    Models (ORM)        │
         │    PostgreSQL          │
         └────────────────────────┘
```

### Regra fundamental

Cada camada só conhece a camada imediatamente abaixo:
- Controller chama Service
- Service chama Repository
- Repository chama Model
- **Nenhuma camada pula outra**

---

## 3. Estrutura de Pastas

```
market-automation/
│
├── app/
│   ├── main.py                    # Ponto de entrada da aplicação
│   │
│   ├── core/
│   │   └── config.py              # Configurações e variáveis de ambiente
│   │
│   ├── database/
│   │   ├── base.py                # Classe Base do SQLAlchemy
│   │   └── session.py             # Engine, SessionLocal, get_db()
│   │
│   ├── models/
│   │   ├── product_model.py       # Tabela "products"
│   │   └── consumption_model.py   # Tabela "consumptions"
│   │
│   ├── schemas/
│   │   ├── product_schema.py      # DTOs de produto (entrada/saída)
│   │   └── consumption_schema.py  # DTOs de consumo (entrada/saída)
│   │
│   ├── repositories/
│   │   ├── product_repository.py      # CRUD de produtos
│   │   └── consumption_repository.py  # Registro de consumos
│   │
│   ├── services/
│   │   ├── inventory_service.py   # Gerencia o estoque
│   │   ├── consumption_service.py # Registra consumo + dispara alerta
│   │   └── alert_service.py       # Verifica e gera alertas de estoque
│   │
│   ├── controllers/
│   │   ├── inventory_controller.py  # Rotas /products e /alerts
│   │   └── telegram_controller.py   # Rota /consume
│   │
│   ├── telegram/
│   │   ├── bot.py                 # Inicializa e sobe o bot
│   │   ├── handlers.py            # Processa comandos e mensagens
│   │   └── alert_sender.py        # Envia alertas proativos
│   │
│   └── utils/
│       ├── message_parser.py      # Parser de linguagem natural (regex)
│       └── unit_converter.py      # Conversão e normalização de unidades
│
├── migrations/
│   ├── env.py                     # Configuração do Alembic
│   ├── script.py.mako             # Template de migrations
│   └── versions/                  # Arquivos de migration gerados
│
├── tests/
│   ├── conftest.py
│   ├── test_message_parser.py
│   └── test_unit_converter.py
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── .env
```

---

## 4. Camada: Infrastructure

### `app/main.py` — Ponto de entrada

```
FastAPI app
    ├── on_startup()
    │       ├── Testa conexão com o banco (SELECT 1)
    │       └── Sobe o bot Telegram em uma thread separada (daemon)
    │
    └── Routers registrados:
            ├── /products  (inventory_controller)
            ├── /consume   (telegram_controller)
            └── /alerts    (alerts_router)
```

O bot roda em `threading.Thread(daemon=True)`. Isso significa que ele vive enquanto o processo principal (FastAPI) estiver vivo e é encerrado automaticamente junto com ele.

---

### `app/core/config.py` — Configurações

Usa `pydantic-settings` para ler variáveis do arquivo `.env` automaticamente.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `app_name` | `"Market Automation"` | Nome da aplicação |
| `debug` | `false` | Modo debug |
| `database_url` | `postgresql://...` | URL de conexão com o banco |
| `telegram_token` | `""` | Token do bot (BotFather) |
| `telegram_chat_id` | `""` | ID do chat para alertas automáticos |

O objeto `settings` é instanciado uma única vez na importação e compartilhado em todo o projeto via `from app.core.config import settings`.

---

### `app/database/base.py` — Base declarativa

```python
class Base(DeclarativeBase):
    pass
```

Todos os models herdam dessa `Base`. Ela mantém um `metadata` interno que registra todas as tabelas. O Alembic usa esse `metadata` para detectar mudanças e gerar migrations.

---

### `app/database/session.py` — Sessão do banco

| Objeto | Tipo | Função |
|--------|------|--------|
| `engine` | `Engine` | Conexão física com o PostgreSQL |
| `SessionLocal` | `sessionmaker` | Fábrica de sessões — cada chamada cria uma sessão nova |
| `get_db()` | `Generator` | Dependency injection do FastAPI — abre sessão, injeta, fecha automaticamente |

O padrão `yield` no `get_db()` garante que a sessão seja sempre fechada, mesmo se houver exceção:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db      # FastAPI injeta aqui
    finally:
        db.close()    # sempre executado
```

---

### `alembic.ini` + `migrations/env.py` — Migrations

O Alembic lê o `DATABASE_URL` do ambiente (sobrepõe o `alembic.ini`) e importa todos os models via `import app.models` para detectar as tabelas automaticamente.

Comandos importantes:
```bash
# Gerar migration a partir dos models
alembic revision --autogenerate -m "descrição"

# Aplicar migrations pendentes
alembic upgrade head

# Reverter a migration anterior
alembic downgrade -1
```

---

## 5. Camada: Models

Os models são classes Python que representam tabelas no banco. Usam a **API moderna do SQLAlchemy 2.0** com `Mapped` e `mapped_column`.

### `Product` — tabela `products`

| Campo | Tipo SQL | Descrição |
|-------|----------|-----------|
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `name` | `VARCHAR(100) UNIQUE` | Nome do produto (case-insensitive nas buscas) |
| `quantity` | `FLOAT` | Quantidade atual em estoque |
| `unit` | `VARCHAR(20)` | Unidade de medida (kg, l, un, etc.) |
| `minimum_quantity` | `FLOAT` | Limite mínimo para alerta |
| `created_at` | `TIMESTAMPTZ` | Data de criação (gerada pelo banco) |

Relacionamento:
```python
consumptions: Mapped[list["Consumption"]] = relationship(
    back_populates="product",
    cascade="all, delete-orphan"  # deleta consumos ao deletar produto
)
```

---

### `Consumption` — tabela `consumptions`

| Campo | Tipo SQL | Descrição |
|-------|----------|-----------|
| `id` | `SERIAL PRIMARY KEY` | Identificador único |
| `product_id` | `INT FOREIGN KEY` | Referência ao produto |
| `quantity` | `FLOAT` | Quantidade consumida |
| `unit` | `VARCHAR(20)` | Unidade do consumo (pode diferir do produto) |
| `created_at` | `TIMESTAMPTZ` | Data do consumo (gerada pelo banco) |

O campo `unit` na `Consumption` registra a unidade **como o usuário informou** (ex: "g"), mesmo que o produto esteja em "kg". A conversão acontece na camada de serviço.

---

## 6. Camada: Schemas

Os schemas são classes Pydantic que controlam **o que entra e o que sai** da API. Eles são separados dos models ORM intencionalmente.

### Por que separar Schema de Model?

| Model ORM | Schema Pydantic |
|-----------|----------------|
| Representa a tabela no banco | Representa os dados da API |
| Tem todos os campos | Expõe só o necessário |
| Pode ter relações complexas | É simples e serializável |
| Mutável durante o ciclo de vida | Validado na entrada/saída |

### Schemas de Produto

```
ProductCreate     → dados que o cliente envia para CRIAR um produto
ProductUpdate     → dados para ATUALIZAR quantidade/unidade
ProductResponse   → dados que a API RETORNA (inclui id, created_at, is_low_stock)
```

O campo `is_low_stock` em `ProductResponse` **não existe no banco** — é calculado pelo `InventoryService` e injetado no schema antes de retornar.

### Schemas de Consumo

```
ConsumptionCreate   → produto_name + quantity + unit (entrada)
ConsumptionResponse → id + product_id + quantity + unit + created_at (saída)
```

`ConsumptionCreate` usa `product_name` (string) em vez de `product_id` (int) para facilitar o uso via Telegram — o usuário digita o nome, o sistema resolve o ID.

### `ConfigDict(from_attributes=True)`

Presente nos schemas de resposta. Permite fazer:
```python
ProductResponse.model_validate(product_orm_object)
```
O Pydantic lê os atributos do objeto SQLAlchemy diretamente, sem precisar converter para dicionário antes.

---

## 7. Camada: Repositories

Responsáveis por **todo o acesso ao banco**. Nenhuma outra camada escreve SQL.

### `ProductRepository`

| Método | SQL equivalente | Retorno |
|--------|----------------|---------|
| `get_all()` | `SELECT * FROM products` | `list[Product]` |
| `get_by_id(id)` | `SELECT * WHERE id = ?` | `Product \| None` |
| `get_by_name(name)` | `SELECT * WHERE name ILIKE ?` | `Product \| None` |
| `create(product)` | `INSERT INTO products ...` | `Product` |
| `update(product)` | `UPDATE products SET ...` | `Product` |
| `delete(product)` | `DELETE FROM products WHERE id = ?` | `None` |

`ILIKE` faz busca **case-insensitive**: "frango", "Frango" e "FRANGO" retornam o mesmo produto.

### `ConsumptionRepository`

| Método | Descrição |
|--------|-----------|
| `create(consumption)` | Registra novo consumo no banco |
| `get_by_product(product_id)` | Histórico de consumo de um produto (mais recente primeiro) |

### Padrão de persistência

```python
db.add(obj)      # 1. Adiciona à sessão (em memória)
db.commit()      # 2. Grava no banco (transação)
db.refresh(obj)  # 3. Recarrega do banco (pega id, created_at, etc.)
```

---

## 8. Camada: Services

Onde ficam as **regras de negócio**. Os services orquestram repositories, validam regras e tomam decisões.

### `InventoryService`

Gerencia o estoque de produtos.

**`add_product(data)`**
1. Verifica se já existe produto com o mesmo nome (via `get_by_name`)
2. Se sim → lança `ValueError` (vira HTTP 409 no controller)
3. Se não → cria o `Product` ORM e chama `ProductRepository.create()`
4. Converte o resultado para `ProductResponse` com `is_low_stock` calculado

**`_to_response(product)`** — método interno
```python
response = ProductResponse.model_validate(product)  # ORM → schema
response.is_low_stock = product.quantity <= product.minimum_quantity
return response
```

---

### `ConsumptionService`

Orquestra o fluxo mais complexo da aplicação.

**`register(data)`** — passo a passo:

```
1. Busca o produto pelo nome
       └── Não encontrado → ValueError

2. Converte a unidade do consumo para a unidade do produto
       Exemplo: data.unit="g", product.unit="kg"
       └── to_base_unit(500, "g", "kg") = 0.5

3. Verifica se há estoque suficiente
       └── product.quantity < quantidade_convertida → ValueError

4. Deduz a quantidade do estoque
       product.quantity = round(2.0 - 0.5, 4) = 1.5

5. Salva o produto atualizado (ProductRepository.update)

6. Cria o registro de Consumption (ConsumptionRepository.create)

7. Verifica se ficou abaixo do mínimo
       └── Se sim E se TELEGRAM_CHAT_ID configurado:
               → send_alert() envia mensagem no Telegram

8. Retorna ConsumptionResponse
```

O `round(..., 4)` na etapa 4 evita erros de ponto flutuante (ex: `1.0 - 0.3 = 0.7000000000000001`).

---

### `AlertService`

**`check_low_stock(product_name)`**
- Busca o produto pelo nome
- Se `quantity <= minimum_quantity` → retorna string com a mensagem de alerta
- Caso contrário → retorna `None`

**`get_all_low_stock_alerts()`**
- Busca todos os produtos
- Filtra os que estão abaixo do mínimo
- Retorna lista de strings prontas para exibição

---

## 9. Camada: Controllers

Os controllers conectam as requisições HTTP aos services. Eles não contêm lógica de negócio.

### Endpoints disponíveis

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/health` | 200 | Verifica se a API está no ar |
| `POST` | `/products/` | 201 | Cadastra produto |
| `GET` | `/products/` | 200 | Lista todos os produtos |
| `GET` | `/products/{name}` | 200 / 404 | Busca produto pelo nome |
| `POST` | `/consume/` | 201 | Registra consumo |
| `GET` | `/alerts/` | 200 | Lista produtos com estoque baixo |

### Tratamento de erros

Os controllers convertem `ValueError` dos services em respostas HTTP adequadas:

```python
try:
    return InventoryService(db).add_product(data)
except ValueError as e:
    raise HTTPException(status_code=409, detail=str(e))
```

| Exceção | Status HTTP | Situação |
|---------|------------|----------|
| `ValueError` no create | 409 Conflict | Produto já existe |
| `ValueError` no get | 404 Not Found | Produto não encontrado |
| `ValueError` no consume | 400 Bad Request | Estoque insuficiente / produto não encontrado |

### `ConsumeResponse`

O endpoint `POST /consume/` retorna mais do que o consumo em si:

```python
class ConsumeResponse(ConsumptionResponse):
    alert: str | None = None  # mensagem de alerta, se aplicável
```

Isso permite que o cliente da API saiba, em uma única chamada, se o estoque ficou baixo.

### Injeção de dependência com `Depends`

```python
def list_products(db: Session = Depends(get_db)):
```

O FastAPI chama `get_db()` automaticamente antes de executar o endpoint, injeta a sessão, e a fecha após a resposta. O controller nunca gerencia o ciclo de vida do banco.

---

## 10. Camada: Telegram

### `telegram/bot.py` — Inicialização

Responsável por construir e subir o bot.

**`build_application()`**
- Cria o `Application` com o token do `.env`
- Registra os handlers:
  - `CommandHandler("add", cmd_add)` → `/add`
  - `CommandHandler("estoque", cmd_estoque)` → `/estoque`
  - `MessageHandler(TEXT & ~COMMAND, handle_consumption)` → qualquer texto que não seja comando

**`start_bot()`**
- Cria um novo event loop (`asyncio.new_event_loop()`) — necessário pois roda em thread secundária
- Chama `_run_bot()` que usa a API async direta (sem `run_polling()`) para evitar o erro de signal handler que só funciona na thread principal

```python
async def _run_bot():
    async with application:
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()  # mantém rodando para sempre
```

---

### `telegram/handlers.py` — Handlers

**`handle_consumption(update, context)`** — mensagens de texto livres

```
1. Lê o texto da mensagem
2. Chama parse_consumption_message() → ParsedConsumption ou None
3. Se None → responde com instruções de uso
4. Se válido:
       → ConsumptionService.register()
       → AlertService.check_low_stock()
       → Responde: "✅ Registrado: 500g de frango" + alerta se houver
```

**`cmd_add(update, context)`** — `/add <nome> <qty> <unidade> <minimo>`

```
Exemplo: /add frango 2 kg 0.5
         context.args = ["frango", "2", "kg", "0.5"]

1. Valida que vieram 4 argumentos
2. Faz parse dos tipos (float para quantidade e mínimo)
3. Chama InventoryService.add_product()
4. Responde com confirmação ou erro
```

**`cmd_estoque(update, context)`** — `/estoque`

```
1. Busca todos os produtos via InventoryService.get_all_products()
2. Para cada produto:
       ✅ se quantity > minimum_quantity
       ⚠️ se quantity <= minimum_quantity
3. Responde com lista formatada em Markdown
```

---

### `telegram/alert_sender.py` — Alertas proativos

```python
async def send_alert(chat_id, message):
    bot = Bot(token=settings.telegram_token)
    await bot.send_message(chat_id=chat_id, text=message)
```

Diferente dos handlers (que respondem a mensagens do usuário), o `send_alert` **inicia** uma conversa — envia mensagem sem o usuário ter pedido. Por isso precisa do `TELEGRAM_CHAT_ID`.

Como é chamado de dentro do `ConsumptionService` (código síncrono), usa `asyncio.run()` para executar a corotina.

---

## 11. Camada: Utils

### `utils/message_parser.py` — Parser de linguagem natural

Interpreta frases de consumo usando **expressões regulares (regex)**.

Dois padrões:

**Com unidade** — `_PATTERN_WITH_UNIT`
```
"consumi  500g    de  frango"
    ^       ^         ^
  verbo  qty+unit   produto
```
Regex simplificado: `(verbo)\s+(número)(unidade)\s+(de\s+)?(produto)`

**Sem unidade** — `_PATTERN_WITHOUT_UNIT`
```
"comi  2  ovos"
   ^   ^    ^
 verbo qty produto  → unit = "un"
```

Verbos aceitos: `consumi | usei | gastei | utilizei | comi | bebi | tomei`

O parser usa `fullmatch()` em vez de `match()` — isso exige que o regex cubra **toda a string**, evitando falsos positivos.

**Retorno:**
```python
@dataclass
class ParsedConsumption:
    product_name: str   # "frango"
    quantity: float     # 500.0
    unit: str           # "g"
```

---

### `utils/unit_converter.py` — Conversão de unidades

**`normalize_unit(unit)`**
Converte aliases textuais para símbolo canônico:
```
"quilogramas" → "kg"
"litros"      → "l"
"mililitros"  → "ml"
"gramas"      → "g"
"unidades"    → "un"
```

**`to_base_unit(quantity, from_unit, product_unit)`**
Converte a quantidade consumida para a unidade do produto:
```
to_base_unit(500, "g",  "kg") → 0.5
to_base_unit(200, "ml", "l")  → 0.2
to_base_unit(1,   "kg", "g")  → 1000.0
```

Usa uma tabela de fatores:
```python
_CONVERSION_TABLE = {
    ("g",  "kg"): 0.001,
    ("kg", "g"):  1000.0,
    ("ml", "l"):  0.001,
    ("l",  "ml"): 1000.0,
}
```

Lança `ValueError` se tentar converter entre grandezas diferentes (ex: "g" → "l").

**`format_quantity(quantity, unit)`**
```
1.5  + "kg" → "1.5kg"
2.0  + "un" → "2un"     (o :g remove o .0 desnecessário)
```

---

## 12. Fluxos Completos

### Fluxo 1 — Cadastrar produto via API

```
POST /products/
Body: {"name": "frango", "quantity": 2.0, "unit": "kg", "minimum_quantity": 0.5}

1. FastAPI valida o body com ProductCreate (Pydantic)
2. inventory_controller.create_product() é chamado
3. Depends(get_db) injeta a sessão do banco
4. InventoryService(db).add_product(data)
       → ProductRepository.get_by_name("frango") → None (não existe)
       → Cria Product ORM
       → ProductRepository.create(product)
               → db.add() + db.commit() + db.refresh()
       → _to_response(): calcula is_low_stock = (2.0 <= 0.5) = False
5. Retorna ProductResponse com status 201
```

---

### Fluxo 2 — Registrar consumo via Telegram

```
Usuário envia: "consumi 500g de frango"

1. MessageHandler captura o texto (não é comando)
2. handle_consumption() é chamado
3. parse_consumption_message("consumi 500g de frango")
       → _PATTERN_WITH_UNIT.fullmatch()
       → ParsedConsumption(product_name="frango", quantity=500.0, unit="g")
4. ConsumptionService(db).register(ConsumptionCreate(...))
       → ProductRepository.get_by_name("frango") → Product(qty=2.0, unit="kg")
       → to_base_unit(500, "g", "kg") = 0.5
       → 2.0 >= 0.5 ✓ (estoque suficiente)
       → product.quantity = round(2.0 - 0.5, 4) = 1.5
       → ProductRepository.update(product)
       → ConsumptionRepository.create(Consumption(...))
       → 1.5 > 0.5 (não é baixo) → sem alerta
5. Resposta: "✅ Registrado: 500.0g de frango."
```

---

### Fluxo 3 — Alerta automático de estoque baixo

```
Usuário envia: "consumi 1.6kg de frango"
(estoque atual: 2.0kg, mínimo: 0.5kg)

1-4. (mesmo fluxo acima)
       → product.quantity = round(2.0 - 1.6, 4) = 0.4

5. 0.4 <= 0.5 (mínimo) → dispara alerta
       → asyncio.run(send_alert(chat_id, "⚠️ Frango está acabando..."))
               → Bot.send_message() → mensagem chega no Telegram

6. Resposta para o usuário:
   "✅ Registrado: 1.6kg de frango.
    ⚠️ Frango está acabando. Restam apenas 0.4kg (mínimo: 0.5kg)."
```

---

### Fluxo 4 — Startup da aplicação

```
docker compose up
    │
    ├── db (PostgreSQL) sobe e passa no healthcheck
    │
    └── api (FastAPI) sobe
            │
            ├── uvicorn carrega app/main.py
            ├── Routers são registrados (/products, /consume, /alerts)
            │
            └── on_startup() executa:
                    ├── engine.connect() → SELECT 1 → banco OK
                    └── Thread(target=start_bot, daemon=True).start()
                                │
                                ├── asyncio.new_event_loop()
                                ├── build_application() → registra handlers
                                ├── application.start()
                                └── updater.start_polling() → bot ativo
```

---

## 13. Variáveis de Ambiente

Arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/inventory
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
DEBUG=false
```

| Variável | Como obter |
|----------|-----------|
| `TELEGRAM_TOKEN` | Fale com [@BotFather](https://t.me/BotFather) no Telegram → `/newbot` |
| `TELEGRAM_CHAT_ID` | Envie uma mensagem pro bot e acesse `https://api.telegram.org/bot<TOKEN>/getUpdates` |

---

## 14. Testes

### `tests/test_message_parser.py`

Testa o parser de linguagem natural com `pytest.parametrize`.

Categorias testadas:
- Unidades abreviadas: `"consumi 1kg de frango"`
- Unidades por extenso: `"usei 500 gramas de farinha"`
- Decimal com vírgula: `"consumi 1,5kg de frango"`
- Sem unidade: `"consumi 2 ovos"`
- Sem preposição "de": `"consumi 1kg frango"`
- Outros verbos: `"tomei 1 litro de leite"`
- Mensagens inválidas: `"olá"`, `"comprei frango"`, `""`

### `tests/test_unit_converter.py`

Testa a conversão de unidades com 3 classes de teste:

- `TestNormalizeUnit` — 20 aliases diferentes
- `TestToBaseUnit` — 16 conversões válidas + 6 pares incompatíveis
- `TestFormatQuantity` — 5 formatos de exibição

```bash
# Rodar os testes
pytest tests/ -v
```
