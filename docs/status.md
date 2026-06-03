# Текущее состояние

Последнее обновление: 2026-05-17

## ✅ Реализовано

### Ядро

| Компонент | Файл | Статус |
|-----------|------|--------|
| LangGraph оркестратор | `app/orchestrator/` | ✅ Работает |
| AI-агенты | `app/ai_agents/` | ✅ Работает |
| Telegram-бот | `app/infrastructure/interface/` | ✅ Работает |
| Bybit-клиент | `bybit_client.py` | ✅ Работает |
| FastAPI сервер | `server.py` | ✅ Работает |
| PostgreSQL + Alembic | `app/database/` | ✅ Работает |
| Docker Compose | `docker-compose.yml` | ✅ Работает |
| Redis | `docker-compose.yml` | ✅ Работает |

### Веб-интерфейс (REST API)

Все эндпоинты реализованы (статус: ✅). 
Подробный список и описание см. в [api.md](api.md#rest-api-fastapi).

### Веб-интерфейс (UI)

| Компонент | Статус |
|-----------|--------|
| Табовая навигация (5 табов) | ✅ |
| Таб «Объявления» | ✅ CRUD + поиск публичных |
| Таб «Ордера» | ✅ Списки + действия |
| Таб «Чат» | ✅ Сообщения + отправка |
| Таб «Аккаунт» | ✅ Баланс, методы, контрагент |
| Таб «Мониторинг» | ✅ Запуск + approval UI |
| JWT авторизация | ✅ |
| WebSocket real-time | ✅ |
| Toast уведомления | ✅ |
| Модальные окна | ✅ |

### Bybit Client методы

Все базовые методы реализованы (статус: ✅).
Детальное описание методов см. в [modules/bybit_client.md](modules/bybit_client.md).

### AI-агенты

| Агент | Статус | Примечание |
|-------|--------|------------|
| `IntentClassifier` | ✅ | 9 типов намерений |
| `IntentRouter` | ✅ | С rule-based fallback |
| `ResponseGenerator` | ✅ | Тоновая адаптация |
| `PaymentParser` | ⚠️ | OCR работает, качество не верифицировано |
| `FraudAnalyzer` | ✅ | 8 правил, BIN-коды 19 банков |
| `AILogger` | ✅ | Логирование в БД, расчёт стоимости |

### FraudAnalyzer: Rule-based проверки

Все проверки реализованы (статус: ✅).
Список правил см. в [modules/ai_agents.md](modules/ai_agents.md#fraudanalyzer).

### AILogger: Возможности

Функционал логирования реализован (статус: ✅).
Архитектуру логирования см. в [modules/ai_agents.md](modules/ai_agents.md#ailogger).

### Telegram-бот

| Функция | Статус |
|---------|--------|
| Текстовые сообщения | ✅ |
| Голосовые (Whisper) | ✅ Требуется OPENAI_API_KEY |
| Фото (Vision) | ✅ OpenRouter или OpenAI |
| InlineKeyboard меню | ✅ Переработано |
| AI-диалог (/ask) | ✅ Через OpenRouter |
| Анализ P2P | ✅ Подменю |
| Проверка мошенничества | ✅ Подменю + Vision |
| Настройки | ✅ AI-провайдер, язык, баланс |

### Провайдеры AI

Все заявленные провайдеры (OpenAI, Anthropic, Groq, Together, Mistral, Local, Mock, OpenRouter) интегрированы (статус: ✅).
Детали настройки см. в [api.md](api.md#ai-providers).

---

## ⚠️ Частично реализовано

| Компонент | Проблема | Решение |
|-----------|----------|---------|
| PaymentParser | Качество OCR не верифицировано | Тесты на реальных скриншотах |
| Processing Client | Mock-заглушка | Интеграция с реальным API |

---

### Тестирование

| Компонент | Статус |
|-----------|--------|
| tests/conftest.py (fixtures) | ✅ |
| tests/unit/ai_agents/ | ✅ base_agent, intent_classifier, fraud_analyzer |
| tests/unit/orchestrator/ | ✅ state, graph |
| pytest.ini | ✅ |
| pytest-cov | ✅ |

### Healthcheck

| Endpoint | Статус | Описание |
|----------|--------|----------|
| GET /health | ✅ | Полная проверка (database, Redis) |
| GET /health/live | ✅ | Liveness probe |
| GET /health/ready | ✅ | Readiness probe |

### Logging

| Компонент | Статус |
|-----------|--------|
| Loguru | ✅ |
| setup_logging() | ✅ Rotation, compression |
| InterceptHandler | ✅ Standard logging |

### Graceful Shutdown

| Компонент | Статус |
|-----------|--------|
| SIGTERM/SIGINT handlers | ✅ |
| check_database_connection() | ✅ |
| 10 sec timeout | ✅ |
| POST /shutdown | ✅ |

### Безопасность

| Компонент | Статус |
|-----------|--------|
| JWT аутентификация | ✅ |
| Rate limiting | ✅ |
| Security headers | ✅ |
| CORS hardening | ✅ |
| Audit logging | ✅ |
| DB backup | ✅ |

### Auth Endpoints

Эндпоинты авторизации реализованы (статус: ✅). Детали см. в [api.md](api.md#rest-api-fastapi).

### Security Models

| Модель | Назначение |
|--------|------------|
| User | Пользователи с ролями |
| UserSession | Refresh токены |
| SecurityAuditLog | Аудит безопасности |
| ApiKey | Service-to-service ключи |

---

## ❌ Не реализовано

| Компонент | Приоритет | Примечание |
|-----------|-----------|------------|
| Integration тесты API | Средний | tests/integration/api/ |
| Sentry для ошибок | Средний | Мониторинг ошибок |
| Prometheus/Grafana | Низкий | Метрики и мониторинг |

---

## 📌 Отложено

| Компонент | Приоритет | Примечание |
|-----------|-----------|------------|
| CI/CD (GitHub Actions) | Низкий | Автоматизация деплоя |

---

## Известные проблемы

1. **PaymentParser OCR** — может неточно распознавать скриншоты на русском
2. **Processing API** — полностью mock, реальная интеграция отсутствует

---

## 🔧 Последние исправления (2026-05-17)

### Замена SqliteSaver на AsyncSqliteSaver
**Проблема:** При запуске мониторинга ордера ошибка:
```
Error in graph execution: The SqliteSaver does not support async methods.
Consider using AsyncSqliteSaver instead.
```

**Причина:**
- `app/orchestrator/graph.py` использовал синхронный `SqliteSaver`
- `server.py` вызывает асинхронный метод `p2p_graph.astream()`
- `aiosqlite` уже был установлен, но не использовался

**Исправлено:**
- Заменён импорт `SqliteSaver` → `AsyncSqliteSaver` из `langgraph.checkpoint.sqlite.aio`
- Добавлена ленивая инициализация через `get_p2p_graph()` и `get_checkpointer()`
- Обновлён `server.py`: `p2p_graph.astream()` → `(await get_p2p_graph()).astream()`
- Обновлён `orchestrator.py`: все методы переведены на async API (`astream`, `aget_state`, `aupdate_state`)
- Обновлена документация: `docs/modules/orchestrator.md`, `docs/architecture.md`

### Исправление мониторинга ордеров (sync/async)
**Проблема:** При запуске мониторинга ордера ошибка:
```
Error in graph execution: No synchronous function provided to "fetch_order".
Either initialize with a synchronous function or invoke via the async API (ainvoke, astream, etc.)
```

**Причина:**
- Все узлы графа (`app/orchestrator/nodes.py`) объявлены как `async def`
- В `server.py` граф вызывался синхронно через `p2p_graph.stream()`
- LangGraph требует async API (`astream`) для async-узлов

**Исправлено:**
- В `run_graph_async()` заменён `for event in p2p_graph.stream(...)` на `async for event in p2p_graph.astream(...)`
- Теперь весь пайплайн мониторинга выполняется корректно в асинхронном контексте

### Обновление списков валют в UI
**Проблема:** В выпадающих списках для выбора валют (поиск публичных объявлений и создание объявления) были только тестовые значения (RUB, USD) и 3 криптовалюты.

**Исправлено:**
- **Фиатные валюты** — расширено до 25 валют, поддерживаемых ByBit P2P:
  - RUB, USD, EUR, CNY, HKD, KZT, UAH, TRY, GBP, AED, CAD, AUD
  - THB, VND, INR, IDR, MYR, PHP, SGD, JPY, BRL, MXN, KRW, TWD, CHF
- **Криптовалюты** — USDT, BTC, ETH (по документации ByBit P2P API)
- Все валюты отображаются с расширенными названиями (например, `RUB — Российский рубль`)

### Исправление отображения веб-интерфейса
**Проблема:** При отсутствии авторизации все элементы (включая форму авторизации) отображались на одной странице.

**Причина:** 
- Основной контент `.container` был видим по умолчанию
- Отсутствовал общий CSS-класс `.hidden`
- Дублирующиеся CSS-правила

**Исправлено:**
- Добавлен общий CSS-класс `.hidden { display: none !important; }`
- Основной контент `.container` теперь скрыт по умолчанию (`id="main-container" class="hidden"`)
- Обновлены JS-функции `showAuthOverlay()`/`hideAuthOverlay()` для управления видимостью
- Удалены дублирующиеся CSS-правила (`.auth-tabs`, `.auth-form h2`, `.balance-item`, `.auth-error`)
- Унифицированы цвета через CSS-переменные (`var(--accent)`, `var(--danger)`)

### Docker volumes для development
**Добавлено:** Монтирование `templates/` и `static/` в read-only режиме для быстрой разработки без пересборки образа.

**Предупреждение:** Эти volumes должны быть удалены перед production деплоем (см. `docs/setup.md`).

### Интеграция P2P функций в веб-интерфейс (Текущее обновление)
**Добавлено:**
- **Загрузка файлов в чат:** Реализован API эндпоинт `POST /api/chat/{order_id}/upload` и UI-кнопка (скрепка) для прикрепления скриншотов/документов к P2P-чату.
- **Управление ордерами:** Добавлены кнопки действий в модальном окне деталей ордера:
  - "Отметить оплаченным" (mark as paid)
  - "Отпустить активы" (release assets)
  - "Отменить" (cancel order)
- **История торгов:** Добавлена новая вкладка "История торгов" (`trade_history`) для просмотра завершенных сделок пользователя.
- **Редактирование объявлений:** Добавлено модальное окно для редактирования созданного объявления (изменение цены, минимальной и максимальной суммы) с привязкой к `PUT /api/ads/{ad_id}`.
- **Профили аккаунта и контрагента:** Улучшено отображение базовой статистики (рейтинг, количество сделок, процент отмен) без сырых JSON-данных.
