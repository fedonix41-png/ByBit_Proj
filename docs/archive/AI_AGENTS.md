# AI Агенты

## Обзор

Система использует модульную архитектуру AI-агентов для анализа сообщений, генерации ответов, распознавания платежей и оценки рисков. Все агенты поддерживают мульти-провайдер конфигурацию с fallback логикой.

## Архитектура

### BaseAIAgent
Базовый класс для всех AI-агентов с унифицированным интерфейсом.

#### Поддерживаемые провайдеры
- **OpenAI**: gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo
- **Anthropic**: claude-3-sonnet, claude-3-haiku, claude-2
- **Groq**: mixtral-8x7b, llama2-70b
- **Together AI**: mixtral, llama-2
- **Mistral**: mistral-large, mistral-medium
- **Local**: Ollama (llama3, codellama, mistral)

#### Конфигурация
```python
# В .env файле
AI_PROVIDER=openai  # или anthropic, groq, together, mistral, local
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
# etc.
```

#### Fallback логика
```python
# Автоматическое переключение при ошибках
try:
    result = self.openai_client.chat.completions.create(...)
except Exception:
    try:
        result = self.anthropic_client.messages.create(...)
    except Exception:
        result = self.local_llm.generate(...)
```

## Агенты

### IntentClassifier
**Назначение**: Классификация намерений клиентов из текстовых сообщений.

#### Входные данные
- Текст сообщения
- История чата (опционально)
- Контекст ордера

#### Выходные данные
```json
{
  "intent": "ready_to_pay",
  "confidence": 0.95,
  "entities": {
    "amount": "10000",
    "currency": "RUB"
  }
}
```

#### Поддерживаемые intents
- `greeting` - Приветствие
- `ready_to_pay` - Готов оплатить
- `payment_sent` - Оплата отправлена
- `cancel` - Отмена сделки
- `complaint` - Жалоба
- `question` - Вопрос
- `other` - Другое

#### Примеры
```
Вход: "Здравствуйте, хочу купить 0.001 BTC за 50000 RUB"
Выход: {"intent": "ready_to_pay", "confidence": 0.92}

Вход: "Оплатил, вот скриншот"
Выход: {"intent": "payment_sent", "confidence": 0.88}
```

### ResponseGenerator
**Назначение**: Генерация контекстных ответов на основе классифицированного намерения.

#### Входные данные
- Intent от IntentClassifier
- Детали ордера
- История переписки
- Контекст сделки

#### Выходные данные
```json
{
  "response": "Здравствуйте! Для оплаты отправьте 10000 RUB на карту XXXX-XXXX-XXXX-XXXX",
  "explanation": "Стандартный ответ для готовности к оплате с реквизитами",
  "urgency": "normal"
}
```

#### Типы ответов
- **Инструкции**: Как оплатить, куда отправить средства
- **Подтверждения**: Подтверждение получения платежа
- **Разъяснения**: Ответы на вопросы
- **Отказы**: Безопасный отказ от рискованных сделок

### PaymentParser
**Назначение**: OCR-анализ скриншотов платежных подтверждений.

#### Входные данные
- Фото/скриншот платежа
- Ожидаемая сумма и валюта (из ордера)

#### Выходные данные
```json
{
  "amount": 10000.0,
  "currency": "RUB",
  "card_number": "1234567890123456",
  "timestamp": "2024-01-15T14:30:00",
  "confidence": 0.89,
  "raw_text": "Оплата на сумму 10000 рублей..."
}
```

#### OCR возможности
- Распознавание суммы платежа
- Извлечение номера карты/кошелька
- Определение времени транзакции
- Валидация формата данных

#### Интеграция
```python
# Использует pytesseract + PIL
import pytesseract
from PIL import Image

text = pytesseract.image_to_string(image)
# AI анализ текста для извлечения данных
```

### FraudAnalyzer
**Назначение**: Оценка рисков мошенничества и подозрительной активности.

#### Входные данные
- Данные платежа от PaymentParser
- Детали ордера
- История контрагента
- Геолокация (если доступна)

#### Выходные данные
```json
{
  "risk_score": 0.15,
  "risk_level": "low",
  "flags": ["amount_match", "time_reasonable"],
  "recommendation": "approve",
  "explanation": "Все проверки пройдены успешно"
}
```

