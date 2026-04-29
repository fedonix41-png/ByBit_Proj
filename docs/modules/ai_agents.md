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

### Методы

```python
class BaseAIAgent(ABC):
    def __init__(self, provider: str = None, model: str = None)
    
    async def generate(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: float = 0.3,
        json_mode: bool = False
    ) -> Dict[str, Any]
    
    @abstractmethod
    async def process(self, input_data: Dict) -> Dict
```

### Пример использования

```python
from app.ai_agents.base_agent import BaseAIAgent, AIProvider

class MyAgent(BaseAIAgent):
    async def process(self, input_data):
        result = await self.generate(
            system_prompt="Ты помощник.",
            user_prompt=input_data["message"],
            temperature=0.5
        )
        return {"response": result["content"]}
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

## FraudAnalyzer

**Файл:** `fraud_analyzer.py`

Анализ рисков мошенничества для P2P транзакций.

### Алгоритм

```
1. Rule-based проверки (40%)
   - Совпадение суммы
   - Формат карты
   - Тайминг (ордер vs платёж)
   - Совпадение валюты

2. AI-анализ (60%)
   - Красные/зелёные флаги
   - Контекст транзакции

3. Итоговая оценка = 0.4 * rules + 0.6 * ai
```

### API

```python
analyzer = FraudAnalyzer()

result = await analyzer.process({
    "payment_data": {
        "amount": 10000,
        "currency": "RUB",
        "card_number": "1234****5678"
    },
    "order_data": {
        "expected_amount": 10000,
        "currency": "RUB"
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
#     "checks": {"amount_match": True, ...},
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
