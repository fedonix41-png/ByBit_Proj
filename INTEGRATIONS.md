# Внешние интеграции

## Обзор

Система интегрируется с несколькими внешними сервисами для обеспечения полного цикла P2P автоматизации. Текущий статус: Telegram и Bybit реализованы, Processing API в mock режиме.

## Telegram Bot API

### Настройка
```bash
# 1. Создать бота через @BotFather
# 2. Получить токен
# 3. Настроить .env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Реализованные функции

#### Команды бота
```python
# /start - Приветствие и инструкции
# /status - Текущий статус ордеров
# /cancel - Отмена активного мониторинга
# /help - Справка по командам
```

#### Обработка сообщений
- **Текст**: Передача в IntentClassifier для анализа
- **Фото**: Сохранение и передача в PaymentParser для OCR
- **Документы**: Поддержка дополнительных файлов

#### Отправка уведомлений
```python
await bot.send_message(
    chat_id=user_id,
    text="Сделка завершена успешно! ✅"
)
```

### Webhook vs Polling
- **Текущая реализация**: Long polling через `telegram.ext`
- **Рекомендация**: Webhook для production (более надежно)

### Безопасность
- **Token validation**: Проверка входящих обновлений
- **User isolation**: Разделение по chat_id
- **Rate limiting**: Защита от spam

## Bybit P2P API

### Режимы работы

#### Testnet API режим (рекомендуемый для разработки)
```python
# bybit_client.py - автоматически использует testnet API
USE_MOCK_DATA = False
BYBIT_TESTNET = True

# Реальные вызовы к Bybit Testnet API
def get_ads_list():
    # Вызывает настоящий Bybit P2P API
    response = self.client.get_my_ads()
    return [Order.from_api(item) for item in response['data']]
```

#### Mock режим (fallback)
```python
# Используется автоматически при проблемах с API
USE_MOCK_DATA = True

# Возвращает тестовые данные для отладки
def get_ads_list():
    return [
        Order(id="ORD001", price=50000, amount=0.001, ...),
        Order(id="ORD002", price=51000, amount=0.002, ...)
    ]
```

#### Real API режим (требуется реализация)
```python
# Требуется установка
pip install pybit

# Конфигурация
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret
BYBIT_TESTNET=True
```

### Реализованные методы

#### ✅ Полностью реализованы с Bybit Testnet API:

1. **get_ads_list()** - Получение списка объявлений
   ```python
   # Получение списка ваших P2P объявлений
   ads = await bybit_client.get_ads_list()
   # Возвращает: List[Order] - ваши реальные объявления на testnet
   ```

2. **get_chat_messages(order_id)** - История чата для ордера
   ```python
   # Получение сообщений из реального P2P чата
   messages = await bybit_client.get_chat_messages("ORD001")
   # Возвращает: List[ChatMessage] - настоящие сообщения
   ```

3. **send_chat_message(order_id, text)** - Отправка сообщения
   ```python
   # Отправка сообщения в реальный P2P чат
   success = await bybit_client.send_chat_message("ORD001", "Здравствуйте!")
   # Возвращает: bool - успех отправки
   ```

4. **get_balance()** - Баланс аккаунта
   ```python
   # Получение реального баланса testnet аккаунта
   balance = await bybit_client.get_balance()
   # Возвращает: List[Balance] - ваши testnet средства
   ```

5. **confirm_payment(order_id)** - Подтверждение оплаты
   ```python
   # Подтверждение платежа в реальной сделке
   success = await bybit_client.confirm_payment("ORD001")
   # Возвращает: bool - успех подтверждения
   ```

#### get_chat_messages(order_id)
```python
# История чата для ордера
messages = await bybit_client.get_chat_messages("ORD001")
# Возвращает: List[ChatMessage]
```

#### send_chat_message(order_id, text)
```python
# Отправка сообщения
success = await bybit_client.send_chat_message("ORD001", "Привет!")
# Возвращает: bool
```

#### get_balance()
```python
# Баланс аккаунта
balance = await bybit_client.get_balance()
# Возвращает: List[Balance]
```

#### confirm_payment(order_id)
```python
# Подтверждение оплаты
success = await bybit_client.confirm_payment("ORD001")
# Возвращает: bool
```

### Дополнительные методы

#### ✅ Реализованы в коде:
- `create_order()` - Создание нового объявления
- `cancel_order()` - Отмена ордера
- `get_order_details()` - Детали ордера
- `get_trade_history()` - История торгов
- `appeal_order()` - Создание апелляции

Все методы поддерживают как testnet API, так и mock fallback.

### Обработка ошибок
```python
try:
    result = await bybit_api_call()
