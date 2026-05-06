# AI-агенты

**Расположение:** `app/ai_agents/`

## BaseAIAgent

**Файл:** `base_agent.py`

Базовый класс для всех AI-агентов с поддержкой множества провайдеров.

### Провайдеры

| Провайдер | Enum | API ключ | Модель (default) |
|-----------|------|----------|------------------|
| OpenAI | `OPENAI` | `OPENAI_API_KEY` | `gpt-4-turbo-preview` |
| Anthropic | `ANTHROPIC` | `ANTHROPIC_API_KEY` | `claude-3-sonnet-20240229` |
| Groq | `GROQ` | `GROQ_API_KEY` | `mixtral-8x7b-32768` |
| Together | `TOGETHER` | `TOGETHER_API_KEY` | `mistralai/Mixtral-8x7B-Instruct-v0.1` |
| Mistral | `MISTRAL` | `MISTRAL_API_KEY` | `mistral-large-latest` |
| Local | `LOCAL` | `LOCAL_LLM_URL` | `llama-3-8b` |
| OpenRouter | `OPENROUTER` | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` |
| Mock | `MOCK` | - | `mock-ai-model` |

### Параметры конструктора

```python
class BaseAIAgent(ABC):
    def __init__(
        self,
        provider: str = None,
        model: str = None,
        log_to_db: bool = True,           # Логировать в БД
        agent_type: Optional[str] = None  # Тип агента для логов
    )
```

### Методы

```python
async def generate(
    self, 
    system_prompt: str, 
    user_prompt: str,
    temperature: float = 0.3,
    json_mode: bool = False,
    order_id: Optional[int] = None      # ID ордера для логирования
) -> Dict[str, Any]
```

### Возвращаемые данные generate()

```python
{
    "content": "...",      # Текст ответа
    "tokens": 150,         # Использовано токенов
    "model": "gpt-4o",     # Модель
    "latency_ms": 850      # Время ответа в мс
}
```

### Пример использования

```python
from app.ai_agents.base_agent import BaseAIAgent, AIProvider

class MyAgent(BaseAIAgent):
    def __init__(self):
        super().__init__(agent_type="my_agent")  # Тип для логов
    
    async def process(self, input_data):
        result = await self.generate(
            system_prompt="Ты помощник.",
            user_prompt=input_data["message"],
            temperature=0.5,
            order_id=input_data.get("order_id")  # Для связи с ордером
        )
        return {"response": result["content"], "latency_ms": result["latency_ms"]}
```

---

## OpenRouterAdapter

**Файл:** `openrouter_adapter.py`

Отдельный адаптер для OpenRouter.ai с OpenAI-совместимым интерфейсом.

### Особенности

- Использует `langchain_openai.ChatOpenAI` с `base_url="https://openrouter.ai/api/v1"`
- Асинхронный метод `generate()` для неблокирующих вызовов
- Обработка ошибок с понятными сообщениями для пользователя

### API

```python
from app.ai_agents.openrouter_adapter import OpenRouterClient

# Инициализация (читает OPENROUTER_API_KEY и OPENROUTER_MODEL из env)
client = OpenRouterClient()

# Асинхронная генерация
response = await client.generate(
    prompt="Какие реквизиты для оплаты?",
    system="Ты помощник P2P торговли."
)

# Проверка конфигурации
if client.is_configured:
    response = await client.generate("Привет")
else:
    print("API-ключ не настроен")
```

### Переменные окружения

| Переменная | Default | Описание |
|------------|---------|----------|
| `OPENROUTER_API_KEY` | - | API ключ OpenRouter |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Модель для использования |

### Обработка ошибок

| Ошибка | Сообщение пользователю |
|--------|----------------------|
| `AuthenticationError` | "Неверный API-ключ OpenRouter" |
| `APIConnectionError` | "Сервис временно недоступен" |
| Нет ключа | "API-ключ OpenRouter не настроен" |

---

## IntentClassifier

**Файл:** `intent_classifier.py`

Классификация намерений пользователя в P2P контексте.

### Поддерживаемые намерения

| Intent | Описание |
|--------|----------|
| `greeting` | Приветствие |
| `ready_to_pay` | Готов оплатить |
| `payment_sent` | Платёж отправлен |
| `request_details` | Запрос реквизитов |
| `complaint` | Жалоба |
| `question` | Вопрос |
| `cancel` | Отмена сделки |
| `confirm_receipt` | Подтверждение получения |
| `unknown` | Неизвестно |

### API

```python
classifier = IntentClassifier()

result = await classifier.process({
    "message": "Готов перевести 10000 рублей",
    "context": {
        "order_amount": 10000,
        "currency": "RUB",
        "order_status": "pending"
    }
})

