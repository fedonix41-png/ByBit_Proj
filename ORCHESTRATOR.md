# Оркестратор (LangGraph)

## Обзор

Оркестратор построен на базе LangGraph - фреймворка для создания stateful multi-actor приложений. Он управляет полным жизненным циклом P2P сделки от обнаружения ордера до завершения платежа.

## Архитектура

### Основные компоненты

#### State (P2PAutomationState)
```python
@dataclass
class P2PAutomationState:
    # Текущий ордер
    current_order_id: Optional[str] = None
    order_details: Optional[Dict] = None

    # Сообщения и коммуникация
    messages: List[Dict] = field(default_factory=list)
    telegram_chat_id: Optional[str] = None

    # AI анализ
    current_intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    proposed_response: Optional[str] = None

    # Платежная информация
    payment_data: Optional[Dict] = None
    payment_proof_path: Optional[str] = None

    # Решения и approvals
    approval_required: bool = False
    response_approved: Optional[bool] = None
    risk_approved: Optional[bool] = None
    risk_score: Optional[float] = None

    # Статус и ошибки
    status: str = "idle"
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
```

#### Graph Nodes (12 узлов)

### 1. fetch_order_details
**Назначение**: Получение детальной информации об ордере из Bybit API.

**Вход**: current_order_id
**Выход**: order_details (цена, сумма, валюта, контрагент)
**Интеграции**: Bybit P2P API

### 2. check_new_messages
**Назначение**: Опрос новых сообщений от клиента.

**Вход**: current_order_id, telegram_chat_id
**Выход**: messages (список новых сообщений)
**Интеграции**: Telegram Bot API

### 3. classify_intent
**Назначение**: AI-анализ намерения клиента.

**Вход**: messages (последнее сообщение)
**Выход**: current_intent, intent_confidence
**Интеграции**: IntentClassifier AI agent

### 4. generate_response
**Назначение**: Генерация ответа на основе намерения.

**Вход**: current_intent, order_details
**Выход**: proposed_response
**Интеграции**: ResponseGenerator AI agent

### 5. await_response_approval [INTERRUPT]
**Назначение**: Ожидание подтверждения ответа человеком.

**Логика**:
- Устанавливает approval_required = True
- Передает управление в UI
- Ждет человеческого решения

### 6. send_response
**Назначение**: Отправка одобренного ответа клиенту.

**Вход**: proposed_response, response_approved
**Выход**: Отправленное сообщение в Telegram
**Интеграции**: Telegram Bot API

### 7. parse_payment_proof
**Назначение**: OCR-анализ скриншота платежа.

**Вход**: Фото от клиента
**Выход**: payment_data (сумма, карта, время)
**Интеграции**: PaymentParser AI agent

### 8. analyze_fraud_risk
**Назначение**: Оценка рисков платежа.

**Вход**: payment_data, order_details
**Выход**: risk_score, risk_flags
**Интеграции**: FraudAnalyzer AI agent

### 9. await_risk_approval [INTERRUPT]
**Назначение**: Ожидание подтверждения платежа человеком.

**Логика**:
- Проверяет risk_score
- При высоком риске требует подтверждения
- Передает данные в UI для решения

### 10. submit_to_processing
**Назначение**: Отправка транзакции в процессинговую систему.

**Вход**: payment_data, order_details
**Выход**: processing_id
**Интеграции**: Processing API client

### 11. confirm_payment
**Назначение**: Подтверждение оплаты в Bybit.

**Вход**: current_order_id
**Выход**: Статус подтверждения
**Интеграции**: Bybit P2P API

### 12. notify_completion
**Назначение**: Уведомление о завершении сделки.

**Вход**: Статус завершения
**Выход**: Уведомление в Telegram
**Интеграции**: Telegram Bot API

## Граф состояний

### Диаграмма workflow

```
┌─────────────────┐
│ fetch_order     │
│ _details        │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ check_new       │
│ _messages       │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│ classify_intent │────▶│ generate        │
└─────────┬───────┘     │ _response       │
          │             └─────────┬───────┘
          │                       │
          ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ await_response  │◄────┤ await_response  │
│ _approval       │     │ _approval       │
│ [INTERRUPT]     │     │ [INTERRUPT]     │
└─────────┬───────┘     └─────────────────┘
          │
          ▼
┌─────────────────┐
│ send_response   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ parse_payment   │
│ _proof          │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│ analyze_fraud   │────▶│ await_risk      │
│ _risk           │     │ _approval       │
└─────────┬───────┘     │ [INTERRUPT]     │
          │             └─────────┬───────┘
          ▼                       │
┌─────────────────┐               │
│ submit_to       │◄──────────────┘
│ _processing     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ confirm_payment │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ notify          │
│ _completion     │
└─────────────────┘
```

### Interrupt точки

#### Response Approval Interrupt
**Триггер**: После генерации ответа AI
**Цель**: Проверка и одобрение ответа перед отправкой
**UI компоненты**:
- Текст предложенного ответа
- Обоснование AI
- Кнопки: Одобрить/Отклонить/Редактировать

#### Risk Approval Interrupt
**Триггер**: После анализа рисков платежа
**Цель**: Подтверждение подозрительных транзакций
**UI компоненты**:
- Данные платежа (OCR результат)
- Risk score и флаги
- Рекомендация системы
- Кнопки: Одобрить/Отклонить

## Персистентность