except BybitAPIError as e:
    logger.error(f"Bybit API error: {e}")
    # Fallback to mock or retry
except RateLimitError:
    await asyncio.sleep(60)  # Rate limit cooldown
```

### Rate limiting
- **Bybit limits**: 10 req/sec для P2P API
- **Implementation**: Token bucket algorithm
- **Backoff**: Exponential backoff при rate limits

## Processing API

### Текущий статус: Mock режим
```python
# processing_client.py
USE_MOCK = True

class ProcessingClient:
    async def submit_transaction(self, data):
        # Mock implementation
        await asyncio.sleep(1)  # Simulate API call
        return {
            "transaction_id": f"txn_{random.randint(1000,9999)}",
            "status": "pending"
        }
```

### Требуемая интеграция
```python
# Real implementation needed
class ProcessingClient:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://processing-api.com/v1"

    async def submit_transaction(self, transaction_data):
        payload = {
            "amount": transaction_data["amount"],
            "currency": transaction_data["currency"],
            "payment_method": transaction_data["method"],
            "recipient": transaction_data["recipient"]
        }

        response = await self._post("/transactions", payload)
        return response.json()

    async def check_status(self, transaction_id):
        response = await self._get(f"/transactions/{transaction_id}")
        return response.json()

    async def handle_webhook(self, webhook_data):
        # Validate webhook signature
        # Update transaction status in DB
        pass
```

### Webhook обработка
```python
# webhook_handlers.py
@app.post("/webhooks/processing")
async def processing_webhook(request: Request):
    # Validate signature
    signature = request.headers.get("X-Signature")
    if not validate_signature(request.body, signature):
        raise HTTPException(status_code=401)

    # Parse webhook
    data = await request.json()

    # Update transaction status
    await update_transaction_status(data["transaction_id"], data["status"])

    return {"status": "ok"}
```

### Безопасность webhook
- **Signature validation**: HMAC-SHA256
- **IP whitelisting**: Разрешенные IP processing сервиса
- **Idempotency**: Защита от дублированных webhook
- **Timeout handling**: Graceful handling network issues

## Архитектура интеграций

### Клиентские классы
```python
# integrations/
├── __init__.py
├── telegram_bot.py      # Telegram Bot API
├── bybit_client.py      # Bybit P2P API
├── processing_client.py # Processing API
└── webhook_handlers.py  # Webhook endpoints
```

### Общий интерфейс
```python
class BaseAPIClient:
    def __init__(self, config: dict):
        self.config = config
        self.session = aiohttp.ClientSession()

    async def _get(self, endpoint: str) -> dict:
        async with self.session.get(f"{self.base_url}{endpoint}") as resp:
            return await resp.json()

    async def _post(self, endpoint: str, data: dict) -> dict:
        async with self.session.post(f"{self.base_url}{endpoint}", json=data) as resp:
            return await resp.json()

    async def close(self):
        await self.session.close()
