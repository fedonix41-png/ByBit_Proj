# Changelog

Все значимые изменения в проекте документируются в этом файле.

## [Unreleased]

### Добавлено
- **Bybit Testnet API Integration**: Полная интеграция с Bybit P2P testnet API для безопасной разработки
- **Testnet-first подход**: Testnet API как основной режим разработки вместо mock
- **TESTNET_SETUP.md**: Подробное руководство по настройке testnet аккаунта и API ключей
- **Обновленная документация**: Все файлы обновлены для использования testnet API

### Изменено
- **README.md**: Testnet API позиционируется как основной режим разработки
- **QUICKSTART.md**: Инструкции по получению testnet API ключей
- **INTEGRATIONS.md**: Mock режим заменен на testnet API в примерах
- **DEVELOPMENT.md**: Добавлен раздел о testnet разработке
- **config.py**: Улучшенные сообщения об ошибках и проверки

### Планируется
- Реализация Processing API интеграции
- Интеграция Web UI с v2.0 оркестратором
- Добавление аутентификации UI
- Комплексное тестирование (unit, integration, e2e)
- Мониторинг и алерты (Prometheus + Grafana)
- Production hardening

## [2.0.0] - 2024-04-XX

### Добавлено
- **Модульная архитектура v2.0**: Полная реструктуризация проекта
- **AI-агенты**: 4 специализированных AI агента с мульти-провайдер поддержкой
  - IntentClassifier (классификация намерений)
  - ResponseGenerator (генерация ответов)
  - PaymentParser (OCR анализ платежей)
  - FraudAnalyzer (оценка рисков)
- **LangGraph оркестратор**: 12-узловой граф с персистентностью через SqliteSaver
- **PostgreSQL база данных**: Полная реляционная модель с SQLAlchemy + Alembic
- **Telegram Bot**: Полная интеграция с командами и обработкой фото
- **Docker Compose**: Полный стек с PostgreSQL и Telegram ботом
- **Мульти-провайдер AI**: OpenAI, Anthropic, Groq, Together, Mistral, Local (Ollama)

### Изменено
- Переход с монолитной архитектуры на модульную
- Замена SQLite на PostgreSQL для production
- Миграция с MemorySaver на SqliteSaver для персистентности
- Обновление всех зависимостей на современные версии

### Документация
- Полная реконструкция документации на основе кода
- Создание новых .md файлов: API_REFERENCE, DATABASE_SCHEMA, AI_AGENTS, ORCHESTRATOR, INTEGRATIONS, TESTING, DEVELOPMENT
- Исправление всех несоответствий между кодом и документацией

## [1.0.0] - 2024-01-XX

### Добавлено
- Первая рабочая версия MVP
- FastAPI сервер с WebSocket поддержкой
- LangGraph стейт-машина с Human-in-the-Loop
- Web UI с real-time обновлениями
- Mock Bybit P2P клиент для тестирования
- Управление сервером через ./manage.sh
- Базовая классификация намерений (rule-based)
- Секции: баланс, объявления, чат, история, подтверждение
- Документация: README, ARCHITECTURE, STATUS

### Технологии
- Python 3.11+
- FastAPI + Uvicorn
- LangGraph + MemorySaver
- WebSocket для real-time
- Jinja2 для шаблонов
- Pydantic v2 для валидации

---

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
версионирование следует [Semantic Versioning](https://semver.org/lang/ru/).
