# Дорожная карта

## Этап 1: Консолидация кода ✅ ЗАВЕРШЁН

- [x] Удалить корневой `graph.py`
- [x] Переключить server.py на orchestrator/
- [x] Единый граф для веб и бота

## Этап 2: Очистка документации ✅ ЗАВЕРШЁН

- [x] Архивировать устаревшие .md файлы
- [x] Создать структурированную документацию в /docs/
- [x] Обновить README.md

## Этап 3: Доработка AI ✅ ЗАВЕРШЁН

- [ ] Верифицировать PaymentParser на реальных скриншотах
- [x] Добавить правила в FraudAnalyzer
  - [x] 8 rule-based проверок
  - [x] BIN-коды 19 банков
  - [x] BANK_ALIASES нормализация
  - [x] duplicate_check (SHA-256)
  - [x] metadata_check (EXIF)
- [x] Логирование AI-взаимодействий в БД
  - [x] AILogger с PRICING_TABLE
  - [x] AIInteraction модель
  - [x] ScreenshotHash модель
  - [x] BaseAIAgent: log_to_db, agent_type, order_id, latency_ms
- [ ] Подключить реальный Processing API

## Этап 4: OpenRouter.ai ✅ ЗАВЕРШЁН

- [x] Добавить OPENROUTER_API_KEY в config
- [x] Реализовать _generate_openrouter() в BaseAIAgent
- [x] Добавить AIProvider.OPENROUTER
- [x] Создать OpenRouterClient (openrouter_adapter.py)
- [x] Интегрировать в docker-compose.yml
- [x] Vision через OpenRouter

## Этап 5: Переработка меню бота ✅ ЗАВЕРШЁН

- [x] Новое главное меню с InlineKeyboard
- [x] Команда /ask для AI-диалога
- [x] Подменю Анализ P2P
- [x] Подменю Проверка мошенничества
- [x] Подменю Настройки
- [x] Состояния пользователя (ai_mode, current_menu)
- [x] Vision через OpenRouter

## Этап 6: MessageProcessor ✅ ЗАВЕРШЁН

- [x] Модели БД: BlacklistEntry, ViolationHistory, ABTestConfig, WebhookEvent
- [x] MessageProcessor с правилами безопасности
- [x] Redis для rate limiting
- [x] ML-детекция спама через OpenRouter
- [x] Webhook-уведомления о нарушениях
- [x] A/B тестирование правил
- [x] Интеграция в telegram_handlers

## Этап 7: Тестирование ✅ ЗАВЕРШЁН

- [x] Smoke-тесты
  - [x] tests/conftest.py с fixtures (event_loop, mock_settings, mock_db_session, mock_bybit_client)
  - [x] tests/unit/ai_agents/test_base_agent.py
  - [x] tests/unit/ai_agents/test_intent_classifier.py
  - [x] tests/unit/ai_agents/test_fraud_analyzer.py (BIN, карты, телефоны)
  - [x] tests/unit/orchestrator/test_state.py
  - [x] tests/unit/orchestrator/test_graph.py
- [x] Unified logging
  - [x] app/core/logging_config.py с Loguru
  - [x] setup_logging() с rotation и compression
  - [x] InterceptHandler для стандартного logging
- [x] Проверка БД при старте
  - [x] check_database_connection() в server.py
- [x] Graceful shutdown
  - [x] Signal handlers для SIGTERM/SIGINT
  - [x] Таймаут 10 сек для завершения операций
  - [x] POST /shutdown endpoint для тестирования
- [x] Healthcheck endpoints
  - [x] GET /health - полная проверка (database, Redis)
  - [x] GET /health/live - liveness probe
  - [x] GET /health/ready - readiness probe
- [x] pytest.ini с настройками
- [x] Зависимости: pytest>=8.0.0, pytest-asyncio>=0.23.0, pytest-cov>=4.1.0, pytest-mock>=3.12.0

## Этап 8: Production 📋 ЗАПЛАНИРОВАНО

- [ ] Аутентификация веб-интерфейса
- [ ] Резервное копирование БД
- [ ] Healthcheck endpoints
- [ ] Rate limiting

## Этап 9: Расширения 📋 ДОЛГОСРОЧНО

- [ ] Backtesting
- [ ] Цепочки агентов
- [ ] Автоуведомления о рисках
- [ ] Админ-панель
- [ ] Prometheus/Grafana
- [ ] CI/CD (GitHub Actions)
- [ ] Автотрейдинг с ИИ

---

## Приоритеты на ближайший месяц

1. **Тесты** — критично для стабильности
2. **PaymentParser верификация** — проверка OCR
3. **Processing API** — интеграция с реальным API
