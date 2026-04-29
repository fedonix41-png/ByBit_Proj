# 🤖 Bybit P2P Automation v2.1

> **Статус:** Продвинутая версия с AI-агентами и LangGraph оркестратором

Система автоматизации P2P-торговли криптовалютой на платформе Bybit с AI-анализом сообщений, оценкой рисков и обязательным человеческим контролем (Human-in-the-Loop).

---

## 🚀 Быстрый старт

```bash
# Установка
curl -LsSf https://astral.sh/uv/install.sh | sh
cd ByBit-tst
cp .env.example .env
# Отредактируйте .env!

# Запуск
./start.sh server   # FastAPI на http://127.0.0.1:8000
./start.sh bot      # Telegram-бот
./start.sh docker   # Полный стек через Docker
```

---

## 📖 Документация

**[docs/index.md](docs/index.md)** — оглавление документации

| Раздел | Описание |
|--------|----------|
| [docs/overview.md](docs/overview.md) | Обзор проекта |
| [docs/architecture.md](docs/architecture.md) | Архитектура и компоненты |
| [docs/stack.md](docs/stack.md) | **Стек технологий** |
| [docs/setup.md](docs/setup.md) | Установка и настройка |
| [docs/api.md](docs/api.md) | REST API и внешние сервисы |
| [docs/status.md](docs/status.md) | Текущее состояние |
| [docs/roadmap.md](docs/roadmap.md) | Дорожная карта |

**Модули:**
| Файл | Описание |
|------|----------|
| [docs/modules/ai_agents.md](docs/modules/ai_agents.md) | AI-агенты |
| [docs/modules/orchestrator.md](docs/modules/orchestrator.md) | LangGraph оркестратор |
| [docs/modules/telegram.md](docs/modules/telegram.md) | Telegram-бот |
| [docs/modules/database.md](docs/modules/database.md) | База данных |
| [docs/modules/bybit_client.md](docs/modules/bybit_client.md) | Bybit API |
| [docs/modules/bridge.md](docs/modules/bridge.md) | P2P Bridge |

---

## ⚠️ Важно

- **Testnet-first** — разработка только на тестовой сети
- **Human-in-the-Loop** — подтверждение критических действий
- **Mock-режим** — тестирование без реальных API

---

## 🛠️ Возможности

| Компонент | Описание |
|-----------|----------|
| AI-агенты | IntentClassifier, ResponseGenerator, PaymentParser, FraudAnalyzer |
| Оркестратор | 12-узловой LangGraph граф с прерываниями |
| Telegram-бот | Текст, голос, фото, InlineKeyboard меню |
| Bybit API | Testnet + mock fallback |
| База данных | PostgreSQL + Alembic миграции |
| Веб-интерфейс | FastAPI + WebSocket |

---

## 📝 Лицензия

MIT License
