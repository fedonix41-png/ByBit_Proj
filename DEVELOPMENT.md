# Настройка среды разработчика

## Обзор

Руководство по настройке локальной среды разработки для проекта ByBit P2P Automation. Поддерживаются Linux, macOS и Windows (WSL).

## Предварительные требования

### Системные зависимости
```bash
# Python 3.11+
python --version  # Должен быть 3.11 или выше

# uv (рекомендуется для управления зависимостями)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Docker + Docker Compose
docker --version
docker-compose --version

# Git
git --version
```

### IDE и инструменты
- **VS Code** с расширениями:
  - Python
  - Pylance
  - Jupyter
  - Docker
- **PyCharm Professional** (опционально)

## Быстрый старт

### 1. Клонирование проекта
```bash
git clone <repository-url>
cd ByBit-tst
```

### 2. Настройка виртуального окружения
```bash
# С uv (рекомендуется)
uv venv
source .venv/bin/activate  # Linux/macOS
# или .venv/Scripts/activate  # Windows

# С venv
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv/Scripts/activate     # Windows
```

### 3. Установка зависимостей
```bash
# С uv
uv pip install -e .

# С pip
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
```bash
cp .env.example .env

# Отредактируйте .env файл:
# - TELEGRAM_BOT_TOKEN (получить от @BotFather)
# - AI_PROVIDER (openai/anthropic/groq/together/mistral/local)
# - OPENAI_API_KEY (если используете OpenAI)
# - BYBIT_TESTNET=True (для безопасного тестирования)
# - USE_MOCK_DATA=True (для mock режима)
```

### 5. Настройка базы данных
```bash
# Через Docker
docker-compose up -d postgres

# Или локально (если установлен PostgreSQL)
createdb p2p_automation
```

### 6. Инициализация БД
```bash
# Применить миграции
alembic upgrade head

# Или через Docker
docker-compose run --rm app alembic upgrade head
```

### 7. Запуск приложения
```bash
# Development режим
python main.py

# Через Docker
docker-compose up -d
```

### 8. Проверка работы
```bash
# Открыть в браузере
open http://127.0.0.1:8000

# Проверить API
curl http://127.0.0.1:8000/api/ads
```

## Детальная настройка

### Структура проекта для разработки

```
ByBit-tst/
├── .venv/                    # Виртуальное окружение
├── .vscode/                  # VS Code настройки
│   ├── settings.json
│   ├── launch.json          # Debug конфигурации
│   └── extensions.json      # Рекомендуемые расширения
├── .env                      # Переменные окружения (не коммитить)
├── .env.example             # Шаблон переменных
├── pyrightconfig.json       # Pyright конфигурация
├── .pre-commit-config.yaml  # Pre-commit hooks
├── tests/                   # Тесты
└── [остальные файлы проекта]
```

### VS Code настройки

#### settings.json
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/*.pyc": true
  }
}
```

#### launch.json (для debugging)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: Telegram Bot",
      "type": "python",
      "request": "launch",
      "module": "python",
      "args": ["-m", "app.integrations.telegram_bot"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "tests/"],
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

#### extensions.json
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-toolsai.jupyter",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-vscode-remote.remote-containers",
    "ms-azuretools.vscode-docker"
  ]
}
```

### Pre-commit hooks

#### Установка
```bash
pip install pre-commit
pre-commit install
```

#### .pre-commit-config.yaml
```yaml
repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
  - id: trailing-whitespace
  - id: end-of-file-fixer
  - id: check-yaml
  - id: check-added-large-files

- repo: https://github.com/psf/black
  rev: 23.3.0
  hooks:
  - id: black
    language_version: python3

- repo: https://github.com/pycqa/isort
  rev: 5.12.0
  hooks:
  - id: isort
    args: ["--profile", "black"]

- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.5.1
  hooks:
  - id: mypy
    additional_dependencies: [types-all]
```

### Type checking (Pyright)

#### pyrightconfig.json
```json
{
  "include": ["app", "tests"],
  "exclude": ["**/__pycache__", ".venv", "data"],
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "pythonVersion": "3.11",
  "typeCheckingMode": "basic",
  "useLibraryCodeForTypes": true
}
```

## Рабочие процессы разработки

### Добавление новой зависимости
```bash
# С uv
uv add package-name

# С pip
pip install package-name
pip freeze > requirements.txt
```

### Работа с базой данных

#### Создание миграции
```bash
# Автоматическая миграция
alembic revision --autogenerate -m "Add new table"

# Ручная миграция
alembic revision -m "Custom changes"
```

#### Применение миграций
```bash
alembic upgrade head
```

#### Rollback
```bash
alembic downgrade -1
```

### Тестирование

#### Запуск тестов
```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный тест
pytest tests/unit/test_ai_agents.py -v
```

#### Отладка тестов
```bash
# С подробным выводом
pytest -xvs --pdb

