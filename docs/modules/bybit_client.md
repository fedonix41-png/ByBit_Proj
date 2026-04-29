# Bybit API Клиент

**Файл:** `bybit_client.py`

## Режимы работы

| Режим | Условие | Описание |
|-------|---------|----------|
| **Testnet** | `BYBIT_TESTNET=True` | Безопасная разработка |
| **Production** | `BYBIT_TESTNET=False` | Реальные средства |
| **Mock** | `USE_MOCK_DATA=True` | Без API вызовов |

## Singleton

```python
from bybit_client import bybit_client

# Единственный экземпляр
bybit_client.get_ads_list()
```

---

## Методы

### Получение данных

```python
# Список объявлений
ads = bybit_client.get_ads_list()  # List[Order]

# Сообщения чата
messages = bybit_client.get_chat_messages(order_id)  # List[ChatMessage]

# Детали ордера
details = bybit_client.get_order_details(order_id)  # Dict

# Баланс
balance = bybit_client.get_balance()  # List[Balance]

# Способы оплаты
methods = bybit_client.get_payment_methods()  # List[Dict]

# История торгов
history = bybit_client.get_trade_history(limit=20)  # List[Dict]
```

### Действия

```python
# Отправить сообщение
success = bybit_client.send_chat_message(order_id, "Текст сообщения")

# Подтвердить платёж
success = bybit_client.confirm_payment(order_id)

# Создать ордер
order_id = bybit_client.create_order(
    side="SELL",
    currency="RUB",
    crypto="USDT",
    price=95.5,
    amount=1000
)

# Отменить ордер
success = bybit_client.cancel_order(order_id)

# Создать апелляцию
success = bybit_client.appeal_order(order_id, "Причина")
```

---

## Модели данных

### Order

```python
class Order(BaseModel):
    order_id: str
    ad_id: Optional[str]
    side: Literal["BUY", "SELL"]
    currency: str
    crypto: str
    price: float
    amount: float
    status: str
    created_at: Optional[datetime]
    counterparty: Optional[str]
```

### ChatMessage

```python
class ChatMessage(BaseModel):
    message_id: str
    order_id: str
    sender: Literal["me", "counterparty"]
    text: str
    timestamp: datetime
    read: bool = False
```

### Balance

```python
class Balance(BaseModel):
    currency: str
    available: float
    locked: float
    total: float
```

---

## Mock-режим

При отсутствии SDK или ошибках API автоматически возвращаются тестовые данные:

```python
# Mock данные для get_ads_list()
[
    Order(
        order_id="ORD001",
        side="SELL",
        currency="RUB",
        crypto="USDT",
        price=95.50,
        amount=1000.0,
        status="active"
    ),
    # ...
]

# Mock данные для get_balance()
[
    Balance(currency="USDT", available=1500.0, locked=500.0, total=2000.0),
    Balance(currency="BTC", available=0.05, locked=0.0, total=0.05)
]
```

---

## SDK

```bash
uv pip install bybit-p2p
```

При отсутствии SDK — автоматический fallback в mock.

---

## Конфигурация

```python
# config.py
BYBIT_API_KEY = settings.BYBIT_API_KEY
BYBIT_API_SECRET = settings.BYBIT_API_SECRET
BYBIT_TESTNET = settings.BYBIT_TESTNET  # True по умолчанию
USE_MOCK_DATA = settings.USE_MOCK_DATA
```

---

## Безопасность

- Всегда используйте testnet для разработки
- Production API требует явного `BYBIT_TESTNET=False`
- Mock-режим безопасен для тестирования без реальных ключей
