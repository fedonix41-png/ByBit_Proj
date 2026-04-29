# Быстрый старт

## Требования
- **Python 3.11+**
- **uv** (рекомендуется) или pip
- **Docker** + Docker Compose (для полной установки)
- **PostgreSQL** (или использовать Docker)

## Установка

### 1. Клонирование и настройка
```bash
# Клонировать репозиторий
git clone <repository-url>
cd ByBit-tst

# Скопировать конфигурацию
cp .env.example .env
```

### 2. Настройка переменных окружения
Отредактируйте `.env` файл:

```bash
# Telegram Bot (получить от @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# AI Провайдеры (выберите один)
AI_PROVIDER=openai  # openai/anthropic/groq/together/mistral/local
OPENAI_API_KEY=your_openai_key

# Bybit API - Testnet (ОБЯЗАТЕЛЬНО для безопасной разработки)
BYBIT_API_KEY=your_testnet_api_key
BYBIT_API_SECRET=your_testnet_api_secret
BYBIT_TESTNET=true

# Processing API (пока mock, будет заменено на real)
USE_MOCK_DATA=false  # Для Bybit используем testnet API!

# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/p2p_automation
```

### Как получить Bybit Testnet API ключи

1. **Зарегистрируйтесь на testnet**: https://testnet.bybit.com/
2. **Войдите в аккаунт** и перейдите в **API Management**
3. **Создайте новый API ключ** с правами:
   - ✅ **P2P Trading** (чтение и запись)
   - ✅ **Read** (чтение)
   - ✅ **Write** (запись)
4. **Привяжите к IP-адресу** (для безопасности)
5. **Скопируйте** API Key и Secret в `.env` файл

⚠️ **Testnet полностью безопасен** - нет реальных денег!

### 3. Запуск через Docker (рекомендуется)
```bash
# Полная установка с PostgreSQL
./manage.sh start

# Или через docker-compose напрямую
docker-compose up -d
```

### 4. Проверка установки
```bash
# Проверить статус контейнеров
docker-compose ps

# Посмотреть логи
docker-compose logs -f telegram_bot
docker-compose logs -f app

# Проверить API
curl http://127.0.0.1:8000/api/ads
```

## Ручной запуск (альтернатива)

### Установка зависимостей
```bash
# Через uv (рекомендуется)
uv pip install -e .

# Или через pip
pip install -r requirements.txt
```

### Настройка базы данных
```bash
# Создать базу данных PostgreSQL
createdb p2p_automation

# Запустить миграции
alembic upgrade head
```

### Запуск компонентов
```bash
# Терминал 1: FastAPI сервер
python main.py

# Терминал 2: Telegram бот
python -m app.integrations.telegram_bot
```

## Проверка работоспособности

### 1. Web-интерфейс
Откройте [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 2. Telegram бот
1. Найдите бота в Telegram
2. Отправьте `/start`
3. Отправьте `/status`

### 3. API endpoints
```bash
# Проверить баланс
curl http://127.0.0.1:8000/api/balance

# Проверить объявления
curl http://127.0.0.1:8000/api/ads
```

## Первый тест автоматизации

### 1. Создать тестовый ордер
Используйте Bybit testnet для создания P2P ордера.

### 2. Запустить мониторинг
В веб-интерфейсе:
1. Выберите ордер из списка
2. Нажмите "Start Monitoring"

### 3. Симулировать общение
1. В Telegram отправьте сообщение боту: "Здравствуйте, хочу купить BTC"
2. Система проанализирует intent через AI
3. Появится запрос на подтверждение ответа
4. Подтвердите ответ в веб-интерфейсе

### 4. Проверить логи
```bash
# Логи приложения
docker-compose logs -f app

# Логи бота
docker-compose logs -f telegram_bot
```

## Структура проекта

```
ByBit-tst/
├── app/                          # Основное приложение (v2.0)
│   ├── ai_agents/               # AI агенты
│   ├── orchestrator/            # LangGraph автоматизация
│   ├── integrations/            # Внешние API
│   ├── database/                # Модели и сессии БД
│   └── ...
├── docker/                       # Docker конфигурация
├── alembic/                      # Миграции БД
├── static/                       # Статические файлы UI
├── templates/                    # HTML шаблоны
├── server.py                     # FastAPI сервер (v1 UI)
├── main.py                       # Точка входа
└── pyproject.toml                # Зависимости
```

## Команды управления

### Docker
```bash
# Запуск всех сервисов
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск конкретного сервиса
docker-compose restart telegram_bot

# Логи
docker-compose logs -f app
docker-compose logs -f postgres

# Миграции БД
docker-compose run --rm app alembic upgrade head
```

### Ручное управление
```bash
# Запуск сервера
python main.py

# Миграции
alembic upgrade head

# Очистка (осторожно!)
docker-compose down -v  # Удалит все данные
```

## Устранение неполадок

### Проблема: Контейнеры не запускаются
```bash
# Проверить статус
docker-compose ps

# Детальные логи
docker-compose logs

# Пересоздать контейнеры
docker-compose up --build --force-recreate
```

### Проблема: База данных недоступна
```bash
# Проверить PostgreSQL
docker-compose exec postgres psql -U p2p_user -d p2p_automation

# Или пересоздать
docker-compose down -v
docker-compose up -d postgres
```

### Проблема: Telegram бот не отвечает
```bash
# Проверить токен в .env
# Проверить логи бота
docker-compose logs telegram_bot

# Перезапустить бота
docker-compose restart telegram_bot
```

### Проблема: AI не работает
```bash
# Проверить API ключ
# Проверить AI_PROVIDER в .env
# Проверить логи приложения
docker-compose logs app
```

## Следующие шаги

1. **Настройка production**: Заменить mock данные на реальные API
2. **Безопасность**: Добавить аутентификацию UI
3. **Мониторинг**: Настроить логирование и алерты
4. **Тестирование**: Написать unit и integration тесты
5. **Документация**: Изучить API Reference и Architecture docs

## Поддержка

- **Документация**: См. README.md, ARCHITECTURE.md, API_REFERENCE.md
- **Логи**: Все логи доступны через `docker-compose logs`
- **База данных**: Доступ через `docker-compose exec postgres psql`