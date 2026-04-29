# Bybit P2P Automation — Документация

**Версия:** 2.1.0 | **Обновлено:** 2026-04-29

---

## Быстрая навигация

| Документ | Описание |
|----------|----------|
| [overview.md](overview.md) | Назначение, возможности, целевая аудитория |
| [architecture.md](architecture.md) | Архитектура системы, компоненты, потоки данных |
| [stack.md](stack.md) | **Стек технологий** (зависимости, версии, провайдеры) |
| [setup.md](setup.md) | Установка, настройка, переменные окружения |
| [api.md](api.md) | REST API, WebSocket, внешние сервисы |
| [status.md](status.md) | Текущее состояние реализации |
| [roadmap.md](roadmap.md) | План развития проекта |

## Модули

| Документ | Описание |
|----------|----------|
| [modules/ai_agents.md](modules/ai_agents.md) | AI-агенты: классификация, генерация, анализ |
| [modules/orchestrator.md](modules/orchestrator.md) | LangGraph оркестратор: граф, узлы, состояние |
| [modules/telegram.md](modules/telegram.md) | Telegram-бот: команды, хэндлеры, меню |
| [modules/database.md](modules/database.md) | База данных: модели, миграции |
| [modules/bybit_client.md](modules/bybit_client.md) | Bybit API клиент |
| [modules/bridge.md](modules/bridge.md) | P2P Bridge: связь интерфейса и оркестратора |

---

## Быстрый старт

```bash
# 1. Настройка
cp .env.example .env
# Отредактируйте .env (API ключи, токены)

# 2. Установка
uv sync

# 3. Запуск
./start.sh server   # FastAPI на http://127.0.0.1:8000
./start.sh bot      # Telegram-бот
./start.sh docker   # Полный стек через Docker
```

---

## Структура проекта

```
app/
├── ai_agents/        # AI-агенты (OpenAI, Anthropic, etc.)
├── orchestrator/     # LangGraph граф (12 узлов)
├── infrastructure/   # Telegram бот, Bridge
├── database/         # SQLAlchemy модели
├── integrations/     # Внешние API клиенты
└── domain/           # Доменные модели, промпты

bybit_client.py       # Bybit P2P API клиент
server.py             # FastAPI сервер
main.py / main_bot.py # Точки входа
```

---

*Подробнее см. в соответствующих разделах документации.*
