# Установка и настройка

## Требования

- Python 3.11+
- PostgreSQL 15+ (или Docker)
- Tesseract OCR (для PaymentParser)
- uv (рекомендуется) или pip

## Переменные окружения

Создайте `.env` из примера:
```bash
cp .env.example .env
```

### Обязательные

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота |
| `BYBIT_API_KEY` | API ключ Bybit (testnet) |
| `BYBIT_API_SECRET` | API секрет Bybit (testnet) |

### Рекомендуемые

| Переменная | Default | Описание |
|------------|---------|----------|
| `BYBIT_TESTNET` | `True` | Использовать testnet (безопасно!) |
| `USE_MOCK_DATA` | `False` | Mock-режим Bybit |
| `USE_AI_MOCK` | `False` | Mock-режим AI |
| `DATABASE_URL` | - | PostgreSQL URL |
| `AI_PROVIDER` | `openai` | Провайдер AI |

### AI провайдеры

| Переменная | Провайдер |
|------------|-----------|
| `OPENAI_API_KEY` | OpenAI (GPT-4, Whisper) |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) |
| `GROQ_API_KEY` | Groq (Mixtral) |
| `TOGETHER_API_KEY` | Together AI |
| `MISTRAL_API_KEY` | Mistral AI |
| `LOCAL_LLM_URL` | Ollama (default: `http://localhost:11434`) |

### Сервер

| Переменная | Default | Описание |
|------------|---------|----------|
| `HOST` | `127.0.0.1` | Хост сервера |
| `PORT` | `8000` | Порт сервера |
| `DEBUG` | `True` | Режим отладки |

## Установка

### uv (рекомендуется)

```bash
# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установка зависимостей
uv sync
```

### pip + venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Запуск

### FastAPI сервер

```bash
# Через manage.sh
./manage.sh start

# Напрямую
uv run python main.py

# Через start.sh
./start.sh server
```

Доступ: http://127.0.0.1:8000

### Telegram-бот

```bash
./start.sh bot
# или
uv run python main_bot.py
```

### Docker Compose

```bash
# Запуск полного стека
docker-compose up -d

# Логи
docker-compose logs -f

# Остановка
docker-compose down
```

**Контейнеры:**
- `postgres` — PostgreSQL :5432
- `app` — FastAPI :8000
- `telegram_bot` — Telegram бот

## Миграции БД

```bash
# Применить миграции
uv run alembic upgrade head

# Статус
uv run alembic current

# Создать миграцию
uv run alembic revision --autogenerate -m "описание"

# Откатить
uv run alembic downgrade -1
```

## Управление сервером

```bash
./manage.sh start    # Запуск
./manage.sh stop     # Остановка
./manage.sh restart  # Перезапуск
./manage.sh status   # Статус
./manage.sh logs     # Логи
```

## Проверка

```bash
# Проверка конфигурации
uv run python -c "import config; config.validate_config()"

# Проверка БД
uv run python -c "from app.database.session import init_db; init_db()"

# Тест API
curl http://127.0.0.1:8000/api/balance
```

## Устранение проблем

### "TELEGRAM_BOT_TOKEN not set"
→ Добавьте токен в `.env`

### "bybit-p2p not installed"
→ `uv pip install bybit-p2p` или `USE_MOCK_DATA=True`

### "OPENAI_API_KEY not set"
→ Добавьте ключ или `USE_AI_MOCK=True`

### PostgreSQL не запускается
```bash
docker-compose down -v
docker-compose up -d
```
