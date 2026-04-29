# Архитектура

## Схема компонентов

```
┌─────────────────────────────────────────────────────────────────┐
│                      ВНЕШНИЕ СЕРВИСЫ                             │
├─────────────┬─────────────┬─────────────┬─────────────────────────┤
│  Telegram   │   Bybit     │     AI      │   Processing           │
│    API      │  P2P API    │  Providers  │     API (mock)         │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────────────────────┘
       │             │             │
       ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ИНТЕРФЕЙСНЫЙ СЛОЙ                             │
├───────────────────────┬─────────────────────────────────────────┤
│    Telegram Bot       │           FastAPI Server                 │
│  (interface/bot.py)   │         (server.py)                      │
│                       │                                          │
│  • Команды            │  • REST API (/api/*)                    │
│  • InlineKeyboard     │  • WebSocket (/ws)                      │
│  • Хэндлеры           │  • HTML templates                       │
└───────────┬───────────┴──────────────┬──────────────────────────┘
            │                          │
            ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        P2P Bridge                                │
│              (infrastructure/bridge/p2p_bridge.py)               │
│                                                                  │
│  • Форматирование сообщений    • Ретраи (tenacity)              │
│  • Контекст диалога            • Семантические маркеры          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph ОРКЕСТРАТОР                          │
│                     (orchestrator/)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  graph.py ──── 12-узловой граф с прерываниями                   │
│  state.py ──── P2PAutomationState (TypedDict)                   │
│  nodes.py ──── Узлы обработки                                   │
│  edges.py ──── Условные переходы                                │
│                                                                  │
│  Персистентность: SqliteSaver                                   │
│  Точки прерывания: response_approval, risk_approval             │
│                                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐    ┌────────────────┐    ┌────────────────┐
│  AI-агенты   │    │ Bybit клиент   │    │  Processing    │
│ (ai_agents/) │    │(bybit_client)  │    │    клиент      │
├──────────────┤    ├────────────────┤    ├────────────────┤
│ IntentClass. │    │ testnet/prod   │    │ mock-режим     │
│ IntentRouter │    │ mock fallback  │    │                │
│ ResponseGen  │    │                │    │                │
│ PaymentPars. │    │                │    │                │
│ FraudAnalyz. │    │                │    │                │
└──────────────┘    └────────────────┘    └────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ХРАНИЛИЩЕ ДАННЫХ                            │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Docker)          SQLite (персистентность графа)    │
│  • Order, Message             • data/checkpoints/p2p_state.db  │
│  • Decision, Transaction      • SqliteSaver                     │
│  • AIInteraction              • Состояние диалогов              │
│                                                                  │
│  Миграции: Alembic                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Граф оркестратора

```
                    ┌─────────────┐
                    │ fetch_order │
                    └──────┬──────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ check_messages│
                   └───────┬───────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
               [process]      [wait] → END
                    │
                    ▼
              ┌──────────────┐
              │classify_intent│
              └───────┬──────┘
                      │
                      ▼
           ┌──────────────────┐
           │generate_response │
           └─────────┬────────┘
                     │
                     ▼
       ┌─────────────────────────┐
       │await_response_approval  │ ◄── INTERRUPT
       └────────────┬────────────┘
                    │
             ┌──────┴──────┐
             ▼             ▼
          [send]        [skip] → END
             │
             ▼
       ┌─────────────┐
       │send_response│
       └──────┬──────┘
              │
       ┌──────┴──────┐
       ▼             ▼
   [parse]        [skip] → END
       │
       ▼
┌──────────────┐
│parse_payment │
└──────┬───────┘
       │
       ▼
 ┌──────────────┐
 │analyze_risk  │
 └──────┬───────┘
       │
       ▼
┌─────────────────────┐
│await_risk_approval  │ ◄── INTERRUPT
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
[submit]      [reject] → END
    │
    ▼
┌──────────────────┐
│submit_processing │
└────────┬─────────┘
         │
         ▼
 ┌────────────────┐
 │confirm_payment │
 └───────┬────────┘
         │
         ▼
┌───────────────────┐
│notify_completion  │
└─────────┬─────────┘
          │
          ▼
         END
```

## Поток данных (типичный сценарий)

```
Пользователь пишет в Telegram
           │
           ▼
    Telegram Bot API
           │
           ▼
      P2P Bridge
   (добавляет контекст)
           │
           ▼
      Orchestrator
           │
           ▼
   ┌─────────────────┐
   │ classify_intent │ ← IntentClassifier (AI)
   └────────┬────────┘
            │
            ▼
 ┌───────────────────┐
 │ generate_response │ ← ResponseGenerator (AI)
 └────────┬──────────┘
          │
          ▼
┌─────────────────────┐
│ await_approval      │ ← INTERRUPT: ждёт человека
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
 [approve]  [reject]
    │
    ▼
 send_response → Bybit API
```

## Связи между модулями

| Модуль | Зависит от | Использует |
|--------|-----------|------------|
| Telegram Bot | Bridge, Orchestrator | python-telegram-bot |
| Bridge | Orchestrator | tenacity |
| Orchestrator | AI Agents, Bybit Client | langgraph, langchain |
| AI Agents | - | openai, anthropic, groq, etc. |
| Bybit Client | - | bybit-p2p (optional) |
| Database | - | sqlalchemy, alembic |
| FastAPI | Orchestrator, Bybit Client | fastapi, uvicorn |
