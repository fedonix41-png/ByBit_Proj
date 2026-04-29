# Схема базы данных

## Обзор

Система использует PostgreSQL для хранения всех данных P2P автоматизации. База данных содержит историю ордеров, сообщений, решений и AI взаимодействий.

## Технологии
- **База данных:** PostgreSQL
- **ORM:** SQLAlchemy
- **Миграции:** Alembic

## Модели данных

### Order (orders)
Основная таблица для P2P ордеров.

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| order_id | String(100) | ID ордера на Bybit (уникальный) |
| ad_id | String(100) | ID объявления |
| side | String(10) | BUY/SELL |
| crypto | String(20) | Криптовалюта (BTC, ETH, etc.) |
| currency | String(10) | Валюта (RUB, USD, etc.) |
| amount | Float | Сумма ордера |
| price | Float | Цена за единицу |
| status | String(50) | Статус ордера |
| counterparty | String(100) | Контрагент |
| counterparty_telegram_id | String(50) | Telegram ID контрагента |
| created_at | DateTime | Время создания |
| updated_at | DateTime | Время последнего обновления |
| completed_at | DateTime | Время завершения |
| meta_info | JSON | Дополнительная информация |

**Связи:**
- messages (1:N)
- decisions (1:N)
- transactions (1:N)

### Message (messages)
Сообщения из чата с анализом AI.

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| order_id | Integer | Foreign Key → orders.id |
| message_id | String(100) | ID сообщения (уникальный) |
| sender | String(20) | me/counterparty |
| text | Text | Текст сообщения |
| intent | String(50) | Определенный intent (опционально) |
| confidence | Float | Уверенность AI (0-1) |
| entities | JSON | Извлеченные сущности |
| timestamp | DateTime | Время сообщения |
| source | String(20) | telegram/bybit |

**Связи:**
- order (N:1)

### Decision (decisions)
Записи о решениях (человеческих и автоматических).

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| order_id | Integer | Foreign Key → orders.id |
| decision_type | String(50) | response_approval/risk_approval |
| approved | Boolean | Одобрено/отклонено |
| proposed_action | Text | Предлагаемое действие |
| risk_score | Float | Оценка риска (0-1) |
| risk_flags | JSON | Флаги рисков |
| reason | Text | Обоснование решения |
| decided_by | String(50) | human/auto |
| decided_at | DateTime | Время решения |
| meta_info | JSON | Дополнительная информация |

**Связи:**
- order (N:1)

### Transaction (transactions)
Финансовые транзакции.

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| order_id | Integer | Foreign Key → orders.id |
| processing_id | String(100) | ID в процессинговой системе |
| amount | Float | Сумма транзакции |
| currency | String(10) | Валюта |
| status | String(50) | pending/completed/failed |
| payment_proof_path | String(500) | Путь к файлу доказательства оплаты |
| payment_data | JSON | Данные платежа (карта, сумма, etc.) |
| submitted_at | DateTime | Время отправки |
| completed_at | DateTime | Время завершения |
| error_message | Text | Сообщение об ошибке |
| meta_info | JSON | Дополнительная информация |

**Связи:**
- order (N:1)

### AIInteraction (ai_interactions)
История взаимодействий с AI моделями.

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| order_id | Integer | Foreign Key → orders.id (опционально) |
| agent_type | String(50) | intent/response/ocr/fraud |
| provider | String(50) | openai/anthropic/local |
| model | String(100) | Название модели |
| input_data | JSON | Входные данные |
| output_data | JSON | Выходные данные |
| tokens_used | Integer | Количество токенов |
| cost | Float | Стоимость запроса |
| latency_ms | Integer | Задержка в мс |
| created_at | DateTime | Время создания |
| meta_info | JSON | Дополнительная информация |

## ER-диаграмма

```
┌─────────────┐     ┌─────────────┐
│   Order     │     │  AIInteraction │
│             │     │                 │
│ id          │     │ id              │
│ order_id    │     │ order_id        │
│ ...         │     │ agent_type      │
└─────┬───────┘     │ ...             │
      │             └─────────────────┘
      │
      │ 1:N
      │
┌─────┴───────┐     ┌─────────────┐
│  Message    │     │  Decision   │
│             │     │             │
│ id          │     │ id          │
│ order_id    │◄────┤ order_id    │
│ text        │     │ approved    │
│ intent      │     │ ...         │
│ ...         │     └─────────────┘
└─────┬───────┘
      │
      │ 1:N
      │
┌─────┴───────┐
│ Transaction │
│             │
│ id          │
│ order_id    │
│ amount      │
│ status      │
│ ...         │
└─────────────┘
```

## Миграции

Миграции управляются через Alembic. Основные миграции:

- `001_initial_migration.py` - Создание всех таблиц
- `002_fix_schema_issues.py` - Исправления схемы

## Использование в коде

### Создание сессии
```python
from app.database.session import get_db_session

with get_db_session() as session:
    # Работа с БД
    orders = session.query(Order).all()
```

### Добавление записи
```python
from app.database.models import Order

order = Order(
    order_id="12345",
    side="BUY",
    crypto="BTC",
    currency="RUB",
    amount=0.001,
    price=5000000,
    status="active"
)
session.add(order)
session.commit()
```

### Запросы
```python
# Найти ордер по ID
order = session.query(Order).filter(Order.order_id == "12345").first()

# Получить сообщения ордера
messages = order.messages

# Получить решения по рискам
decisions = session.query(Decision).filter(
    Decision.decision_type == "risk_approval"
).all()
```