# Тестирование

## Структура тестов

```
tests/
├── conftest.py           # Общие fixtures
├── unit/
│   ├── ai_agents/        # Тесты AI-агентов
│   └── orchestrator/     # Тесты оркестратора
```

## Запуск тестов

```bash
# Установка зависимостей
pip install -e ".[dev]"

# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=app --cov-report=html

# Только unit-тесты
pytest tests/unit/

# Конкретный файл
pytest tests/unit/ai_agents/test_fraud_analyzer.py
```

## Fixtures

| Fixture | Описание |
|---------|----------|
| `event_loop` | Event loop для async тестов |
| `mock_settings` | Mock конфигурации |
| `mock_db_session` | Mock БД сессии |
| `mock_bybit_client` | Mock Bybit API клиента |
| `sample_order_data` | Пример данных ордера |
| `sample_payment_data` | Пример данных платежа |

## Smoke-тесты

### AI-агенты

| Файл | Тестирует |
|------|-----------|
| `test_base_agent.py` | Инициализация, mock провайдер |
| `test_intent_classifier.py` | Классификация намерений |
| `test_fraud_analyzer.py` | Правила проверки (BIN, карты, телефоны) |

### Оркестратор

| Файл | Тестирует |
|------|-----------|
| `test_state.py` | Структура состояния |
| `test_graph.py` | Узлы и переходы |

## Покрытие

```bash
pytest --cov=app --cov-report=term-missing
```

Отчёт сохраняется в `htmlcov/index.html`.

## CI/CD

CI/CD планируется в будущих версиях.