# Результат:
# {
#     "intent": "ready_to_pay",
#     "confidence": 0.95,
#     "entities": {"amount": 10000, "currency": "RUB"}
# }
```

---

## IntentRouter

**Файл:** `intent_router.py`

Определение типа ответа и маршрутизация в узел графа.

### Типы ответов

| Тип | Описание | Узел |
|-----|----------|------|
| `text` | Текстовый ответ | `generate_response` |
| `action` | Выполнение действия | `parse_payment`, `handle_cancel` |
| `info` | Информационный ответ | `generate_response` |

### API

```python
router = IntentRouter()

result = await router.process({
    "message": "Отправил платёж",
    "intent": "payment_sent",
    "context": {"has_image": True}
})

# Результат:
# {
#     "response_type": "action",
#     "routing": {"node": "parse_payment", "requires_approval": True},
#     "confidence": 0.9
# }
```

---

## ResponseGenerator

**Файл:** `response_generator.py`

Генерация профессиональных ответов клиентам.

### Тоны

| Тон | Когда используется |
|-----|-------------------|
| `friendly` | Приветствия |
| `professional` | Инструкции |
| `empathetic` | Жалобы |

### API

```python
generator = ResponseGenerator()

result = await generator.process({
    "intent": "ready_to_pay",
    "message": "Готов оплатить",
    "context": {
        "order_id": "ORD123",
        "order_amount": 10000,
        "currency": "RUB",
        "payment_methods": ["Сбербанк", "Тинькофф"]
    }
})

# Результат:
# {
#     "response": "Отлично! Отправьте реквизиты...",
#     "tone": "professional"
# }
```

---

## PaymentParser

**Файл:** `payment_parser.py`

OCR + AI парсинг скриншотов платёжных документов.

### Пайплайн

```
Изображение → Tesseract OCR → AI парсинг → Структурированные данные
```

### API

```python
parser = PaymentParser()

result = await parser.process({
    "image_path": "/path/to/screenshot.jpg",
    "expected_amount": 10000,
    "expected_currency": "RUB"
})

# Результат:
# {
#     "amount": 10000.0,
#     "currency": "RUB",
#     "card_number": "1234****5678",
#     "timestamp": "2024-01-15 14:30",
#     "bank": "Сбербанк",
#     "confidence": 0.9
# }
```

### Зависимости

- `pytesseract`
- `Pillow`
- Tesseract OCR с русским языком (`tesseract-ocr-rus`)

---

## AILogger

**Файл:** `ai_logger.py`

Логирование AI-взаимодействий в базу данных с расчётом стоимости.

### Таблица цен (PRICING_TABLE)

| Провайдер | Модель | Input ($/1K) | Output ($/1K) |
|-----------|--------|--------------|---------------|
| openai | gpt-4o | $0.0025 | $0.01 |
| openai | gpt-4o-mini | $0.00015 | $0.0006 |
| openai | gpt-4-turbo | $0.01 | $0.03 |
| anthropic | claude-3-opus | $0.015 | $0.075 |
| anthropic | claude-3-sonnet | $0.003 | $0.015 |
| anthropic | claude-3-haiku | $0.00025 | $0.00125 |
| groq | mixtral-8x7b | $0.00027 | $0.00027 |
| mistral | mistral-large | $0.004 | $0.012 |
| openrouter | default | $0.00015 | $0.00015 |
| local/mock | default | $0.00 | $0.00 |

### API

```python
from app.ai_agents.ai_logger import get_ai_logger

logger = get_ai_logger()

# Расчёт стоимости
cost = logger.calculate_cost(
    provider="openai",
    model="gpt-4o",
    input_tokens=500,
    output_tokens=200
)  # => 0.00325

# Логирование взаимодействия
await logger.log_interaction(
    agent_type="FraudAnalyzer",
    provider="openai",
    model="gpt-4o-mini",
    input_data={"prompt": "..."},
    output_data={"response": "..."},
    tokens_used=150,
    latency_ms=850,
    order_id=123
)
```

### Singleton паттерн

```python
# Используйте get_ai_logger() вместо прямого создания
_ailogger_instance: Optional[AILogger] = None

def get_ai_logger() -> AILogger:
    global _ailogger_instance
    if _ailogger_instance is None:
        _ailogger_instance = AILogger()
    return _ailogger_instance
