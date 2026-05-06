"""Message processor with security, rate limiting, and validation."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re
import os
import time
import hashlib
import random
from loguru import logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ...database.session import get_db
from ...database.models import BlacklistEntry, ViolationHistory, ABTestConfig, WebhookEvent


@dataclass
class ProcessingResult:
    should_process: bool
    response: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    log_level: str = "info"
    variant: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_process": self.should_process,
            "response": self.response,
            "metadata": self.metadata,
            "log_level": self.log_level,
            "variant": self.variant,
        }


SENSITIVE_PATTERNS = [
    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    r'\b(?:\d[ -]*?){13,16}\b',
    r'\b\d{2}[/-]?\d{2}[/-]?\d{4}\b',
    r'\b(?:password|passwd|pwd)\s*[:=]\s*\S+',
    r'\b(?:api[_-]?key|secret|token)\s*[:=]\s*\S+',
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
]

SPAM_INDICATORS = [
    r'(?:buy|sell|trade)\s+(?:crypto|bitcoin|btc|eth)',
    r'(?:click|visit|check)\s+(?:this|here|link)',
    r'(?:free|gratis|bonus)\s+(?:money|cash|coins)',
    r'(?:telegram|whatsapp|signal)\s+(?:group|channel)',
    r'\b(?:scam|fraud|fake)\b',
    r'(?:limited|urgent|hurry)\s+(?:time|offer|deal)',
]

SUSPICIOUS_PATTERNS = [
    r'(?:send|transfer|give)\s+(?:money|funds|crypto)',
    r'(?:double|triple|multiply)\s+(?:your|my)\s+(?:money|crypto)',
    r'(?:guaranteed|risk[- ]?free)\s+(?:profit|return)',
    r'(?:investment|invest)\s+(?:opportunity|scheme)',
]


class MessageProcessor:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._in_memory_rates: Dict[str, List[float]] = {}
        self._ab_test_cache: Dict[str, Dict[str, Any]] = {}
        self._blacklist_cache: Dict[str, datetime] = {}
        self._blacklist_last_refresh: Optional[datetime] = None
        
        self.max_message_length = 2000
        self.min_message_length = 1
        self.rate_limit_window = 60
        self.rate_limit_max = 15
        self.blacklist_cache_ttl = 300
        self.max_violations_before_ban = 5
        
        self._initialized = False

    async def init_redis(self) -> bool:
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available, using in-memory rate limiting")
            return False
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await self.redis_client.ping()
            logger.info("Redis connection established for rate limiting")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, falling back to in-memory")
            self.redis_client = None
            return False

    async def initialize(self) -> None:
        if self._initialized:
            return
        
        await self.init_redis()
        await self._refresh_blacklist_cache()
        self._initialized = True
        logger.info("MessageProcessor initialized")

    async def process_message(
        self,
        user_id: str,
        message: str,
        username: Optional[str] = None,
        user_data: Optional[Dict] = None,
    ) -> ProcessingResult:
        if not self._initialized:
            await self.initialize()
        
        metadata: Dict[str, Any] = {
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.utcnow().isoformat(),
            "checks_passed": [],
            "checks_failed": [],
        }
        
        start_time = time.time()
        
        try:
            if not message or not message.strip():
                return ProcessingResult(
                    should_process=False,
                    response="Empty message not allowed",
                    metadata={**metadata, "reason": "empty_message"},
                    log_level="warning",
                )
            
            if len(message) > self.max_message_length:
                await self._log_violation(
                    user_id, "message_too_long", "low", message, {"length": len(message)}
                )
                return ProcessingResult(
                    should_process=False,
                    response=f"Message too long. Maximum {self.max_message_length} characters.",
                    metadata={**metadata, "reason": "message_too_long", "length": len(message)},
                    log_level="warning",
                )
            
            blacklist_result = await self._check_blacklist_db(user_id, message)
            if not blacklist_result.should_process:
                metadata["checks_failed"].append("blacklist")
                await self._send_webhook("blacklist_violation", user_id, {
                    "username": username,
                    "message_preview": message[:100],
                    "violation_type": blacklist_result.metadata.get("violation_type") if blacklist_result.metadata else None,
                })
                return ProcessingResult(
                    should_process=False,
                    response=blacklist_result.response,
                    metadata={**metadata, **(blacklist_result.metadata or {})},
                    log_level="warning",
                )
            metadata["checks_passed"].append("blacklist")
            
            sensitive_result = await self._check_sensitive_content(message)
            if not sensitive_result.should_process:
                metadata["checks_failed"].append("sensitive_content")
                await self._log_violation(
                    user_id, "sensitive_content", "medium", message,
                    {"patterns_found": sensitive_result.metadata.get("patterns_found")}
                )
                return ProcessingResult(
                    should_process=False,
                    response="Message contains sensitive information. Please remove it.",
                    metadata={**metadata, **(sensitive_result.metadata or {})},
                    log_level="warning",
                )
            metadata["checks_passed"].append("sensitive_check")
            
            spam_result = await self._check_spam_patterns(message)
            if not spam_result.should_process:
                metadata["checks_failed"].append("spam_detection")
                await self._log_violation(
                    user_id, "spam_detected", "high", message,
                    {"spam_score": spam_result.metadata.get("spam_score")}
                )
                await self._send_webhook("spam_detected", user_id, {
                    "username": username,
                    "spam_score": spam_result.metadata.get("spam_score"),
                    "message_preview": message[:100],
                })
                return ProcessingResult(
                    should_process=False,
                    response="Message flagged as potential spam.",
                    metadata={**metadata, **(spam_result.metadata or {})},
                    log_level="warning",
                )
            metadata["checks_passed"].append("spam_check")
            
            rate_limit_result = await self._check_rate_limit_redis(user_id)
            if not rate_limit_result.should_process:
                metadata["checks_failed"].append("rate_limit")
                return ProcessingResult(
                    should_process=False,
                    response="Rate limit exceeded. Please wait before sending more messages.",
                    metadata={**metadata, **(rate_limit_result.metadata or {})},
                    log_level="warning",
                )
            metadata["checks_passed"].append("rate_limit")
            
            business_result = await self._check_business_rules(user_id, message, user_data)
            if not business_result.should_process:
                metadata["checks_failed"].append("business_rules")
                return ProcessingResult(
                    should_process=False,
                    response=business_result.response,
                    metadata={**metadata, **(business_result.metadata or {})},
                    log_level="info",
                )
            metadata["checks_passed"].append("business_rules")
            
            variant = await self._get_ab_variant("message_processing", user_id)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            metadata["processing_time_ms"] = processing_time_ms
            
            if variant:
                await self._log_ab_test_result("message_processing", user_id, variant, "processed", processing_time_ms)
            
            return ProcessingResult(
                should_process=True,
                metadata=metadata,
                log_level="info",
                variant=variant,
            )
            
        except Exception as e:
            logger.exception(f"Error processing message for user {user_id}: {e}")
            return ProcessingResult(
                should_process=False,
                response="An error occurred while processing your message.",
                metadata={**metadata, "error": str(e)},
                log_level="error",
            )

    async def _check_blacklist_db(self, user_id: str, message: str) -> ProcessingResult:
        try:
            if self._blacklist_last_refresh:
                cache_age = (datetime.utcnow() - self._blacklist_last_refresh).total_seconds()
                if cache_age > self.blacklist_cache_ttl:
                    await self._refresh_blacklist_cache()
            
            with get_db() as db:
                user_blacklisted = db.query(BlacklistEntry).filter(
                    BlacklistEntry.entry_type == "user",
                    BlacklistEntry.value == user_id,
                    BlacklistEntry.is_active == True,
                    (BlacklistEntry.expires_at == None) | (BlacklistEntry.expires_at > datetime.utcnow())
                ).first()
                
                if user_blacklisted:
                    return ProcessingResult(
                        should_process=False,
                        response="Your account has been restricted.",
                        metadata={"violation_type": "blacklisted_user", "reason": user_blacklisted.reason},
                        log_level="warning",
                    )
                
                message_lower = message.lower()
                word_blacklist = db.query(BlacklistEntry).filter(
                    BlacklistEntry.entry_type == "word",
                    BlacklistEntry.is_active == True,
                    (BlacklistEntry.expires_at == None) | (BlacklistEntry.expires_at > datetime.utcnow())
                ).all()
                
                for entry in word_blacklist:
                    if entry.value.lower() in message_lower:
                        return ProcessingResult(
                            should_process=False,
                            response="Message contains prohibited content.",
                            metadata={
                                "violation_type": "blacklisted_word",
                                "severity": entry.severity,
                                "reason": entry.reason,
                            },
                            log_level="warning",
                        )
                
                pattern_blacklist = db.query(BlacklistEntry).filter(
                    BlacklistEntry.entry_type == "pattern",
                    BlacklistEntry.is_active == True,
                    (BlacklistEntry.expires_at == None) | (BlacklistEntry.expires_at > datetime.utcnow())
                ).all()
                
                for entry in pattern_blacklist:
                    try:
                        if re.search(entry.value, message, re.IGNORECASE):
                            return ProcessingResult(
                                should_process=False,
                                response="Message contains prohibited content.",
                                metadata={
                                    "violation_type": "blacklisted_pattern",
                                    "severity": entry.severity,
                                },
                                log_level="warning",
                            )
                    except re.error:
                        logger.warning(f"Invalid regex pattern in blacklist: {entry.value}")
                        continue
            
            return ProcessingResult(should_process=True)
            
        except Exception as e:
            logger.exception(f"Error checking blacklist: {e}")
            return ProcessingResult(should_process=True)

    async def _refresh_blacklist_cache(self) -> None:
        self._blacklist_last_refresh = datetime.utcnow()

    async def _check_rate_limit_redis(self, user_id: str) -> ProcessingResult:
        current_time = time.time()
        window_start = current_time - self.rate_limit_window
        
        if self.redis_client:
            try:
                key = f"rate_limit:{user_id}"
                
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, self.rate_limit_window)
                
                results = await pipe.execute()
                request_count = results[1]
                
                if request_count >= self.rate_limit_max:
                    retry_after = int(self.rate_limit_window - (current_time - window_start))
                    return ProcessingResult(
                        should_process=False,
                        metadata={
                            "reason": "rate_limited",
                            "request_count": request_count,
                            "max_requests": self.rate_limit_max,
                            "retry_after": retry_after,
                        },
                        log_level="warning",
                    )
                
                return ProcessingResult(
                    should_process=True,
                    metadata={"request_count": request_count + 1},
                )
                
            except Exception as e:
                logger.warning(f"Redis rate limit error: {e}, falling back to in-memory")
        
        if user_id not in self._in_memory_rates:
            self._in_memory_rates[user_id] = []
        
        self._in_memory_rates[user_id] = [
            ts for ts in self._in_memory_rates[user_id] if ts > window_start
        ]
        
        if len(self._in_memory_rates[user_id]) >= self.rate_limit_max:
            return ProcessingResult(
                should_process=False,
                metadata={
                    "reason": "rate_limited",
                    "request_count": len(self._in_memory_rates[user_id]),
                    "max_requests": self.rate_limit_max,
                },
                log_level="warning",
            )
        
        self._in_memory_rates[user_id].append(current_time)
        return ProcessingResult(
            should_process=True,
            metadata={"request_count": len(self._in_memory_rates[user_id])},
        )

    async def _check_sensitive_content(self, message: str) -> ProcessingResult:
        patterns_found = []
        
        for i, pattern in enumerate(SENSITIVE_PATTERNS):
            if re.search(pattern, message, re.IGNORECASE):
                patterns_found.append({
                    "pattern_id": i,
                    "type": self._get_sensitive_type(i),
                })
        
        if patterns_found:
            return ProcessingResult(
                should_process=False,
                metadata={"patterns_found": patterns_found},
                log_level="warning",
            )
        
        return ProcessingResult(should_process=True)

    def _get_sensitive_type(self, pattern_index: int) -> str:
        types = [
            "credit_card",
            "card_number",
            "date_of_birth",
            "password",
            "api_key",
            "email",
        ]
        return types[pattern_index] if pattern_index < len(types) else "unknown"

    async def _check_spam_patterns(self, message: str) -> ProcessingResult:
        spam_score = 0
        detected_indicators = []
        
        message_lower = message.lower()
        
        for pattern in SPAM_INDICATORS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                spam_score += 2
                detected_indicators.append(pattern)
        
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                spam_score += 1
                detected_indicators.append(pattern)
        
        ml_result = await self._check_spam_ml(message)
        if not ml_result.should_process:
            spam_score += 3
            detected_indicators.append("ml_detection")
        
        if spam_score >= 3:
            return ProcessingResult(
                should_process=False,
                metadata={
                    "spam_score": spam_score,
                    "indicators": detected_indicators,
                },
                log_level="warning",
            )
        
        if spam_score > 0:
            return ProcessingResult(
                should_process=True,
                metadata={"spam_score": spam_score, "indicators": detected_indicators},
            )
        
        return ProcessingResult(should_process=True)

    async def _check_spam_ml(self, message: str) -> ProcessingResult:
        return ProcessingResult(should_process=True)

    async def _check_business_rules(
        self, user_id: str, message: str, user_data: Optional[Dict] = None
    ) -> ProcessingResult:
        with get_db() as db:
            violation_count = db.query(ViolationHistory).filter(
                ViolationHistory.user_id == user_id,
                ViolationHistory.detected_at > datetime.utcnow() - timedelta(days=30),
                ViolationHistory.severity.in_(["high", "critical"])
            ).count()
            
            if violation_count >= self.max_violations_before_ban:
                return ProcessingResult(
                    should_process=False,
                    response="Your account has been temporarily restricted due to multiple violations.",
                    metadata={"reason": "too_many_violations", "violation_count": violation_count},
                    log_level="warning",
                )
        
        if user_data:
            if user_data.get("banned"):
                return ProcessingResult(
                    should_process=False,
                    response="Your account is banned.",
                    metadata={"reason": "banned"},
                )
            
            if user_data.get("restricted"):
                return ProcessingResult(
                    should_process=False,
                    response="Your account has restrictions.",
                    metadata={"reason": "restricted"},
                )
        
        return ProcessingResult(should_process=True)

    async def _log_violation(
        self,
        user_id: str,
        violation_type: str,
        severity: str,
        message: str,
        metadata: Dict,
    ) -> None:
        try:
            with get_db() as db:
                violation = ViolationHistory(
                    user_id=user_id,
                    violation_type=violation_type,
                    severity=severity,
                    message_text=message[:500] if message else None,
                    extra_data=metadata,
                )
                db.add(violation)
                logger.info(f"Logged violation: {violation_type} for user {user_id}")
        except Exception as e:
            logger.exception(f"Failed to log violation: {e}")

    async def _send_webhook(self, event_type: str, user_id: str, payload: Dict) -> None:
        try:
            webhook_url = os.getenv("WEBHOOK_URL")
            
            with get_db() as db:
                event = WebhookEvent(
                    event_type=event_type,
                    user_id=user_id,
                    payload=payload,
                    webhook_url=webhook_url,
                    status="pending",
                )
                db.add(event)
            
            if webhook_url:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            webhook_url,
                            json={
                                "event_type": event_type,
                                "user_id": user_id,
                                "timestamp": datetime.utcnow().isoformat(),
                                **payload,
                            },
                            timeout=10,
                        )
                        
                        with get_db() as db:
                            db.query(WebhookEvent).filter(
                                WebhookEvent.id == event.id
                            ).update({
                                "status": "sent" if response.status_code == 200 else "failed",
                                "sent_at": datetime.utcnow(),
                                "error_message": None if response.status_code == 200 else f"HTTP {response.status_code}",
                            })
                            
                except Exception as e:
                    logger.warning(f"Webhook delivery failed: {e}")
                    with get_db() as db:
                        db.query(WebhookEvent).filter(
                            WebhookEvent.id == event.id
                        ).update({
                            "status": "failed",
                            "error_message": str(e),
                        })
                        
        except Exception as e:
            logger.exception(f"Failed to create webhook event: {e}")

    async def _get_ab_variant(self, test_name: str, user_id: str) -> Optional[str]:
        try:
            cache_key = f"{test_name}:{user_id}"
            if cache_key in self._ab_test_cache:
                cached = self._ab_test_cache[cache_key]
                if datetime.utcnow() < cached.get("expires", datetime.min):
                    return cached.get("variant")
            
            with get_db() as db:
                test_config = db.query(ABTestConfig).filter(
                    ABTestConfig.test_name == test_name,
                    ABTestConfig.is_active == True,
                    (ABTestConfig.ended_at == None) | (ABTestConfig.ended_at > datetime.utcnow())
                ).first()
                
                if not test_config:
                    return None
                
                hash_input = f"{test_name}:{user_id}".encode()
                hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
                
                if (hash_value % 100) / 100 < test_config.traffic_split:
                    variant = "A"
                else:
                    variant = "B"
                
                self._ab_test_cache[cache_key] = {
                    "variant": variant,
                    "expires": datetime.utcnow() + timedelta(minutes=5),
                }
                
                return variant
                
        except Exception as e:
            logger.warning(f"Failed to get A/B variant: {e}")
            return None

    async def _log_ab_test_result(
        self, test_name: str, user_id: str, variant: str, result_type: str, processing_time_ms: int
    ) -> None:
        try:
            from ...database.models import ABTestResult
            
            with get_db() as db:
                test_config = db.query(ABTestConfig).filter(
                    ABTestConfig.test_name == test_name,
                    ABTestConfig.is_active == True,
                ).first()
                
                if test_config:
                    result = ABTestResult(
                        test_id=test_config.id,
                        user_id=user_id,
                        variant=variant,
                        result_type=result_type,
                        processing_time_ms=processing_time_ms,
                    )
                    db.add(result)
                    
        except Exception as e:
            logger.warning(f"Failed to log A/B test result: {e}")

    async def cleanup(self) -> None:
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
        
        self._initialized = False

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        try:
            with get_db() as db:
                total_violations = db.query(ViolationHistory).filter(
                    ViolationHistory.user_id == user_id
                ).count()
                
                high_severity_violations = db.query(ViolationHistory).filter(
                    ViolationHistory.user_id == user_id,
                    ViolationHistory.severity.in_(["high", "critical"])
                ).count()
                
                recent_violations = db.query(ViolationHistory).filter(
                    ViolationHistory.user_id == user_id,
                    ViolationHistory.detected_at > datetime.utcnow() - timedelta(days=7)
                ).count()
                
                return {
                    "user_id": user_id,
                    "total_violations": total_violations,
                    "high_severity_violations": high_severity_violations,
                    "recent_violations": recent_violations,
                    "is_high_risk": high_severity_violations >= 3,
                }
                
        except Exception as e:
            logger.exception(f"Failed to get user stats: {e}")
            return {"user_id": user_id, "error": str(e)}

    async def check_rate_limit_status(self, user_id: str) -> Dict[str, Any]:
        current_time = time.time()
        window_start = current_time - self.rate_limit_window
        
        if self.redis_client:
            try:
                key = f"rate_limit:{user_id}"
                request_count = await self.redis_client.zcount(key, window_start, current_time)
                
                return {
                    "user_id": user_id,
                    "current_requests": request_count,
                    "max_requests": self.rate_limit_max,
                    "window_seconds": self.rate_limit_window,
                    "remaining": max(0, self.rate_limit_max - request_count),
                }
            except Exception as e:
                logger.warning(f"Failed to get rate limit status from Redis: {e}")
        
        if user_id in self._in_memory_rates:
            requests = [ts for ts in self._in_memory_rates[user_id] if ts > window_start]
            return {
                "user_id": user_id,
                "current_requests": len(requests),
                "max_requests": self.rate_limit_max,
                "window_seconds": self.rate_limit_window,
                "remaining": max(0, self.rate_limit_max - len(requests)),
            }
        
        return {
            "user_id": user_id,
            "current_requests": 0,
            "max_requests": self.rate_limit_max,
            "window_seconds": self.rate_limit_window,
            "remaining": self.rate_limit_max,
        }


message_processor = MessageProcessor()
