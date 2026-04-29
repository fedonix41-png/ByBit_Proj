# API и внешние сервисы

## REST API (FastAPI)

Базовый URL: `http://127.0.0.1:8000`

### Endpoints

#### Объявления и ордера

```
GET  /api/ads                    # Список объявлений
GET  /api/order/{order_id}       # Детали ордера
POST /api/order/{order_id}/cancel      # Отмена ордера
POST /api/order/{order_id}/confirm_payment  # Подтверждение платежа
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

### Используемые эндпоинты

| Эндпоинт | Метод | Назначение |
|----------|-------|------------|
| `/v5/p2p/item/query` | POST | Список объявлений |
| `/v5/p2p/order/info` | POST | Информация об ордере |
| `/v5/p2p/order/message/query` | POST | История чата |
| `/v5/p2p/order/message/send` | POST | Отправка сообщения |
| `/v5/p2p/order/pay` | POST | Подтверждение платежа |
| `/v5/p2p/order/cancel` | POST | Отмена ордера |
| `/v5/account/wallet-balance` | GET | Баланс |

### SDK

```bash
uv pip install bybit-p2p
```

### Fallback

При отсутствии SDK или ошибках API — автоматический переход в mock-режим.

---

## AI Providers

### OpenAI

**Используется для:**
- Текст: `gpt-4o-mini` (IntentClassifier, ResponseGenerator)
- Аудио: `whisper-1` (транскрипция голосовых)
- Изображения: `gpt-4o` (Vision для скриншотов)

**Переменные:**
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
- `OPENAI_AUDIO_MODEL` (default: `whisper-1`)
- `OPENAI_VISION_MODEL` (default: `gpt-4o`)

### Другие провайдеры

| Провайдер | Переменная | Модель (default) |
|-----------|------------|------------------|
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-sonnet-20240229` |
| Groq | `GROQ_API_KEY` | `mixtral-8x7b-32768` |
| Together | `TOGETHER_API_KEY` | `mistralai/Mixtral-8x7B-Instruct-v0.1` |
| Mistral | `MISTRAL_API_KEY` | `mistral-large-latest` |
| Local (Ollama) | `LOCAL_LLM_URL` | `llama-3-8b` |

### OpenRouter.ai (планируется)

**Статус:** Архитектура подготовлена, реализация pending.

**Требуемые изменения:**
1. Добавить `OPENROUTER_API_KEY` в config
2. Реализовать `_generate_openrouter()` в BaseAIAgent
3. Добавить `AIProvider.OPENROUTER`

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