```

### Конфигурация
```python
# config.py
INTEGRATIONS_CONFIG = {
    "telegram": {
        "token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "webhook_url": os.getenv("TELEGRAM_WEBHOOK_URL")
    },
    "bybit": {
        "api_key": os.getenv("BYBIT_API_KEY"),
        "api_secret": os.getenv("BYBIT_API_SECRET"),
        "testnet": os.getenv("BYBIT_TESTNET", "true").lower() == "true",
        "use_mock": os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    },
    "processing": {
        "api_key": os.getenv("PROCESSING_API_KEY"),
        "api_secret": os.getenv("PROCESSING_API_SECRET"),
        "webhook_secret": os.getenv("PROCESSING_WEBHOOK_SECRET"),
        "use_mock": os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    }
}
```

## Мониторинг интеграций

### Health checks
```python
# health.py
async def check_integrations():
    results = {}

    # Telegram
    try:
        await telegram_bot.get_me()
        results["telegram"] = "healthy"
    except Exception as e:
        results["telegram"] = f"unhealthy: {e}"

    # Bybit
    try:
        await bybit_client.get_balance()
        results["bybit"] = "healthy"
    except Exception as e:
        results["bybit"] = f"unhealthy: {e}"

    # Processing
    try:
        await processing_client.health_check()
        results["processing"] = "healthy"
    except Exception as e:
        results["processing"] = f"unhealthy: {e}"

    return results
```

### Метрики
```python
# Prometheus metrics
integration_requests_total = Counter(
    'integration_requests_total',
    'Total requests to external APIs',
    ['integration', 'method', 'status']
)

integration_request_duration = Histogram(
    'integration_request_duration_seconds',
    'Request duration to external APIs',
    ['integration', 'method']
)
```

### Alerting
- **Unhealthy integrations**: Автоматическое отключение
- **Rate limit hits**: Уведомление о превышении лимитов
- **Error spikes**: Мониторинг роста ошибок
- **Latency degradation**: Уведомление о замедлении

## Тестирование интеграций

### Unit тесты
```python
# test_integrations.py
@pytest.mark.asyncio
async def test_telegram_bot():
    bot = TelegramBot(config)
    await bot.start()

    # Test sending message
    result = await bot.send_message(chat_id=123, text="Test")
    assert result is True

    await bot.stop()

@pytest.mark.asyncio
async def test_bybit_mock():
    client = BybitClient({"use_mock": True})

    ads = await client.get_ads_list()
    assert len(ads) > 0
    assert ads[0].id.startswith("ORD")
```

### Integration тесты
```python
# test_integration.py
@pytest.mark.asyncio
async def test_full_flow():
    # Setup test order
    order_id = await create_test_order()

    # Test message sending
    success = await telegram_bot.send_message(order_id, "Test message")
    assert success

    # Test balance check
    balance = await bybit_client.get_balance()
    assert balance is not None
```

### Test environments
- **Mock mode**: Для unit и integration тестов
- **Testnet**: Для Bybit API тестирования
- **Staging**: Для end-to-end с реальными API

## Troubleshooting

### Telegram проблемы
```
Проблема: Bot не отвечает
Решение:
1. Проверить TELEGRAM_BOT_TOKEN
2. Проверить логи: docker-compose logs telegram_bot
3. Проверить webhook: curl https://api.telegram.org/bot<token>/getWebhookInfo
```

### Bybit проблемы
```
Проблема: API возвращает ошибку
Решение:
1. Проверить BYBIT_TESTNET=True
2. Проверить API ключи и IP binding
3. Проверить rate limits
4. Переключиться на mock: USE_MOCK_DATA=True
```

### Processing проблемы
```
Проблема: Webhook не приходит
Решение:
1. Проверить webhook URL в processing dashboard
2. Проверить webhook_secret
3. Проверить firewall (порт 443)
4. Проверить SSL certificate
```

## Migration plan

### Phase 1: Telegram + Bybit mock
- ✅ Telegram bot работает
- ✅ Bybit в mock режиме
- ✅ Processing mock

### Phase 2: Bybit real API
- [ ] Установить pybit
- [ ] Реализовать все методы
- [ ] Тестирование на testnet

### Phase 3: Processing real API
- [ ] Получить доступ к processing API
- [ ] Реализовать submit_transaction
- [ ] Настроить webhooks
- [ ] Тестирование с реальными транзакциями

### Phase 4: Production hardening
- [ ] Rate limiting
- [ ] Circuit breakers
- [ ] Comprehensive monitoring
- [ ] Backup и disaster recovery