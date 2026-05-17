# Bybit API Клиент

**Файл:** `bybit_client.py`

**Библиотека:** `bybit-p2p` (официальный SDK)

**Документация API:** https://bybit-exchange.github.io/docs/p2p/guide

---

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
# Список объявлений пользователя
ads = bybit_client.get_ads_list()  # List[Order]

# Публичные объявления
online_ads = bybit_client.get_online_ads(token="USDT", currency="RUB", side="1")  # List[Dict]

# Все ордера
orders = bybit_client.get_orders(page=1, size=20)  # List[Dict]

# Ожидающие ордера
pending = bybit_client.get_pending_orders(page=1, size=20)  # List[Dict]

# Детали ордера
details = bybit_client.get_order_details(order_id)  # Dict

# Сообщения чата
messages = bybit_client.get_chat_messages(order_id, size=30)  # List[ChatMessage]

# Баланс
balance = bybit_client.get_balance(account_type="FUND")  # List[Balance]

# Способы оплаты пользователя
methods = bybit_client.get_user_payment_types()  # List[Dict]

# История торгов
history = bybit_client.get_trade_history(limit=20)  # List[Dict]
```

### Действия

```python
# Отправить сообщение в чат
success = bybit_client.send_chat_message(order_id, "Текст сообщения")

# Загрузить файл в чат (скриншот оплаты)
success = bybit_client.upload_chat_file(order_id, "/path/to/file.jpg")

# Пометить как оплачено (для покупателя)
success = bybit_client.mark_as_paid(order_id, payment_type, payment_id)

# Отпустить крипту (для продавца после получения оплаты)
success = bybit_client.release_assets(order_id)

# Создать объявление
ad_id = bybit_client.create_ad(
    side="SELL",
    currency="RUB",
    crypto="USDT",
    price=95.5,
    min_amount=100,
    max_amount=10000,
    payment_methods=["payment_id"]
)

# Обновить объявление
success = bybit_client.update_ad(ad_id, price=96.0, min_amount=200)

# Получить детали объявления
details = bybit_client.get_ad_details(ad_id)

# Отменить объявление
success = bybit_client.cancel_order(ad_id)

# Получить информацию об аккаунте
account = bybit_client.get_account_information()

# Получить информацию о контрагенте
counterparty = bybit_client.get_counterparty_info(order_id)
```

### Устаревшие методы

```python
# confirm_payment() - использовать release_assets()
success = bybit_client.confirm_payment(order_id)  # deprecated

# appeal_order() - не реализовано в SDK
success = bybit_client.appeal_order(order_id, "Причина")  # returns False
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

**Библиотека:** `bybit-p2p` (официальный Python SDK от Bybit)

```bash
uv pip install bybit-p2p
```

**PyPI:** https://pypi.org/project/bybit-p2p/

**GitHub:** https://github.com/bybit-exchange/bybit_p2p

При отсутствии SDK — автоматический fallback в mock.

### Соответствие методов

| Метод клиента | Метод API | Эндпоинт |
|--------------|-----------|----------|
| `get_ads_list()` | `P2P.get_ads_list()` | `/v5/p2p/item/personal/list` |
| `get_online_ads()` | `P2P.get_online_ads()` | `/v5/p2p/item/online` |
| `get_ad_details()` | `P2P.get_ad_details()` | `/v5/p2p/item/info` |
| `create_ad()` | `P2P.post_new_ad()` | `/v5/p2p/item/create` |
| `update_ad()` | `P2P.update_ad()` | `/v5/p2p/item/update` |
| `cancel_order()` | `P2P.remove_ad()` | `/v5/p2p/item/delete` |
| `get_orders()` | `P2P.get_orders(page, size)` | `/v5/p2p/order/simplifyList` |
| `get_pending_orders()` | `P2P.get_pending_orders(page, size)` | `/v5/p2p/order/pending/simplifyList` |
| `get_order_details()` | `P2P.get_order_details(orderId)` | `/v5/p2p/order/info` |
| `get_chat_messages()` | `P2P.get_chat_messages(orderId, size)` | `/v5/p2p/order/message/listpage` |
| `send_chat_message()` | `P2P.send_chat_message(...)` | `/v5/p2p/order/message/send` |
| `upload_chat_file()` | `P2P.upload_chat_file(...)` | `/v5/p2p/order/message/upload` |
| `mark_as_paid()` | `P2P.mark_as_paid(orderId, ...)` | `/v5/p2p/order/pay` |
| `release_assets()` | `P2P.release_assets(orderId)` | `/v5/p2p/order/finish` |
| `get_balance()` | `P2P.get_current_balance(...)` | `/v5/asset/transfer/query-account-coins-balance` |
| `get_user_payment_types()` | `P2P.get_user_payment_types()` | `/v5/p2p/user/payment/list` |
| `get_account_information()` | `P2P.get_account_information()` | `/v5/p2p/user/personal/info` |
| `get_counterparty_info()` | `P2P.get_counterparty_info()` | `/v5/p2p/user/personal/info` |

### Форматы ответов

**P2P методы:** `ret_code`, `ret_msg`, `result` (snake_case)
**Wallet методы:** `retCode`, `retMsg`, `result` (camelCase)

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
