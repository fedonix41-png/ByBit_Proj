# База данных

**Расположение:** `app/database/`

## Технологии

- **PostgreSQL** — основная БД
- **SQLAlchemy** — ORM
- **Alembic** — миграции

---

## Модели

**Файл:** `models.py`

### Order

P2P ордера.

```python
class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), unique=True, index=True)
    ad_id = Column(String(100))
    side = Column(String(10))  # BUY/SELL
    crypto = Column(String(20))
    currency = Column(String(10))
    amount = Column(Float)
    price = Column(Float)
    status = Column(String(50))
    counterparty = Column(String(100))
    counterparty_telegram_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    meta_info = Column(JSON)
    
    # Связи
    messages = relationship("Message", back_populates="order")
    decisions = relationship("Decision", back_populates="order")
    transactions = relationship("Transaction", back_populates="order")
```

### Message

Сообщения чата с AI-анализом.

```python
class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    message_id = Column(String(100), unique=True)
    sender = Column(String(20))  # me/counterparty
    text = Column(Text)
    intent = Column(String(50))
    confidence = Column(Float)
    entities = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(20))  # telegram/bybit
    
    order = relationship("Order", back_populates="messages")
```

### Decision

Решения (человеческие и автоматические).

```python
class Decision(Base):
    __tablename__ = 'decisions'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    decision_type = Column(String(50))  # response_approval/risk_approval
    approved = Column(Boolean)
    proposed_action = Column(Text)
    risk_score = Column(Float)
    risk_flags = Column(JSON)
    reason = Column(Text)
    decided_by = Column(String(50))  # human/auto
    decided_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="decisions")
```

### Transaction

Финансовые транзакции.

```python
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    processing_id = Column(String(100), unique=True)
    amount = Column(Float)
    currency = Column(String(10))
    status = Column(String(50))  # pending/completed/failed
    payment_proof_path = Column(String(500))
    payment_data = Column(JSON)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    order = relationship("Order", back_populates="transactions")
```

### AIInteraction

История AI-запросов.

```python
class AIInteraction(Base):
    __tablename__ = 'ai_interactions'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer)
    agent_type = Column(String(50))  # intent/response/ocr/fraud
    provider = Column(String(50))  # openai/anthropic/...
    model = Column(String(100))
    input_data = Column(JSON)
    output_data = Column(JSON)
    tokens_used = Column(Integer)
    cost = Column(Float)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Session

**Файл:** `session.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/checkpoints.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
```

---

## Миграции

**Расположение:** `alembic/versions/`

### Команды

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

### Существующие миграции

| Файл | Описание |
|------|----------|
| `001_initial_migration.py` | Создание всех таблиц |
| `002_fix_schema_issues.py` | Исправления схемы |

---

## ER-диаграмма

```
┌─────────────┐
│   Order     │
│             │
│ order_id    │
│ side        │
│ amount      │
│ status      │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────┴──────┐     ┌─────────────┐     ┌─────────────┐
│  Message    │     │  Decision   │     │ Transaction │
│             │     │             │     │             │
│ text        │     │ approved    │     │ amount      │
│ intent      │     │ decision_   │     │ status      │
│ confidence  │     │   type      │     │ payment_    │
└─────────────┘     └─────────────┘     │   data      │
                                        └─────────────┘

┌─────────────────┐
│ AIInteraction   │
│                 │
│ agent_type      │
│ provider        │
│ tokens_used     │
└─────────────────┘
```
