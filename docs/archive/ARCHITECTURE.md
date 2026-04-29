# 🏗️ Архитектура системы ByBit P2P Automation v2.0

## Обзор

Система представляет собой продвинутую автоматизацию P2P-торговли криптовалютой с AI-анализом и модульной архитектурой. Ключевая особенность - Human-in-the-Loop подтверждения на критических этапах принятия решений.

## Технологический стек

### Backend
- **Python 3.11+**: Асинхронное программирование, типизация
- **FastAPI**: REST API и WebSocket для real-time обновлений
- **LangGraph + SqliteSaver**: Оркестрация бизнес-процессов с персистентностью
- **SQLAlchemy + PostgreSQL**: Реляционная БД с миграциями через Alembic
- **Pydantic v2**: Валидация и сериализация данных

### AI и ML
- **Мульти-провайдер AI**: OpenAI, Anthropic, Groq, Together, Mistral, Local (Ollama)
- **AI Агенты**: Intent Classification, Response Generation, OCR Payment Parsing, Fraud Analysis
- **Fallback логика**: Graceful degradation при недоступности провайдеров

### Внешние интеграции
- **Telegram Bot API**: Общение с клиентами
- **Bybit P2P API**: Управление ордерами и платежами
- **Processing API**: Внешняя обработка транзакций (текущий статус: mock)

### Инфраструктура
- **Docker + Docker Compose**: Контейнеризация всех компонентов
- **PostgreSQL**: Основная БД для истории и состояний
- **uv**: Менеджер пакетов и зависимостей
- **Alembic**: Миграции базы данных

## Компоненты системы

### 1. AI Агенты (`app/ai_agents/`)
Модульная система AI-агентов с поддержкой мульти-провайдеров.

#### BaseAIAgent
- **Ответственность**: Абстракция над AI API, fallback логика
- **Провайдеры**: OpenAI, Anthropic, Groq, Together, Mistral, Local
- **Функции**: Retry логика, токен counting, cost tracking

#### IntentClassifier
- **Задача**: Классификация намерений клиента из сообщений
- **Intents**: greeting, ready_to_pay, payment_sent, cancel, complaint
- **Выход**: intent + confidence score

#### ResponseGenerator
- **Задача**: Генерация контекстных ответов
- **Вход**: intent, история чата, детали ордера
- **Выход**: Текст ответа + объяснение

#### PaymentParser
- **Задача**: OCR анализ скриншотов платежей
- **Вход**: Фото платежного подтверждения
- **Выход**: Сумма, карта, время, валидация

#### FraudAnalyzer
- **Задача**: Оценка рисков мошенничества
- **Методы**: Rule-based + AI анализ
- **Выход**: Risk score (0-1) + флаги рисков

### 2. Оркестратор (`app/orchestrator/`)
LangGraph-based управление бизнес-процессами.

#### Graph (12 узлов)
1. **fetch_order_details** - Получение деталей ордера из Bybit
2. **check_new_messages** - Опрос новых сообщений
3. **classify_intent** - AI анализ намерения
4. **generate_response** - Генерация ответа
5. **[INTERRUPT] await_response_approval** - Human approval
6. **send_response** - Отправка ответа
7. **parse_payment_proof** - OCR парсинг платежа
8. **analyze_fraud_risk** - Оценка рисков
9. **[INTERRUPT] await_risk_approval** - Human approval
10. **submit_to_processing** - Отправка в процессинг
11. **confirm_payment** - Подтверждение в Bybit
12. **notify_completion** - Уведомления

#### State Management
- **SqliteSaver**: Персистентность состояний
- **Recovery**: Восстановление после сбоев
- **Threading**: Отдельные потоки для каждого ордера
### 3. Интеграции (`app/integrations/`)
Внешние API клиенты.

#### Telegram Bot
- **Библиотека**: python-telegram-bot
- **Функции**: Команды (/start, /status, /cancel, /help), обработка текста и фото
- **Интеграция**: Routing сообщений в оркестратор

#### Bybit P2P Client
- **Статус**: Mock-режим + частичная интеграция
- **Функции**: Получение ордеров, чат, подтверждение платежей
- **Будущее**: Полная интеграция с Bybit API

#### Processing Client
- **Статус**: Mock-режим (заглушки)
- **Функции**: Submit транзакций, проверка статуса, webhooks
- **API**: Внешняя процессинговая система (не реализована)

### 4. База данных (`app/database/`)
PostgreSQL с SQLAlchemy.