```

---

## FraudAnalyzer

**Файл:** `fraud_analyzer.py`

Анализ рисков мошенничества для P2P транзакций.

### Rule-based проверки

| Проверка | Флаги | Описание |
|----------|-------|----------|
| `amount_match` | `amount_mismatch`, `amount_slight_mismatch` | Совпадение суммы |
| `card_format_valid` | `card_format_invalid`, `card_format_unusual` | Формат карты |
| `timing_reasonable` | `payment_before_order`, `payment_too_fast`, `payment_too_late` | Тайминг платежа |
| `currency_match` | `currency_mismatch` | Совпадение валюты |
| `bin_bank_match` | `bin_bank_mismatch`, `bin_unknown` | BIN-код ↔ банк |
| `recipient_match` | `card_number_mismatch`, `bank_mismatch`, `phone_mismatch` | Реквизиты получателя |
| `duplicate_check` | `duplicate_screenshot` | Дубликат скриншота (SHA-256) |
| `metadata_check` | `photo_date_future`, `photo_too_old` | EXIF метаданные |

### BIN-коды (19 банков)

Словарь `BIN_CODES` содержит первые 4 цифры карт для идентификации банков:

```python
BIN_CODES = {
    '4276': 'Сбербанк', '5469': 'Сбербанк', '4279': 'Сбербанк', '2200': 'Сбербанк',
    '2202': 'Тинькофф', '2204': 'Тинькофф', '5536': 'Тинькофф', '5537': 'Тинькофф',
    '2205': 'Альфа-Банк', '4154': 'Альфа-Банк', '4230': 'Альфа-Банк', '5213': 'Альфа-Банк',
    '2203': 'ВТБ', '4272': 'ВТБ', '5278': 'ВТБ',
    '4341': 'Райффайзен', '4345': 'Райффайзен', '5264': 'Райффайзен',
}
```

### Нормализация банков

`BANK_ALIASES` для приведения названий к единому формату:

```python
BANK_ALIASES = {
    'сбер': 'Сбербанк', 'sberbank': 'Сбербанк',
    'тинькофф': 'Тинькофф', 'tinkoff': 'Тинькофф',
    'альфа': 'Альфа-Банк', 'alfa': 'Альфа-Банк',
    'втб': 'ВТБ', 'vtb': 'ВТБ',
    'райффайзен': 'Райффайзен', 'raiffeisen': 'Райффайзен',
}
```

### Алгоритм

```
1. Rule-based проверки (40%)
   - amount_match, card_format_valid
   - timing_reasonable, currency_match
   - bin_bank_match, recipient_match
   - duplicate_check, metadata_check

2. AI-анализ (60%)
   - Красные/зелёные флаги
   - Контекст транзакции

3. Итоговая оценка = 0.4 * rules + 0.6 * ai
```

### API

```python
analyzer = FraudAnalyzer()
analyzer.set_db_session(db_session)  # Для duplicate_check

result = await analyzer.process({
    "payment_data": {
        "amount": 10000,
        "currency": "RUB",
        "card_number": "4276****5678",
        "bank": "Сбербанк"
    },
    "order_data": {
        "expected_amount": 10000,
        "currency": "RUB",
        "expected_bank": "Сбербанк",
        "expected_card_number": "4276****5678"
    },
    "screenshot_path": "/path/to/screenshot.png",
    "parsed_screenshot": {
        "card_number": "4276****5678",
        "amount": 10000
    },
    "counterparty_history": {
        "total_trades": 5,
        "disputes": 0
    }
})

# Результат:
# {
#     "risk_score": 0.15,
#     "risk_level": "low",  # low/medium/high
#     "flags": [],
#     "checks": {
#         "amount_match": {"passed": true, "score": 1.0, "flags": [], "details": "..."},
#         "bin_bank_match": {"passed": true, "score": 1.0, "flags": [], "details": "Bank matches: Сбербанк"},
#         "duplicate_check": {"passed": true, "score": 1.0, "flags": [], "details": "Screenshot is unique"},
#         ...
#     },
#     "recommendation": "approve"  # approve/manual_review/reject
# }
```

---

## Использование в Telegram-боте

### OpenRouter для AI-диалога

Бот использует `OpenRouterClient` для обработки вопросов пользователей:

```python
from app.ai_agents.openrouter_adapter import OpenRouterClient

client = OpenRouterClient()
response = await client.generate(
    prompt="Как проверить контрагента?",
    system="Ты - помощник для P2P торговли..."
)
```

### Vision через OpenRouter

Для анализа изображений (скриншоты платежей, проверка мошенничества) бот использует OpenRouter с vision-моделью:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Анализируй изображение..."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    }]
)
```

### FraudAnalyzer с OpenRouter

`FraudAnalyzer` может использовать OpenRouter как провайдер:

```python
analyzer = FraudAnalyzer(provider="openrouter")
result = await analyzer.process(payment_data)
```
