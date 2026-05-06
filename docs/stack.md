# Стек технологий

**Версия проекта:** 2.1.0

---

## Ядро

| Технология | Версия | Назначение |
|------------|--------|------------|
| Python | ≥3.11 | Основной язык |
| uv | - | Менеджер зависимостей (uv.lock) |
| hatchling | - | Система сборки |

---

## AI / Агенты

| Пакет | Версия | Назначение |
|-------|--------|------------|
| langchain-core | ≥0.3.0 | Ядро LangChain |
| langchain-openai | ≥0.2.0 | Интеграция с OpenAI и OpenAI-совместимыми API |
| langgraph | ≥0.2.45 | Оркестратор (12-узловой граф) |
| langgraph-checkpoint-sqlite | ≥1.0.0 | Персистентность состояния графа |

### AI-провайдеры

| Пакет | Версия | Провайдер |
|-------|--------|-----------|
| openai | ≥1.0.0 | OpenAI (GPT-4, Whisper) |
| anthropic | ≥0.18.0 | Anthropic (Claude) |
| groq | ≥0.4.0 | Groq (Mixtral, Llama) |
| together | ≥1.0.0 | Together AI |
| mistralai | ≥0.1.0 | Mistral AI |

### OpenRouter.ai

Использовать OpenAI-совместимый интерфейс через `langchain-openai`:

```python
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    model="openai/gpt-4-turbo"
)
```

**Примечание:** Пакет `openai` уже установлен, дополнительных зависимостей не требуется.

---

## Telegram Bot

| Пакет | Версия | Примечание |
|-------|--------|------------|
| python-telegram-bot | ≥21.0 | **Не aiogram** |

---

## Веб-сервер

| Пакет | Версия | Назначение |
|-------|--------|------------|
| fastapi | ≥0.115.0 | REST API |
| uvicorn[standard] | ≥0.32.0 | ASGI-сервер |
| websockets | ≥14.1 | Real-time (WebSocket) |
| jinja2 | ≥3.1.4 | HTML-шаблоны |

---

## Базы данных

| Пакет | Версия | Назначение |
|-------|--------|------------|
| sqlalchemy | ≥2.0.0 | ORM |
| alembic | ≥1.13.0 | Миграции |
| psycopg2-binary | ≥2.9.0 | PostgreSQL драйвер |
| aiosqlite | ≥0.20.0 | Async SQLite |

**PostgreSQL** — основная БД (ордера, сообщения, решения).  
**SQLite** — чекпоинты LangGraph (`data/checkpoints/p2p_state.db`).

---

## Redis

| Пакет | Версия | Назначение |
|-------|--------|------------|
| redis | ≥5.0.0 | Rate limiting, кэширование |

**Redis** — rate limiting и кэширование для MessageProcessor.

**Docker:** сервис `redis` в docker-compose.yml

---

## Внешние API

| Пакет | Версия | Назначение |
|-------|--------|------------|
| bybit-p2p | ≥1.0.0 | Bybit P2P API клиент |
| httpx | ≥0.28.0 | HTTP клиент для API вызовов |

---

## Утилиты

| Пакет | Версия | Назначение |
|-------|--------|------------|
| pydantic | ≥2.10.0 | Валидация данных |
| pydantic-settings | ≥2.6.0 | Конфигурация через Settings |
| python-dotenv | ≥1.0.1 | Загрузка .env |
| loguru | ≥0.7.0 | Логирование |
| tenacity | ≥8.0.0 | Ретраи (используется в P2P Bridge) |

---

## OCR (опционально)

| Пакет | Версия | Назначение |
|-------|--------|------------|
| pillow | ≥10.0.0 | Обработка изображений |
| pytesseract | ≥0.3.10 | OCR для скриншотов платежей |

**Системные требования:** Tesseract OCR с русским языком (`tesseract-ocr-rus`)

---

## Деплой

**Docker Compose** — 3 сервиса:

| Сервис | Dockerfile | Назначение |
|--------|------------|------------|
| `postgres` | postgres:15-alpine | База данных |
| `app` | docker/Dockerfile | FastAPI сервер |
| `telegram_bot` | docker/Dockerfile.bot | Telegram бот |

**Разработка:** через `uv` (не pip)

---

## Конфигурация

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    BYBIT_API_KEY: str
    BYBIT_API_SECRET: str
    OPENAI_API_KEY: str = None
    # ...
    
    model_config = SettingsConfigDict(env_file='.env')
```

---

## Полный список зависимостей

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "jinja2>=3.1.4",
    "python-dotenv>=1.0.1",
    "langgraph>=0.2.45",
    "langgraph-checkpoint-sqlite>=1.0.0",
    "langchain-core>=0.3.0",
    "langchain-openai>=0.2.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "websockets>=14.1",
    "httpx>=0.28.0",
    "aiosqlite>=0.20.0",
    "bybit-p2p>=1.0.0",
    "python-telegram-bot>=21.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    "psycopg2-binary>=2.9.0",
    "openai>=1.0.0",
    "anthropic>=0.18.0",
    "groq>=0.4.0",
    "together>=1.0.0",
    "mistralai>=0.1.0",
    "pillow>=10.0.0",
    "pytesseract>=0.3.10",
    "loguru>=0.7.0",
    "tenacity>=8.0.0",
]
```