# Только failing тесты
pytest --lf
```

### Логирование

#### Настройка логирования для разработки
```python
# В config.py или начале main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dev.log')
    ]
)
```

## Docker для разработки

### Development compose
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    volumes:
      - .:/app
      - .venv:/app/.venv
    environment:
      - DEBUG=True
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: p2p_automation
      POSTGRES_USER: p2p_user
      POSTGRES_PASSWORD: dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Использование
```bash
# Development режим
docker-compose -f docker-compose.dev.yml up -d

# Просмотр логов
docker-compose -f docker-compose.dev.yml logs -f app
```

## Работа с Bybit Testnet API

### Настройка testnet API (ОБЯЗАТЕЛЬНО)
```bash
# В .env - используйте ТОЛЬКО testnet ключи!
BYBIT_API_KEY=your_testnet_api_key
BYBIT_API_SECRET=your_testnet_api_secret
BYBIT_TESTNET=True          # Всегда true для разработки
USE_MOCK_DATA=False         # Использовать реальный API

# Проверить настройку
python -c "import config; config.validate_config()"
```

### Создание тестовых данных на testnet
1. **Пополните баланс** через faucet (100-500 USDT)
2. **Создайте объявление** на продажу USDT
3. **Найдите ордер** в веб-интерфейсе
4. **Запустите мониторинг** для тестирования

### Логирование API вызовов
```python
# Включить подробные логи
import logging
logging.getLogger('bybit_client').setLevel(logging.DEBUG)

# В логах увидите:
# ✅ BybitClient initialized with TESTNET API (safe for development)
# API call: get_my_ads -> success
```

### Отладка API проблем
```python
# Тестировать API напрямую
from bybit_client import bybit_client

# Проверить подключение
ads = await bybit_client.get_ads_list()
print(f"Найдено объявлений: {len(ads)}")

# Проверить баланс
balance = await bybit_client.get_balance()
print(f"Баланс: {balance}")
```

## Работа с AI провайдерами

### Настройка OpenAI
```bash
# В .env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4-turbo-preview
```

### Настройка локального Ollama
```bash
# Установить Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Скачать модель
ollama pull llama3.1:8b

# В .env
AI_PROVIDER=local
OLLAMA_MODEL=llama3.1:8b
```

### Тестирование AI
```python
# В Python REPL
from app.ai_agents.intent_classifier import IntentClassifier

agent = IntentClassifier()
result = await agent.classify("Хочу купить BTC")
print(result)
```

## Отладка и troubleshooting

### Common issues

#### Import errors
```bash
# Проверить PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Проверить установку пакетов
pip list | grep fastapi
```

#### Database connection
```bash
# Проверить подключение
python -c "from app.database.session import get_db_session; print('OK')"

# Проверить Alembic
alembic current
```

#### Port conflicts
```bash
# Найти процесс на порту
lsof -i :8000

# Убить процесс
kill -9 <PID>
```

#### Memory issues
```bash
# Проверить использование памяти
ps aux | grep python

# Для больших моделей AI увеличить лимит
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Debug tools

#### PDB debugging
```python
# Добавить breakpoint
import pdb; pdb.set_trace()

# В VS Code - использовать launch.json конфигурации
```

#### Logging levels
```python
# Временно включить DEBUG
logging.getLogger().setLevel(logging.DEBUG)

# Для конкретного модуля
logging.getLogger('app.orchestrator').setLevel(logging.DEBUG)
```

#### Performance profiling
```python
import cProfile

pr = cProfile.Profile()
pr.enable()
# your code here
pr.disable()
pr.print_stats(sort='cumulative')
```

## Contributing guidelines

### Code style
- **Black** для форматирования
- **isort** для сортировки импортов
- **MyPy** для type checking
- **Flake8** для linting

### Commit messages
```
feat: add new AI agent for risk analysis
fix: resolve database connection timeout
docs: update API reference for new endpoints
test: add integration tests for orchestrator
refactor: simplify state management in graph
```

### Pull requests
- Создавать PR из feature branch
- Запускать все тесты перед PR
- Обновлять документацию
- Добавлять миграции БД если нужно

## Production deployment

### Environment variables
```bash
# Production .env
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
LOG_LEVEL=INFO
```

### Docker production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    image: bybit-p2p:latest
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.prod
```

### Monitoring
- **Sentry** для error tracking
- **Prometheus** для metrics
- **Grafana** для dashboards
- **Structured logging** в JSON format

## Полезные команды

```bash
# Полная переустановка
make clean && make install && make run

# Запуск с hot reload
uvicorn main:app --reload

# Database reset
alembic downgrade base && alembic upgrade head

# Test coverage
pytest --cov=app --cov-report=term-missing

# Type checking
mypy app/

# Linting
flake8 app/

# Format code
black app/ && isort app/
```