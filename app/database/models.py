"""Database models for P2P automation."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    ad_id = Column(String(100), nullable=True)
    side = Column(String(10), nullable=False)  # BUY/SELL
    crypto = Column(String(20), nullable=False)
    currency = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)
    counterparty = Column(String(100), nullable=True)
    counterparty_telegram_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    meta_info = Column(JSON, nullable=True)
    
    messages = relationship("Message", back_populates="order", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="order", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="order", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), index=True, nullable=False)
    message_id = Column(String(100), unique=True, nullable=False)
    sender = Column(String(20), nullable=False)  # me/counterparty
    text = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    entities = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(20), nullable=False)  # telegram/bybit
    
    order = relationship("Order", back_populates="messages")

class Decision(Base):
    __tablename__ = 'decisions'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), index=True, nullable=False)
    decision_type = Column(String(50), nullable=False)  # response_approval/risk_approval
    approved = Column(Boolean, nullable=False)
    proposed_action = Column(Text, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_flags = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    decided_by = Column(String(50), nullable=False)  # human/auto
    decided_at = Column(DateTime, default=datetime.utcnow)
    meta_info = Column(JSON, nullable=True)
    
    order = relationship("Order", back_populates="decisions")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), index=True, nullable=False)
    processing_id = Column(String(100), nullable=True, unique=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(50), nullable=False)  # pending/completed/failed
    payment_proof_path = Column(String(500), nullable=True)
    payment_data = Column(JSON, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    meta_info = Column(JSON, nullable=True)
    
    order = relationship("Order", back_populates="transactions")

class AIInteraction(Base):
    __tablename__ = 'ai_interactions'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, index=True, nullable=True)
    agent_type = Column(String(50), nullable=False)  # intent/response/ocr/fraud
    provider = Column(String(50), nullable=False)  # openai/anthropic/local
    model = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_info = Column(JSON, nullable=True)
