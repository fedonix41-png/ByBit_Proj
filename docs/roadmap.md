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

## Этап 7: Тестирование 📋 ЗАПЛАНИРОВАНО

- [ ] Smoke-тесты
- [ ] Логирование ошибок
- [ ] Проверка БД при старте
- [ ] Graceful shutdown

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
