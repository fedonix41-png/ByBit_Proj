# API Reference

## Обзор

Bybit P2P Automation предоставляет REST API и WebSocket для управления автоматизацией P2P-торговли. Все endpoints возвращают JSON ответы с полем `success` для индикации успешности операции.

## Базовый URL
```
http://127.0.0.1:8000
```

## Аутентификация
API не требует аутентификации для локального использования.

## Endpoints

### GET /
**Описание:** Главная страница веб-интерфейса
**Ответ:** HTML страница

### GET /api/ads
**Описание:** Получить список P2P объявлений
**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "price": "number",
      "amount": "number",
      "payment_methods": ["string"],
      "status": "string"
    }
  ]
}
```

### GET /api/chat/{order_id}
**Описание:** Получить историю сообщений для ордера
**Параметры:**
- `order_id` (path): ID ордера
**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "sender": "string",
      "message": "string",
      "timestamp": "string"
    }
  ]
}
```

### GET /api/balance
**Описание:** Получить баланс аккаунта
**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "currency": "string",
      "available": "number",
      "frozen": "number"
    }
  ]
}
```

### GET /api/payment_methods
**Описание:** Получить доступные способы оплаты
**Ответ:**
```json
{
  "success": true,
  "data": ["string"]
}
```

### GET /api/order/{order_id}
**Описание:** Получить детали ордера
**Параметры:**
- `order_id` (path): ID ордера
**Ответ:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "status": "string",
    "amount": "number",
    "price": "number",
    "payment_method": "string"
  }
}
```

### POST /api/order/{order_id}/cancel
**Описание:** Отменить ордер
**Параметры:**
- `order_id` (path): ID ордера
**Ответ:**
```json
{
  "success": true,
  "message": "Order cancelled"
}
```

### POST /api/order/{order_id}/confirm_payment
**Описание:** Подтвердить оплату
**Параметры:**
- `order_id` (path): ID ордера
**Ответ:**
```json
{
  "success": true,
  "message": "Payment confirmed"
}
```

### GET /api/trade_history
**Описание:** Получить историю торгов
**Ответ:**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "timestamp": "string",
      "amount": "number",
      "status": "string"
    }
  ]
}
```

### POST /api/start_monitor
**Описание:** Запустить мониторинг ордера
**Тело запроса:**
```json
{
  "order_id": "string"
}
```
**Ответ:**
```json
{
  "success": true,
  "run_id": "string",
  "order_id": "string"
}
```

### POST /api/approve/{run_id}
**Описание:** Подтвердить или отклонить действие
**Параметры:**
- `run_id` (path): ID запуска
**Тело запроса:**
```json
{
  "approved": true,
  "user_input": "string (optional)"
}
```
**Ответ:**
```json
{
  "success": true,
  "run_id": "string",
  "approved": true
}
```

### GET /api/runs
**Описание:** Получить все активные запуски
**Ответ:**
```json
{
  "success": true,
  "data": {
    "run_id": {
      "order_id": "string",
      "status": "string",
      "state": {}
    }
  }
}
```

### GET /api/run/{run_id}
**Описание:** Получить детали конкретного запуска
**Параметры:**
- `run_id` (path): ID запуска
**Ответ:**
```json
{
  "success": true,
  "data": {
    "order_id": "string",
    "status": "string",
    "state": {}
  }
}
```

## WebSocket

### /ws
**Описание:** WebSocket endpoint для real-time обновлений

**Входящие сообщения:**
- Клиент может отправлять текстовые сообщения для логов

**Исходящие сообщения:**
```json
{
  "type": "monitor_started|state_update|monitor_completed|approval_submitted|error",
  "run_id": "string",
  "order_id": "string (optional)",
  "node": "string (optional)",
  "state": {} (optional),
  "approved": boolean (optional),
  "error": "string (optional)"
}
```

## Коды ошибок

- `400` - Неверный запрос
- `404` - Ресурс не найден
- `500` - Внутренняя ошибка сервера

## Примеры использования

### Python
```python
import requests

# Получить объявления
response = requests.get("http://127.0.0.1:8000/api/ads")
ads = response.json()

# Запустить мониторинг
response = requests.post("http://127.0.0.1:8000/api/start_monitor",
                        json={"order_id": "12345"})
```

### JavaScript (WebSocket)
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```