### SqliteSaver
- **Файл**: checkpoints.db (создается автоматически)
- **Таблицы**: checkpoints, checkpoint_writes
- **Восстановление**: После перезапуска сервера

### State snapshots
```sql
-- checkpoints таблица
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BLOB,  -- Сериализованное состояние
    metadata BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- checkpoint_writes таблица
CREATE TABLE checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    value BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

### Recovery механизм
```python
# Восстановление состояния
config = {"configurable": {"thread_id": run_id}}
checkpoint = graph.get_state(config)
if checkpoint:
    # Продолжить с сохраненного состояния
    graph.update_state(config, checkpoint.values)
```

## Интеграция с UI

### WebSocket обновления
```javascript
// Real-time updates от оркестратора
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'monitor_started':
            showOrderMonitoring(data.run_id, data.order_id);
            break;
        case 'state_update':
            updateGraphState(data.state);
            break;
        case 'approval_required':
            showApprovalModal(data.approval_type, data.data);
            break;
        case 'monitor_completed':
            showCompletionMessage(data.run_id);
            break;
    }
};
```

### REST API endpoints
```python
# Запуск мониторинга
POST /api/start_monitor
{
  "order_id": "string"
}

# Подтверждение действия
POST /api/approve/{run_id}
{
  "approved": true,
  "user_input": "optional string"
}
```

## Обработка ошибок

### Node-level ошибки
```python
async def safe_node_execution(node_func, state, config):
    try:
        return await node_func(state, config)
    except Exception as e:
        logger.error(f"Node execution failed: {e}")
        state.error = str(e)
        state.status = "error"
        return state
```

### Recovery стратегии
- **Retry**: Повтор неудачных операций
- **Fallback**: Использование альтернативных API
- **Human intervention**: Escalation к человеку
- **Circuit breaker**: Отключение проблемных компонентов

### Error states
- `api_error`: Проблема с внешним API
- `ai_error`: Ошибка AI агента
- `validation_error`: Некорректные данные
- `timeout_error`: Превышение таймаута

## Мониторинг и отладка

### Логирование
```python
# Структурированные логи для каждого узла
logger.info(f"Node executed: {node_name}", extra={
    "run_id": run_id,
    "execution_time": execution_time,
    "input_state": input_state,
    "output_state": output_state
})
```

### Метрики
- **Execution time**: Время выполнения каждого узла
- **Success rate**: Процент успешных выполнений
- **Interrupt frequency**: Частота человеческих вмешательств
- **Error rate**: Процент ошибок по типам

### Debug режим
```python
# Подробное логирование состояния
if DEBUG:
    logger.debug(f"State transition: {old_state} -> {new_state}")
    logger.debug(f"Graph config: {config}")
```

## Тестирование

### Unit тесты узлов
```python
def test_fetch_order_details():
    state = P2PAutomationState(current_order_id="test_123")
    result = await fetch_order_details(state, {})
    assert result.order_details is not None

def test_intent_classification():
    state = P2PAutomationState(messages=[{"text": "Хочу купить BTC"}])
    result = await classify_intent(state, {})
    assert result.current_intent == "ready_to_pay"
```

### Integration тесты
```python
def test_full_workflow():
    # Создать ордер
    # Отправить сообщение
    # Сгенерировать ответ
    # Одобрить
    # Проверить завершение
    pass
```

### E2E тесты
- Полный цикл с Telegram ботом
- WebSocket коммуникация
- UI approval flow
- Error recovery scenarios

## Производительность

### Оптимизации
- **Async execution**: Все узлы асинхронные
- **Parallel processing**: Независимые ордера обрабатываются параллельно
- **State compression**: Оптимизация хранения состояния
- **Connection pooling**: Переиспользование API соединений

### Узкие места
- **External API calls**: Bybit/Processing API latency
- **AI processing**: Время генерации ответов
- **Image processing**: OCR для платежных скриншотов
- **Database I/O**: Чтение/запись состояния

### Масштабирование
```python
# Multi-instance deployment
# Redis для распределенного state
# Message queue для распределенной обработки
# Load balancer для API endpoints
```

## Расширение графа

### Добавление нового узла
```python
async def new_node(state: P2PAutomationState, config: dict) -> P2PAutomationState:
    # Логика нового узла
    state.some_new_field = "value"
    return state

# Добавление в граф
graph.add_node("new_node", new_node)
graph.add_edge("existing_node", "new_node")
```

### Условные переходы
```python
def route_based_on_intent(state: P2PAutomationState) -> str:
    if state.current_intent == "ready_to_pay":
        return "generate_payment_instructions"
    elif state.current_intent == "question":
        return "answer_question"
    else:
        return "default_response"

graph.add_conditional_edges(
    "classify_intent",
    route_based_on_intent,
    {
        "generate_payment_instructions": "payment_instructions_node",
        "answer_question": "answer_node",
        "default_response": "default_node"
    }
)
```

## Безопасность

### State validation
```python
def validate_state(state: P2PAutomationState) -> bool:
    # Проверка корректности состояния
    if state.approval_required and not state.proposed_response:
        return False
    return True
```

### Access control
- **Run isolation**: Каждый run_id изолирован
- **User context**: Связь с telegram_chat_id
- **Audit trail**: Полная история изменений состояния

### Data protection
- **Sensitive data**: Не логировать платежные данные
- **Encryption**: Шифрование сохраненного состояния
- **Cleanup**: Удаление старых состояний