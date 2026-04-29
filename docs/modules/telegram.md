# Telegram-бот

**Расположение:** `app/infrastructure/interface/`

## Файлы

| Файл | Назначение |
|------|------------|
| `bot.py` | Настройка бота, команды, меню |
| `telegram_handlers.py` | Хэндлеры сообщений |

---

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие, главное меню |
| `/ask` | Режим AI-диалога (OpenRouter) |
| `/status` | Статус ордеров |
| `/cancel` | Отмена сделки |
| `/help` | Помощь |
| `/menu` | Интерактивное меню |
| `/demo` | Демонстрация функций |

---

## InlineKeyboard

### Главное меню

```
┌─────────────────┬─────────────────┐
│ 💬 Задать вопрос AI │ 📊 Статус торговли │
├─────────────────┼─────────────────┤
│ 🧠 Анализ P2P   │ 🛡️ Проверка мошенничества │
├─────────────────┼─────────────────┤
│ ⚙️ Настройки    │ ℹ️ О боте       │
└─────────────────┴─────────────────┘
```

### Подменю "🧠 Анализ P2P"

```
┌─────────────────┬─────────────────┐
│ 📈 По типу ордера │ 💱 По валюте   │
├─────────────────┼─────────────────┤
│ 📊 Все предложения │              │
├─────────────────┼─────────────────┤
│ ↩️ Назад        │                 │
└─────────────────┴─────────────────┘
```

| Callback | Описание |
|----------|----------|
| `p2p_analysis_by_type` | Анализ по типу ордера |
| `p2p_analysis_by_currency` | Анализ по валюте |
| `p2p_analysis_all` | Все предложения |

### Подменю "🛡️ Проверка мошенничества"

```
┌─────────────────┬─────────────────┐
│ 📷 Анализ скриншота │ 🔍 Проверка ордера │
├─────────────────┼─────────────────┤
│ 📋 История проверок │              │
├─────────────────┼─────────────────┤
│ ↩️ Назад        │                 │
└─────────────────┴─────────────────┘
```

| Callback | Описание |
|----------|----------|
| `fraud_screenshot` | Анализ скриншота платежа |
| `fraud_order` | Проверка ордера |
| `fraud_history` | История проверок |

### Подменю "⚙️ Настройки"

```
┌─────────────────┬─────────────────┐
│ 🤖 AI-провайдер │ 🌐 Язык         │
├─────────────────┼─────────────────┤
│ 📊 Баланс Bybit │                 │
├─────────────────┼─────────────────┤
│ ↩️ Назад        │                 │
└─────────────────┴─────────────────┘
```

| Callback | Описание |
|----------|----------|
| `settings_ai_provider` | Выбор AI-провайдера |
| `settings_language` | Язык интерфейса |
| `settings_bybit_balance` | Баланс Bybit |

### AI-чат клавиатура

```
┌─────────────────┬─────────────────┐
│ 🔄 Новый вопрос │ ↩️ В меню       │
└─────────────────┴─────────────────┘
```

| Callback | Описание |
|----------|----------|
| `ai_new_question` | Начать новый диалог |
| `menu_main` | Вернуться в главное меню |

### Демо-меню

```
┌─────────────────┬─────────────────┐
│ 📝 Текст        │ 🎤 Голос        │
├─────────────────┼─────────────────┤
│ 📷 Фото         │ 🖼️ Анализ чека  │
├─────────────────┼─────────────────┤
│ 📊 Статус       │ 🔙 В меню       │
└─────────────────┴─────────────────┘
```

---

## Состояния пользователя

| Состояние | Описание |
|-----------|----------|
| `ai_mode` | Режим AI-диалога |
| `current_menu` | Текущее меню |
| `ai_provider` | Выбранный AI-провайдер |
| `language` | Язык интерфейса |

---

## Интеграция с OpenRouter

OpenRouterClient используется для AI-диалога с пользователями:

- **Vision через OpenRouter** — модель `openai/gpt-4o` для анализа изображений
- **Fallback на OpenAI** — если `OPENROUTER_API_KEY` не настроен

```python
from app.ai_agents.openrouter_adapter import OpenRouterClient

client = OpenRouterClient()
if client.is_configured:
    response = await client.generate(
        prompt="Как проверить контрагента?",
        system="Ты - помощник для P2P торговли..."
    )
```

---

## Хэндлеры сообщений

### Зависимости

- `OpenRouterClient` из `app/ai_agents/openrouter_adapter.py` — для AI-ответов
- `OPENROUTER_API_KEY` — переменная окружения для аутентификации

### Текст

**Функция:** `handle_text(update, context)`

```python
# Обработка текстового сообщения
response = await p2p_bridge.process_text_message(
    user_id=user_id,
    text=user_message,
    username=username
)
```

### Голос

**Функция:** `handle_voice(update, context)`

```python
# 1. Скачать аудио
file = await context.bot.get_file(voice.file_id)
await file.download_to_drive(TEMP_VOICE_PATH)

# 2. Транскрибировать (Whisper)
transcription = openai_client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-1"
)

# 3. Обработать как текст
response = await p2p_bridge.process_voice_message(
    user_id=user_id,
    transcription=transcription.text
)
```

**Требования:** `OPENAI_API_KEY`

### Фото

**Функция:** `handle_photo(update, context)`

```python
# 1. Скачать фото
photo = update.message.photo[-1]
file = await context.bot.get_file(photo.file_id)
await file.download_to_drive(photo_path)

# 2. Анализ (GPT-4 Vision)
vision_response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": PAYMENT_IMAGE_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    }]
)

# 3. Обработать
response = await p2p_bridge.process_photo_with_analysis(
    user_id=user_id,
    photo_path=photo_path,
    analysis=analysis
)
```

**Требования:** `OPENAI_API_KEY` или `OPENROUTER_API_KEY`

---

## Запуск

### Через main_bot.py

```python
from app.infrastructure.interface.bot import P2PTelegramBot

bot = P2PTelegramBot()
bot.run()
```

### Отдельный процесс

Бот запускается в отдельном процессе через `multiprocessing`:

```python
def run(self):
    def run_polling():
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
        )
    
    process = multiprocessing.Process(target=run_polling, daemon=True)
    process.start()
    process.join()
```

---

## Семантические маркеры

**Файл:** `app/domain/prompts/semantic_markers.py`

| Маркер | Назначение |
|--------|------------|
| `[IMAGE_ANALYSIS]` | Результат анализа изображения |
| `[VOICE]` | Транскрипция голосового |
| `[PAYMENT_PROOF]` | Данные платёжного доказательства |
| `[CONTEXT]` | Контекст сообщения |

```python
from app.domain.prompts.semantic_markers import (
    format_image_message,
    format_voice_message,
    format_payment_proof
)

# Примеры использования
formatted = format_voice_message("Привет, готов оплатить")
# "[VOICE] Привет, готов оплатить"

formatted = format_payment_proof("Сумма: 10000 RUB", {"bank": "Сбербанк"})
# "[PAYMENT_PROOF] Сумма: 10000 RUB [bank: Сбербанк]"
```
