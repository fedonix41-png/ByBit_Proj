# API и внешние сервисы

## REST API (FastAPI)

Базовый URL: `http://127.0.0.1:8000`

### Endpoints

#### Объявления и ордера

```
GET  /api/ads                    # Список объявлений
GET  /api/order/{order_id}       # Детали ордера
POST /api/order/{order_id}/cancel      # Отмена ордера
POST /api/order/{order_id}/confirm_payment  # Подтверждение платежа (для старых интеграций)
POST /api/order/{order_id}/mark_paid   # Отметить ордер оплаченным (buyer)
POST /api/order/{order_id}/release     # Отпустить криптовалюту (seller)
```

#### Чат

```
GET  /api/chat/{order_id}        # История чата
```

#### Баланс и история

```
GET  /api/balance                # Баланс кошелька
GET  /api/trade_history          # История торгов
GET  /api/payment_methods        # Способы оплаты
```

#### Мониторинг и подтверждения

```
POST /api/start_monitor          # Запуск мониторинга ордера
POST /api/approve/{run_id}       # Подтверждение/отклонение действия
GET  /api/runs                   # Все активные запуски
GET  /api/run/{run_id}           # Детали запуска
```

### WebSocket

```
/ws  — Real-time обновления состояния
```

**Типы сообщений:**
- `monitor_started` — мониторинг запущен
- `state_update` — обновление состояния
- `monitor_completed` — мониторинг завершён
- `approval_submitted` — подтверждение отправлено
- `error` — ошибка

### Примеры

**Python:**
```python
import requests

# Получить объявления
ads = requests.get("http://127.0.0.1:8000/api/ads").json()["data"]

# Запустить мониторинг
r = requests.post("http://127.0.0.1:8000/api/start_monitor",
                 json={"order_id": "ORD123"})
run_id = r.json()["run_id"]

# Подтвердить
requests.post(f"http://127.0.0.1:8000/api/approve/{run_id}",
             json={"approved": True})
```

**cURL:**
```bash
# Баланс
curl http://127.0.0.1:8000/api/balance

# Запустить мониторинг
curl -X POST http://127.0.0.1:8000/api/start_monitor \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD123"}'
```

---

## Bybit P2P API

**Базовые URL:**
- Testnet: `https://api-testnet.bybit.com`
- Production: `https://api.bybit.com`

**Аутентификация:** API Key + API Secret (HMAC)

Полное описание методов клиента и SDK `bybit-p2p` находится в [docs/modules/bybit_client.md](modules/bybit_client.md).

---

## AI Providers

Детальная настройка переменных окружения для AI-провайдеров (OpenAI, Anthropic, Groq, Together, Mistral, Local, OpenRouter) перенесена в [docs/setup.md](setup.md#ai-провайдеры).

Использование провайдеров в коде описано в [docs/modules/ai_agents.md](modules/ai_agents.md).

---

## Telegram Bot API

**Режим:** Long polling

### Используемые методы

| Метод | Назначение |
|-------|------------|
| `sendMessage` | Отправка текста |
| `sendPhoto` | Отправка фото |
| `sendVoice` | Отправка голосового |
| `editMessageText` | Редактирование сообщения |
| `answerCallbackQuery` | Ответ на inline-кнопку |

### Webhook vs Polling

Текущая реализация использует polling (`run_polling()`).
Для webhook потребуется отдельная настройка.

---

## Processing API (mock)

**Статус:** Заглушка, реальный API не подключён.

**Методы:**
- `submit_transaction()` — отправка транзакции
- `check_status()` — проверка статуса
- `cancel_transaction()` — отмена
- `handle_webhook()` — обработка вебхуков
