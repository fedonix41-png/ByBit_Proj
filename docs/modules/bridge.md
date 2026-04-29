# P2P Bridge

**Файл:** `app/infrastructure/bridge/p2p_bridge.py`

## Назначение

Адаптер между Telegram-интерфейсом и оркестратором.

**Ответственности:**
- Форматирование входящих сообщений
- Управление контекстом диалога
- Ретраи при ошибках
- Маршрутизация в оркестратор

---

## Класс P2PBridgeService

### Инициализация

```python
from app.infrastructure.bridge.p2p_bridge import p2p_bridge

# Глобальный экземпляр
p2p_bridge.set_telegram_bot(bot)
p2p_bridge.set_orchestrator(orchestrator)
```

---

## Методы

### process_text_message

Обработка текстового сообщения.

```python
response = await p2p_bridge.process_text_message(
    user_id=123456,
    text="Готов оплатить",
    username="user_name"
)

# Возвращает:
# {"response_type": "text", "message": None}
```

### process_voice_message

Обработка транскрибированного голосового.

```python
response = await p2p_bridge.process_voice_message(
    user_id=123456,
    transcription="Привет, готов оплатить",
    username="user_name"
)
```

### process_photo_with_analysis

Обработка фото с AI-анализом.

```python
response = await p2p_bridge.process_photo_with_analysis(
    user_id=123456,
    photo_path="/tmp/photo.jpg",
    analysis="Сумма: 10000 RUB, Банк: Сбербанк",
    caption="Чек об оплате"
)
```

### process_payment_proof

Прямая обработка скриншота платежа.

```python
response = await p2p_bridge.process_payment_proof(
    user_id=123456,
    photo_path="/tmp/payment.jpg"
)
```

---

## Контекст диалога

In-memory хранение истории сообщений.

```python
# Получить историю
history = p2p_bridge._get_conversation_history(user_id)
# [{"role": "user", "content": "...", "timestamp": "..."}]

# Добавить в историю
p2p_bridge._add_to_history(user_id, "user", "Сообщение")

# Очистить
p2p_bridge.clear_conversation(user_id)

# Сводка
summary = p2p_bridge.get_conversation_summary(user_id)
# {"user_id": "...", "message_count": 5, "last_message": {...}}
```

**Ограничение:** `MAX_CONVERSATION_HISTORY` (default: 20)

---

## Ретраи

Автоматические повторы при ошибках.

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def process_text_message(self, ...):
    ...
```

---

## Семантические маркеры

Bridge использует маркеры из `app/domain/prompts/semantic_markers.py`:

```python
from app.domain.prompts.semantic_markers import (
    format_voice_message,
    format_image_message,
    format_payment_proof
)

# Примеры
format_voice_message("Транскрипция")
# "[VOICE] Транскрипция"

format_payment_proof(analysis, {"source": "vision"})
# "[PAYMENT_PROOF] анализ [source: vision]"
```

---

## Интеграция с оркестратором

```python
# В process_text_message
await self.orchestrator.process_telegram_message(
    user_id=str(user_id),
    text=text,
    message_id=f"txt_{user_id}_{hash(text) % 1000000}",
    username=username,
    context={
        "input_type": "text",
        "conversation_history": self._get_conversation_history(user_id)
    }
)
```

---

## Использование в Telegram Handlers

```python
# telegram_handlers.py
from app.infrastructure.bridge.p2p_bridge import p2p_bridge

async def handle_text(update, context):
    response = await p2p_bridge.process_text_message(
        user_id=update.message.from_user.id,
        text=update.message.text,
        username=update.message.from_user.username
    )
    await _send_response(update, context, response)
```