#### Модели
- **Order**: P2P ордера с полными связями
- **Message**: Сообщения с AI анализом
- **Decision**: Человеческие решения (approvals)
- **Transaction**: Финансовые транзакции
- **AIInteraction**: История AI запросов с метриками

#### Сессии
- **get_db_session()**: Context manager для транзакций
- **Connection pooling**: Через SQLAlchemy

### 5. Web Interface
FastAPI сервер с WebSocket.

#### REST API
- **/api/ads**: Список объявлений
- **/api/balance**: Баланс аккаунта
- **/api/start_monitor**: Запуск автоматизации
- **/api/approve/{run_id}**: Подтверждение действий
- Полное API см. в API_REFERENCE.md

#### WebSocket
- **/ws**: Real-time обновления состояния
- **Broadcast**: Сообщения всем подключенным клиентам
- **Events**: monitor_started, state_update, approval_required, completed

## Поток автоматизации P2P

### Полный цикл ордера

```
1. Обнаружение ордера
   ↓
2. Telegram: "Здравствуйте, готов оплатить"
   ↓
3. IntentClassifier: intent="ready_to_pay" (confidence: 0.95)
   ↓
4. ResponseGenerator: "Реквизиты для оплаты: карта XXXX"
   ↓
5. [HUMAN APPROVAL] Подтверждение ответа
   ↓
6. Telegram Bot: отправка ответа
   ↓
7. Ожидание платежа...
   ↓
8. Telegram: скриншот платежа (фото)
   ↓
9. PaymentParser: OCR → сумма, карта, время
   ↓
10. FraudAnalyzer: risk_score=0.15 (low risk)
    ↓
11. [HUMAN APPROVAL] Подтверждение платежа
    ↓
12. Processing API: submit transaction
    ↓
13. Bybit API: confirm payment
    ↓
14. Telegram: "Сделка завершена успешно"
```

### Точки прерывания (Human-in-the-Loop)

1. **Response Approval**: Перед отправкой любого ответа клиенту
   - Показывает: Предлагаемый ответ + объяснение AI
   - Действия: Approve/Reject/Edit

2. **Risk Approval**: Перед подтверждением платежа
   - Показывает: Risk score + флаги + OCR данные
   - Действия: Approve/Reject с обоснованием

### Real-time коммуникация

```
AI Agent → Orchestrator → WebSocket → UI
     ↓            ↓            ↓        ↓
  Decision     State Update  Broadcast  Update
```

## Безопасность

### AI и данные
- **Human-in-the-Loop**: Обязательные подтверждения на всех критических действиях
- **AI Validation**: Проверка результатов AI перед применением
- **Fallback логика**: Продолжение работы при недоступности AI провайдеров

### API безопасность
- **API ключи**: Хранение в .env, не в коде
- **Testnet first**: Все тесты на Bybit testnet
- **IP whitelisting**: Ограничение доступа к API ключам

### Данные и приватность
- **Локальное хранение**: БД на локальном PostgreSQL
- **Шифрование**: Чувствительные данные (опционально)
- **Audit trail**: Полная история всех действий и решений

### Операционная безопасность
- **Контейнеризация**: Изоляция через Docker
- **Логирование**: Структурированные логи всех операций
- **Rate limiting**: Защита от перегрузки API (требуется реализация)

## Персистентность и хранение данных

### PostgreSQL (основная БД)
- **Модели**: Order, Message, Decision, Transaction, AIInteraction
- **Миграции**: Alembic для версионирования схемы
- **Связи**: Полная реляционная модель с foreign keys

### LangGraph State (SqliteSaver)
- **Файл**: checkpoints.db (создается автоматически)
- **Функции**: Сохранение состояния графа, восстановление после сбоев
- **Таблицы**: checkpoints, checkpoint_writes

### In-Memory State
- **active_runs**: Текущие сессии автоматизации
- **WebSocket connections**: Активные подключения UI
- **Очистка**: При завершении сессий и перезапуске

### Файловое хранилище
- **Payment proofs**: Скриншоты платежей (локально)
- **Логи**: Структурированные логи приложений
- **Backups**: Резервные копии БД

## Масштабируемость и развертывание

### Текущая архитектура (v2.0)
- **Модульная структура**: Разделение на AI agents, orchestrator, integrations
- **Docker Compose**: Полный стек (app, bot, postgres)
- **PostgreSQL**: Реляционная БД для персистентности
- **WebSocket**: Real-time коммуникация

### Ограничения текущей версии
- **Один инстанс**: Нет горизонтального масштабирования
- **Mock API**: Processing и частично Bybit в mock режиме
- **Локальное хранение**: Нет cloud storage
- **Нет мониторинга**: Отсутствуют метрики и алерты

