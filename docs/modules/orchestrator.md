# LangGraph Оркестратор

**Расположение:** `app/orchestrator/`

## Файлы

| Файл | Назначение |
|------|------------|
| `graph.py` | Сборка 12-узлового графа |
| `state.py` | TypedDict состояния |
| `nodes.py` | Узлы обработки |
| `edges.py` | Условные переходы |
| `orchestrator.py` | Управление выполнением |

---

## State (P2PAutomationState)

**Файл:** `state.py`

```python
class P2PAutomationState(TypedDict, total=False):
    # Ордер
    order_id: str
    order_data: Optional[Dict[str, Any]]
    
    # Сообщения
    messages: List[Dict[str, Any]]
    last_message: Optional[Dict[str, Any]]
    conversation_history: List[Dict[str, str]]
    
    # AI анализ
    intent: Optional[str]
    intent_confidence: Optional[float]
    entities: Optional[Dict[str, Any]]
    
    # Ответ
    proposed_response: Optional[str]
    response_tone: Optional[str]
    
    # Платёж
    payment_proof_path: Optional[str]
    payment_data: Optional[Dict[str, Any]]
    
    # Риски
    risk_score: Optional[float]
    risk_level: Optional[str]
    risk_flags: Optional[List[str]]
    risk_checks: Optional[Dict[str, bool]]
    
    # Процессинг
    processing_id: Optional[str]
    processing_status: Optional[str]
    
    # Подтверждения (Human-in-the-Loop)
    response_approval_required: bool
    response_approved: Optional[bool]
    risk_approval_required: bool
    risk_approved: Optional[bool]
    
    # Контекст
    user_id: Optional[str]
    username: Optional[str]
    
    # Служебное
    run_id: Optional[str]
    error: Optional[str]
    current_step: Optional[str]
```

---

## Graph

**Файл:** `graph.py`

### Узлы

```
1.  fetch_order          — Получение данных ордера
2.  check_messages       — Проверка новых сообщений
3.  classify_intent      — Классификация намерения
4.  generate_response    — Генерация ответа
5.  await_response_approval — Ожидание подтверждения (INTERRUPT)
6.  send_response        — Отправка ответа
7.  parse_payment        — Парсинг скриншота
8.  analyze_risk         — Анализ рисков
9.  await_risk_approval  — Ожидание подтверждения (INTERRUPT)
10. submit_processing    — Отправка в процессинг
11. confirm_payment      — Подтверждение в Bybit
12. notify_completion    — Уведомление о завершении
```

### Точки прерывания

```python
graph = workflow.compile(
    checkpointer=memory,
    interrupt_before=[
        "await_response_approval",  # Подтверждение ответа
        "await_risk_approval"       # Подтверждение риска
    ]
)
```

### Персистентность

```python
from langgraph.checkpoint.sqlite import SqliteSaver

conn = sqlite3.connect("data/checkpoints/p2p_state.db")
memory = SqliteSaver(conn)
```

---

## Nodes

**Файл:** `nodes.py`

### Пример узла

```python
async def classify_intent(state: P2PAutomationState) -> P2PAutomationState:
    """Классификация намерения сообщения."""
    last_message = state.get("last_message")
    
    if not last_message:
        state["intent"] = "no_message"
        return state
    
    result = await get_intent_classifier().process({
        "message": last_message.get("text", ""),
        "context": {
            "order_amount": state.get("order_data", {}).get("amount"),
            "currency": state.get("order_data", {}).get("currency"),
        }
    })
    
    state["intent"] = result.get("intent")
    state["intent_confidence"] = result.get("confidence")
    state["entities"] = result.get("entities")
    
    return state
```

### Связь узлов с агентами

| Узел | Агент/API |
|------|-----------|
| `classify_intent` | `IntentClassifier` |
| `generate_response` | `ResponseGenerator` |
| `parse_payment` | `PaymentParser` |
| `analyze_risk` | `FraudAnalyzer` |
| `fetch_order` | `bybit_client.get_order_details` |
| `check_messages` | `bybit_client.get_chat_messages` |
| `send_response` | `bybit_client.send_chat_message` |
| `confirm_payment` | `bybit_client.confirm_payment` |

---

## Edges

**Файл:** `edges.py`

Условные переходы между узлами.

```python
def should_process_message(state) -> Literal["process", "wait"]:
    return "process" if state.get("last_message") else "wait"

def should_send_response(state) -> Literal["send", "skip"]:
    return "send" if state.get("response_approved") else "skip"

def should_parse_payment(state) -> Literal["parse", "skip"]:
    intent = state.get("intent")
    if intent == "payment_sent" and state.get("payment_proof_path"):
        return "parse"
    return "skip"

def should_analyze_risk(state) -> Literal["analyze", "skip"]:
    payment_data = state.get("payment_data")
    if payment_data and payment_data.get("confidence", 0) > 0.5:
        return "analyze"
    return "skip"

def should_submit_processing(state) -> Literal["submit", "reject"]:
    return "submit" if state.get("risk_approved") else "reject"
```

---

## Orchestrator

**Файл:** `orchestrator.py`

### Методы

```python
class P2POrchestrator:
    async def process_telegram_message(
        self, user_id: str, text: str, message_id: str, username: str = None
    )
    
    async def process_payment_proof(self, user_id: str, photo_path: str)
    
    async def approve_response(
        self, run_id: str, approved: bool, modified_response: str = None
    )
    
    async def approve_risk(
        self, run_id: str, approved: bool, reason: str = None
    )
    
    async def get_user_orders(self, user_id: str) -> List[Dict]
```

### Использование

```python
from app.orchestrator.orchestrator import orchestrator

# Обработка сообщения
await orchestrator.process_telegram_message(
    user_id="123456",
    text="Готов оплатить",
    message_id="msg_1"
)

# Подтверждение ответа
await orchestrator.approve_response(
    run_id="run_123",
    approved=True
)
```
