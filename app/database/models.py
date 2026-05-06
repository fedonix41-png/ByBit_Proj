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
    side = Column(String(10), nullable=False)
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
    sender = Column(String(20), nullable=False)
    text = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    entities = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(20), nullable=False)
    
    order = relationship("Order", back_populates="messages")

class Decision(Base):
    __tablename__ = 'decisions'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), index=True, nullable=False)
    decision_type = Column(String(50), nullable=False)
    approved = Column(Boolean, nullable=False)
    proposed_action = Column(Text, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_flags = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    decided_by = Column(String(50), nullable=False)
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
    status = Column(String(50), nullable=False)
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
    agent_type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_info = Column(JSON, nullable=True)


class BlacklistEntry(Base):
    """Blacklist for words, patterns, and users."""
    __tablename__ = 'blacklist_entries'
    
    id = Column(Integer, primary_key=True)
    entry_type = Column(String(20), nullable=False)
    value = Column(String(500), nullable=False)
    reason = Column(Text, nullable=True)
    severity = Column(String(20), default='medium')
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    meta_info = Column(JSON, nullable=True)


class ViolationHistory(Base):
    """History of user violations."""
    __tablename__ = 'violation_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), index=True, nullable=False)
    username = Column(String(100), nullable=True)
    violation_type = Column(String(50), nullable=False)
    severity = Column(String(20), default='medium')
    message_text = Column(Text, nullable=True)
    action_taken = Column(String(50), nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)


class ABTestConfig(Base):
    """A/B test configurations."""
    __tablename__ = 'ab_test_configs'
    
    id = Column(Integer, primary_key=True)
    test_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    variant_a = Column(JSON, nullable=False)
    variant_b = Column(JSON, nullable=False)
    traffic_split = Column(Float, default=0.5)
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)


class ABTestResult(Base):
    """A/B test results."""
    __tablename__ = 'ab_test_results'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('ab_test_configs.id'), nullable=False)
    user_id = Column(String(100), nullable=False)
    variant = Column(String(10), nullable=False)
    result_type = Column(String(50), nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)
    
    test = relationship("ABTestConfig")


class WebhookEvent(Base):
    """Webhook events for notifications."""
    __tablename__ = 'webhook_events'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), default='medium')
    user_id = Column(String(100), nullable=True)
    payload = Column(JSON, nullable=False)
    webhook_url = Column(String(500), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending')
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScreenshotHash(Base):
    """Hash storage for duplicate screenshot detection."""
    __tablename__ = 'screenshot_hashes'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), index=True, nullable=False)
    image_hash = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order")
