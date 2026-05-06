# Обработчик сообщений

**Расположение:** `app/infrastructure/handlers/`

---

## MessageProcessor

**Файл:** `message_processor.py`

Условный обработчик сообщений с правилами безопасности, rate limiting и ML-детекцией.

### Возможности

| Функция | Описание |
|---------|----------|
| Blacklist check | Проверка по БД (слова, паттерны, пользователи) |
| Rate limiting | Ограничение запросов (Redis + in-memory fallback) |
| Spam detection | ML-детекция через OpenRouter |
| Sensitive content | Детекция кредитных карт, паролей, email |
| Business rules | Проверка нарушений, банов |
| Webhook notifications | Уведомления о нарушениях |
| A/B testing | Тестирование разных правил |

### Конфигурация

| Переменная | Default | Описание |
|------------|---------|----------|
| `REDIS_URL` | `redis://localhost:6379/0` | URL Redis |
| `REDIS_ENABLED` | `true` | Включить Redis |
| `MESSAGE_MAX_LENGTH` | `2000` | Макс. длина сообщения |
| `RATE_LIMIT_WINDOW` | `60` | Окно rate limit (сек) |
| `RATE_LIMIT_MAX` | `15` | Макс. запросов в окне |
| `MAX_VIOLATIONS_BEFORE_BAN` | `5` | Нарушений до бана |
| `WEBHOOK_URL` | - | URL для webhook уведомлений |

### API

```python
from app.infrastructure.handlers import message_processor

# Инициализация
await message_processor.initialize()

# Обработка сообщения
result = await message_processor.process_message(
    user_id="123456",
    message="Привет!",
    username="user",
    user_data={"banned": False}
)

if result.should_process:
    # Сообщение прошло проверки
    print(result.metadata)
else:
    # Сообщение заблокировано
    print(result.response)  # Причина блокировки
```

### ProcessingResult

```python
@dataclass
class ProcessingResult:
    should_process: bool      # Прошло ли сообщение
    response: Optional[str]   # Ответ если заблокировано
    metadata: Dict[str, Any]  # Метаданные обработки
    log_level: str            # Уровень логирования
    variant: Optional[str]    # A/B вариант
```

---

## SpamDetector

**Файл:** `spam_detector.py`

ML-детекция спама через OpenRouter.

### API

```python
from app.infrastructure.handlers import spam_detector

result = await spam_detector.analyze("Сообщение")

print(result.is_spam)      # True/False
print(result.confidence)   # 0.0-1.0
print(result.categories)   # ["phishing", "scam"]
print(result.explanation)  # Объяснение
```

### Категории детекции

- `phishing` — попытка получить личные данные
- `scam` — мошеннические схемы
- `spam` — нежелательная реклама
- `manipulation` — давление на пользователя
- `impersonation` — выдача себя за другого
- `off_topic` — не связано с P2P
- `legitimate` — нормальное сообщение

---

## Модели БД

### BlacklistEntry

Чёрные списки (слова, паттерны, пользователи).

| Поле | Тип | Описание |
|------|-----|----------|
| `entry_type` | String | word/pattern/user_id/regex |
| `value` | String | Значение |
| `severity` | String | low/medium/high/critical |
| `is_active` | Boolean | Активна ли запись |
| `expires_at` | DateTime | Срок действия |

### ViolationHistory

История нарушений пользователей.

| Поле | Тип | Описание |
|------|-----|----------|
| `user_id` | String | ID пользователя |
| `violation_type` | String | Тип нарушения |
| `severity` | String | Критичность |
| `action_taken` | String | warn/blocked/ignored |

### ABTestConfig

Конфигурация A/B тестов.

| Поле | Тип | Описание |
|------|-----|----------|
| `test_name` | String | Название теста |
| `variant_a` | JSON | Конфиг варианта A |
| `variant_b` | JSON | Конфиг варианта B |
| `traffic_split` | Float | Доля трафика (0.0-1.0) |

### WebhookEvent

Webhook-события для уведомлений.

| Поле | Тип | Описание |
|------|-----|----------|
| `event_type` | String | Тип события |
| `payload` | JSON | Данные события |
| `status` | String | pending/sent/failed |