#### Факторы риска
- **Сумма**: Несоответствие заявленной сумме
- **Время**: Необычное время транзакции
- **Карта**: Известные мошеннические карты
- **Поведение**: Подозрительные паттерны
- **История**: Предыдущие инциденты

#### Правило-based + AI
```python
# Rule-based проверки
if payment_amount != order_amount:
    risk_score += 0.3

# AI анализ паттернов
ai_risk = await self.analyze_pattern(payment_data)
risk_score += ai_risk
```

## Метрики и мониторинг

### AI Interaction tracking
Каждый вызов AI сохраняется в базе данных:

```sql
CREATE TABLE ai_interactions (
    id SERIAL PRIMARY KEY,
    agent_type VARCHAR(50),  -- intent/response/ocr/fraud
    provider VARCHAR(50),    -- openai/anthropic/etc
    tokens_used INTEGER,
    cost DECIMAL(10,4),
    latency_ms INTEGER,
    created_at TIMESTAMP
);
```

### Производительность
- **Latency**: Среднее время ответа AI
- **Cost**: Расходы на AI API
- **Accuracy**: Точность классификации (через human feedback)
- **Fallback rate**: Частота использования fallback провайдеров

### Мониторинг
```python
# Логирование каждого вызова
logger.info(f"AI call: {agent_type} via {provider} - {latency_ms}ms, ${cost}")

# Метрики для Prometheus
ai_requests_total.labels(agent=agent_type, provider=provider).inc()
ai_latency_seconds.labels(agent=agent_type).observe(latency)
```

## Конфигурация и оптимизация

### Настройки по умолчанию
```python
DEFAULT_CONFIG = {
    "temperature": 0.1,  # Детерминированные ответы
    "max_tokens": 1000,
    "timeout": 30,
    "retries": 3
}
```

### Cost optimization
- **Token counting**: Отслеживание использования токенов
- **Model selection**: Автоматический выбор оптимальной модели
- **Caching**: Кэширование частых запросов
- **Batch processing**: Группировка мелких запросов

### Reliability
- **Circuit breaker**: Отключение проблемных провайдеров
- **Rate limiting**: Соблюдение лимитов API
- **Error handling**: Graceful degradation
- **Health checks**: Проверка доступности провайдеров

## Тестирование

### Unit тесты
```python
def test_intent_classification():
    agent = IntentClassifier()
    result = agent.classify("Хочу купить BTC")
    assert result["intent"] == "ready_to_pay"
    assert result["confidence"] > 0.8

def test_fraud_detection():
    agent = FraudAnalyzer()
    risk = agent.analyze({"amount": 1000, "card": "4111111111111111"})
    assert risk["risk_score"] < 0.5
```

### Integration тесты
- Тестирование с реальными API ключами (testnet)
- Проверка fallback логики
- Нагрузочное тестирование

### Test data
- Набор тестовых сообщений с известными intents
- Скриншоты платежей для OCR тестирования
- Risk scenarios для fraud detection

## Безопасность

### API ключи
- Хранение в .env (не в коде)
- Валидация при запуске
- Отсутствие в логах

### Data privacy
- Не логировать чувствительные данные
- Анонимизация в метриках
- Соблюдение GDPR/privacy требований

### Rate limiting
- Защита от abuse AI API
- Очереди для burst нагрузки
- Плавное снижение при перегрузке

## Расширение

### Добавление нового провайдера
```python
class NewProvider:
    def __init__(self, api_key):
        self.client = NewAPIClient(api_key)
    
    async def generate(self, prompt):
        response = await self.client.generate(prompt)
        return response["text"]
```

### Новый агент
```python
class NewAgent(BaseAIAgent):
    async def process(self, input_data):
        prompt = self.build_prompt(input_data)
        response = await self.generate(prompt)
        return self.parse_response(response)
```

## Troubleshooting

### Проблема: Высокая latency
**Решение**: Переключиться на faster провайдер (Groq, Together)

### Проблема: API limits
**Решение**: Добавить rate limiting, использовать несколько ключей

### Проблема: Низкая accuracy
**Решение**: Fine-tuning промптов, добавить few-shot examples

### Проблема: High costs
**Решение**: Оптимизация промптов, кэширование, cheaper модели