### План развития
1. **Production hardening**
   - Аутентификация UI
   - Rate limiting и security
   - Мониторинг (Prometheus/Grafana)
   - Structured logging

2. **Расширение интеграций**
   - Реальная Processing API
   - Полная Bybit API интеграция
   - Webhook обработка
   - Multi-currency support

3. **Масштабирование**
   - Redis для кэширования
   - Message queues (RabbitMQ)
   - Kubernetes deployment
   - Multi-instance support

## Мониторинг и отладка

### Логирование
- **Структурированные логи**: JSON формат для всех компонентов
- **Уровни**: DEBUG, INFO, WARNING, ERROR
- **Компоненты**:
  - AI agents: API вызовы, токены, costs
  - Orchestrator: Graph events, state changes
  - Integrations: API requests/responses
  - Web server: HTTP/WebSocket events

### Текущее состояние мониторинга
- **Отсутствует**: Нет Prometheus/Grafana
- **Логи**: Доступны через docker-compose logs
- **Метрики**: Только базовые счетчики в коде

### План мониторинга
- Prometheus метрики для AI, API, database
- Grafana dashboards для визуализации
- Alerts для критических событий
- Health checks для всех сервисов

## Тестирование

### Текущая ситуация
- **Отсутствуют тесты**: Нет unit, integration или e2e тестов
- **Ручное тестирование**: Через UI и API endpoints
- **Mock режим**: Для безопасного тестирования

### Стратегия тестирования
```python
# Планируемые тесты
Unit Tests:
├── test_ai_agents.py        # AI провайдеры и agents
├── test_orchestrator.py     # LangGraph логика
├── test_integrations.py     # API клиенты
└── test_database.py         # Модели и сессии

Integration Tests:
├── test_api_endpoints.py    # REST API
├── test_websocket.py        # Real-time updates
└── test_full_flow.py        # End-to-end сценарии

E2E Tests:
└── test_telegram_flow.py    # Полный пользовательский флоу
```

### Testing Tools
- **pytest**: Основной фреймворк
- **pytest-asyncio**: Для асинхронных тестов
- **faker**: Генерация тестовых данных
- **responses**: Mock внешних API

## Развертывание

### Локальная разработка
```bash
# Через uv
uv run python main.py

# Или через Docker
docker-compose up -d
```

### Production готовность
- **Docker**: Полная контейнеризация
- **Environment**: .env для конфигурации
- **Database**: PostgreSQL с Alembic миграциями
- **Monitoring**: Логи через docker-compose logs

### Требуется для production
- Аутентификация UI
- HTTPS/TLS
- Backup стратегия
- Rate limiting
- Security hardening

## Зависимости

### Core
- **fastapi + uvicorn**: Web framework и сервер
- **langgraph + langchain**: Оркестрация и AI
- **sqlalchemy + psycopg2**: БД ORM и PostgreSQL драйвер
- **alembic**: Миграции БД

### AI Providers
- **openai, anthropic, groq, together, mistralai**: AI API клиенты
- **python-dotenv**: Конфигурация

### Integrations
- **python-telegram-bot**: Telegram Bot API
- **requests**: HTTP клиент для внешних API
- **pydantic**: Валидация данных

### Utils
- **uvicorn[standard]**: ASGI сервер с hot reload
- **jinja2**: HTML шаблоны
- **websockets**: WebSocket поддержка

## Статус реализации v2.0

### ✅ Реализовано
- Модульная архитектура с AI-агентами
- LangGraph оркестратор с 12 узлами
- PostgreSQL с полными моделями
- Telegram Bot интеграция
- Docker контейнеризация
- Web UI с WebSocket

### ⚠️ Mock режим
- Processing API (заглушки)
- Bybit API (частично mock)

### ❌ Требуется доработка
- Интеграция Web UI с v2.0 оркестратором
- Реальные API вместо mock
- Аутентификация и безопасность
- Тесты и мониторинг
- Production hardening

## Roadmap v2.1+

### Phase 1: Integration completion
- Реальная Processing API
- Полная Bybit API интеграция
- Webhook обработка

### Phase 2: Production ready
- Аутентификация UI
- Rate limiting и security
- Мониторинг (Prometheus/Grafana)
- Comprehensive testing

### Phase 3: Advanced features
- Multi-user support
- Advanced AI capabilities
- Mobile app
- API для third-party интеграций

### Phase 4: Scale
- Microservices architecture
- Cloud-native deployment
- Auto-scaling
- Global distribution
