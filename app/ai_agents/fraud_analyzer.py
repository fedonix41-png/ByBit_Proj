"""Fraud risk analysis AI agent."""
import json
import logging
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)

BIN_CODES = {
    '4276': 'Сбербанк',
    '5469': 'Сбербанк', 
    '4279': 'Сбербанк',
    '2200': 'Сбербанк',
    '2202': 'Тинькофф',
    '2204': 'Тинькофф',
    '5536': 'Тинькофф',
    '5537': 'Тинькофф',
    '4222': 'Тинькофф',
    '2205': 'Альфа-Банк',
    '4154': 'Альфа-Банк',
    '4230': 'Альфа-Банк',
    '5213': 'Альфа-Банк',
    '2203': 'ВТБ',
    '4272': 'ВТБ',
    '5278': 'ВТБ',
    '4341': 'Райффайзен',
    '4345': 'Райффайзен',
    '5264': 'Райффайзен',
}

BANK_ALIASES = {
    'сбер': 'Сбербанк',
    'сбербанк': 'Сбербанк',
    'sberbank': 'Сбербанк',
    'тинькофф': 'Тинькофф',
    'tinkoff': 'Тинькофф',
    'альфа': 'Альфа-Банк',
    'альфа-банк': 'Альфа-Банк',
    'alfa': 'Альфа-Банк',
    'alfabank': 'Альфа-Банк',
    'втб': 'ВТБ',
    'vtb': 'ВТБ',
    'райффайзен': 'Райффайзен',
    'raiffeisen': 'Райффайзен',
}


class FraudAnalyzer(BaseAIAgent):
    """Analyze fraud risk for P2P transactions."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._db_session = None
    
    def set_db_session(self, session):
        """Set database session for duplicate checking."""
        self._db_session = session
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze fraud risk.
        
        Args:
            input_data: {
                "payment_data": {
                    "amount": 10000,
                    "currency": "RUB",
                    "card_number": "1234****5678",
                    "timestamp": "2024-01-15 14:30",
                    "bank": "Сбербанк"
                },
                "order_data": {
                    "order_id": "ORD123",
                    "expected_amount": 10000,
                    "currency": "RUB",
                    "created_at": "2024-01-15 14:00",
                    "expected_bank": "Сбербанк",
                    "expected_card_number": "1234****5678",
                    "expected_phone": "+79001234567"
                },
                "counterparty_history": {
                    "total_trades": 5,
                    "successful_trades": 5,
                    "disputes": 0
                },
                "screenshot_path": "/path/to/screenshot.png",
                "parsed_screenshot": {
                    "card_number": "1234****5678",
                    "amount": 10000
                }
            }
        
        Returns:
            {
                "risk_score": 0.15,
                "risk_level": "low",
                "flags": [],
                "checks": {
                    "amount_match": {"passed": true, "score": 1.0, "flags": [], "details": ""},
                    ...
                },
                "recommendation": "approve"
            }
        """
        payment_data = input_data.get("payment_data", {})
        order_data = input_data.get("order_data", {})
        counterparty_history = input_data.get("counterparty_history", {})
        screenshot_path = input_data.get("screenshot_path")
        parsed_screenshot = input_data.get("parsed_screenshot", {})
        
        rule_checks = self._rule_based_checks(
            payment_data, order_data, screenshot_path, parsed_screenshot
        )
        
        ai_analysis = await self._ai_analysis(payment_data, order_data, counterparty_history, rule_checks)
        
        final_score = self._calculate_final_score(rule_checks, ai_analysis)
        
        if screenshot_path and self._db_session:
            await self._save_screenshot_hash(screenshot_path, order_data.get("order_id"))
        
        return {
            **ai_analysis,
            "risk_score": final_score,
            "risk_level": self._get_risk_level(final_score),
            "checks": rule_checks,
            "recommendation": self._get_recommendation(final_score)
        }
    
    def _rule_based_checks(self, payment_data: Dict, order_data: Dict, 
                           screenshot_path: Optional[str] = None,
                           parsed_screenshot: Dict = None) -> Dict[str, Dict]:
        """Perform all rule-based checks."""
        checks = {}
        
        checks["amount_match"] = self._check_amount_match(
            payment_data.get("amount"), order_data.get("expected_amount")
        )
        
        checks["card_format_valid"] = self._check_card_format(
            payment_data.get("card_number", "")
        )
        
        checks["timing_reasonable"] = self._check_timing(
            payment_data.get("timestamp"), order_data.get("created_at")
        )
        
        checks["currency_match"] = self._check_currency_match(
            payment_data.get("currency"), order_data.get("currency")
        )
        
        checks["bin_bank_match"] = self._check_bin_bank(
            payment_data.get("card_number", ""), order_data.get("expected_bank")
        )
        
        checks["recipient_match"] = self._check_recipient_match(
            parsed_screenshot or {}, order_data
        )
        
        checks["duplicate_check"] = self._check_duplicate(
            screenshot_path, order_data.get("order_id")
        )
        
        checks["metadata_check"] = self._check_metadata(
            screenshot_path, payment_data.get("timestamp")
        )
        
        return checks
    
    def _check_amount_match(self, payment_amount: Optional[float], 
                           expected_amount: Optional[float]) -> Dict[str, Any]:
        """Check if payment amount matches expected amount."""
        if payment_amount is None or expected_amount is None:
            return {
                "passed": False,
                "score": 0.0,
                "flags": ["missing_amount_data"],
                "details": "Amount data is missing"
            }
        
        diff = abs(payment_amount - expected_amount)
        if diff < 1.0:
            return {
                "passed": True,
                "score": 1.0,
                "flags": [],
                "details": f"Amount matches: {payment_amount} RUB"
            }
        elif diff < 10:
            return {
                "passed": True,
                "score": 0.7,
                "flags": ["amount_slight_mismatch"],
                "details": f"Small difference: {diff} RUB"
            }
        else:
            return {
                "passed": False,
                "score": 0.0,
                "flags": ["amount_mismatch"],
                "details": f"Amount mismatch: expected {expected_amount}, got {payment_amount}"
            }
    
    def _check_card_format(self, card_number: str) -> Dict[str, Any]:
        """Check if card number format is valid."""
        if not card_number:
            return {
                "passed": False,
                "score": 0.0,
                "flags": ["missing_card_number"],
                "details": "Card number is missing"
            }
        
        has_mask = "****" in card_number or "*" * 4 in card_number
        min_length = len(card_number.replace("*", "").replace(" ", "")) >= 8
        
        if has_mask and min_length:
            return {
                "passed": True,
                "score": 1.0,
                "flags": [],
                "details": f"Card format valid: {card_number}"
            }
        elif len(card_number) >= 13:
            return {
                "passed": True,
                "score": 0.8,
                "flags": ["card_format_unusual"],
                "details": f"Card has unusual format: {card_number}"
            }
        else:
            return {
                "passed": False,
                "score": 0.2,
                "flags": ["card_format_invalid"],
                "details": f"Card format invalid: {card_number}"
            }
    
    def _check_timing(self, payment_timestamp: Optional[str], 
                     order_created_at: Optional[str]) -> Dict[str, Any]:
        """Check if payment timing is reasonable."""
        if not payment_timestamp or not order_created_at:
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": "Timing data incomplete, skipping check"
            }
        
        try:
            payment_time = self._parse_datetime(payment_timestamp)
            order_time = self._parse_datetime(order_created_at)
            time_diff = (payment_time - order_time).total_seconds()
            
            if time_diff < 0:
                return {
                    "passed": False,
                    "score": 0.0,
                    "flags": ["payment_before_order"],
                    "details": f"Payment before order creation: {time_diff}s"
                }
            elif time_diff < 60:
                return {
                    "passed": False,
                    "score": 0.3,
                    "flags": ["payment_too_fast"],
                    "details": f"Payment too fast: {time_diff}s"
                }
            elif time_diff > 86400:
                return {
                    "passed": False,
                    "score": 0.4,
                    "flags": ["payment_too_late"],
                    "details": f"Payment too late: {time_diff/3600:.1f}h"
                }
            else:
                return {
                    "passed": True,
                    "score": 1.0,
                    "flags": [],
                    "details": f"Timing reasonable: {time_diff/60:.1f} min"
                }
        except Exception as e:
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": f"Could not parse timing: {e}"
            }
    
    def _check_currency_match(self, payment_currency: Optional[str], 
                              order_currency: Optional[str]) -> Dict[str, Any]:
        """Check if currencies match."""
        if not payment_currency or not order_currency:
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": "Currency data incomplete"
            }
        
        if payment_currency.upper() == order_currency.upper():
            return {
                "passed": True,
                "score": 1.0,
                "flags": [],
                "details": f"Currency matches: {payment_currency}"
            }
        else:
            return {
                "passed": False,
                "score": 0.0,
                "flags": ["currency_mismatch"],
                "details": f"Currency mismatch: expected {order_currency}, got {payment_currency}"
            }
    
    def _check_bin_bank(self, card_number: str, expected_bank: Optional[str]) -> Dict[str, Any]:
        """
        Check if card BIN matches expected bank.
        
        BIN (Bank Identification Number) = first 6-8 digits of card number.
        Compares bank from BIN with expected bank from order.
        """
        if not card_number or not expected_bank:
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": "BIN check skipped: missing data"
            }
        
        clean_card = card_number.replace(" ", "").replace("*", "0")
        
        detected_bank = None
        for bin_code, bank_name in BIN_CODES.items():
            if clean_card.startswith(bin_code):
                detected_bank = bank_name
                break
        
        if not detected_bank:
            return {
                "passed": True,
                "score": 0.7,
                "flags": ["bin_unknown"],
                "details": f"BIN not in known codes: {clean_card[:6]}"
            }
        
        expected_normalized = BANK_ALIASES.get(expected_bank.lower(), expected_bank)
        
        if detected_bank == expected_normalized:
            return {
                "passed": True,
                "score": 1.0,
                "flags": [],
                "details": f"Bank matches: {detected_bank}"
            }
        else:
            return {
                "passed": False,
                "score": 0.0,
                "flags": ["bin_bank_mismatch"],
                "details": f"Bank mismatch: expected {expected_bank}, BIN shows {detected_bank}"
            }
    
    def _check_recipient_match(self, parsed_data: Dict, expected_data: Dict) -> Dict[str, Any]:
        """
        Check if recipient details from screenshot match expected.
        
        Compares card number, bank, and phone from screenshot
        with expected values from order.
        """
        if not parsed_data:
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": "No parsed screenshot data"
            }
        
        flags = []
        score = 1.0
        details = []
        
        expected_card = expected_data.get("expected_card_number", "")
        parsed_card = parsed_data.get("card_number", "")
        
        if expected_card and parsed_card:
            if self._cards_match(parsed_card, expected_card):
                details.append(f"Card matches: {parsed_card}")
            else:
                flags.append("card_number_mismatch")
                score = 0.0
                details.append(f"Card mismatch: expected {expected_card}, got {parsed_card}")
        
        expected_bank = expected_data.get("expected_bank", "")
        parsed_bank = parsed_data.get("bank", "")
        
        if expected_bank and parsed_bank:
            expected_normalized = BANK_ALIASES.get(expected_bank.lower(), expected_bank)
            parsed_normalized = BANK_ALIASES.get(parsed_bank.lower(), parsed_bank)
            
            if expected_normalized == parsed_normalized:
                details.append(f"Bank matches: {parsed_bank}")
            else:
                flags.append("bank_mismatch")
                score = min(score, 0.3)
                details.append(f"Bank mismatch: expected {expected_bank}, got {parsed_bank}")
        
        expected_phone = expected_data.get("expected_phone", "")
        parsed_phone = parsed_data.get("phone", "")
        
        if expected_phone and parsed_phone:
            clean_expected = self._normalize_phone(expected_phone)
            clean_parsed = self._normalize_phone(parsed_phone)
            
            if clean_expected == clean_parsed:
                details.append("Phone matches")
            else:
                flags.append("phone_mismatch")
                score = min(score, 0.5)
                details.append(f"Phone mismatch: expected {expected_phone}, got {parsed_phone}")
        
        return {
            "passed": len(flags) == 0,
            "score": score,
            "flags": flags,
            "details": "; ".join(details) if details else "No comparison data"
        }
    
    def _check_duplicate(self, image_path: Optional[str], order_id: Optional[str]) -> Dict[str, Any]:
        """
        Check if screenshot has been used before.
        
        Computes SHA-256 hash and checks database for duplicates.
        """
        if not image_path:
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": "No screenshot provided"
            }
        
        if not self._db_session:
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": "DB session not available for duplicate check"
            }
        
        try:
            image_hash = self._compute_image_hash(image_path)
            
            from app.database.models import ScreenshotHash

            existing = self._db_session.query(ScreenshotHash).filter(
                ScreenshotHash.image_hash == image_hash
            ).first()
            
            if existing:
                return {
                    "passed": False,
                    "score": 0.0,
                    "flags": ["duplicate_screenshot"],
                    "details": f"Screenshot already used in order {existing.order_id}"
                }
            else:
                return {
                    "passed": True,
                    "score": 1.0,
                    "flags": [],
                    "details": "Screenshot is unique"
                }
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return {
                "passed": True,
                "score": 0.7,
                "flags": ["duplicate_check_error"],
                "details": f"Could not verify uniqueness: {e}"
            }
    
    def _check_metadata(self, image_path: Optional[str], 
                       transaction_date: Optional[str]) -> Dict[str, Any]:
        """
        Check image metadata (EXIF) for anomalies.
        
        Checks:
        - Creation date (should be close to transaction date)
        - Device model (if available)
        - GPS coordinates (if available)
        """
        if not image_path:
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": "No image provided"
            }
        
        if not Path(image_path).exists():
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": "Image file not found"
            }
        
        try:
            exif_data = self._extract_exif(image_path)
            
            if not exif_data:
                return {
                    "passed": True,
                    "score": 1.0,
                    "flags": [],
                    "details": "No EXIF data (common for screenshots)"
                }
            
            flags = []
            score = 1.0
            details = []
            
            create_date = exif_data.get("DateTimeOriginal") or exif_data.get("CreateDate")
            if create_date and transaction_date:
                photo_date = self._parse_exif_datetime(create_date)
                trans_date = self._parse_datetime(transaction_date)
                
                if photo_date:
                    diff_days = abs((photo_date - trans_date).days)
                    
                    if photo_date > datetime.now():
                        flags.append("photo_date_future")
                        score = 0.0
                        details.append("Photo date is in the future!")
                    elif diff_days > 7:
                        flags.append("photo_too_old")
                        score = min(score, 0.5)
                        details.append(f"Photo is {diff_days} days old")
                    else:
                        details.append(f"Photo date: {photo_date.date()}")
            
            device = exif_data.get("Model") or exif_data.get("Make")
            if device:
                details.append(f"Device: {device}")
            
            gps = exif_data.get("GPSInfo")
            if gps:
                details.append("GPS data present")
            
            return {
                "passed": len(flags) == 0,
                "score": score,
                "flags": flags,
                "details": "; ".join(details) if details else "EXIF checked"
            }
            
        except Exception as e:
            logger.error(f"Metadata check failed: {e}")
            return {
                "passed": True,
                "score": 0.8,
                "flags": [],
                "details": f"Could not read metadata: {e}"
            }
    
    def _compute_image_hash(self, image_path: str) -> str:
        """Compute SHA-256 hash of image file."""
        sha256 = hashlib.sha256()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _extract_exif(self, image_path: str) -> Optional[Dict]:
        """Extract EXIF data from image using Pillow."""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if not exif_data:
                    return None
                
                result = {}
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    result[tag_name] = value
                
                return result
        except ImportError:
            logger.warning("Pillow not installed, skipping EXIF extraction")
            return None
        except Exception as e:
            logger.debug(f"Could not extract EXIF: {e}")
            return None
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string in various formats."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d.%m.%Y %H:%M:%S",
            "%d.%m.%Y %H:%M",
        ]
        
        dt_str = dt_str.strip()
        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        
        return datetime.fromisoformat(dt_str)
    
    def _parse_exif_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse EXIF datetime format."""
        try:
            return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        except (ValueError, TypeError):
            return None
    
    def _cards_match(self, card1: str, card2: str) -> bool:
        """Check if two card numbers match (considering masks)."""
        c1 = card1.replace(" ", "").replace("-", "")
        c2 = card2.replace(" ", "").replace("-", "")
        
        if len(c1) != len(c2):
            return False
        
        for i, (ch1, ch2) in enumerate(zip(c1, c2)):
            if ch1 == "*" or ch2 == "*":
                continue
            if ch1 != ch2:
                return False
        
        return True
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        return "".join(filter(str.isdigit, phone))
    
    async def _save_screenshot_hash(self, image_path: str, order_id: Optional[str]):
        """Save screenshot hash to database."""
        if not self._db_session or not image_path or not order_id:
            return
        
        try:
            from app.database.models import ScreenshotHash, Order
            
            image_hash = self._compute_image_hash(image_path)
            
            order = self._db_session.query(Order).filter(
                Order.order_id == order_id
            ).first()
            
            if order:
                hash_record = ScreenshotHash(
                    order_id=order.id,
                    image_hash=image_hash
                )
                self._db_session.add(hash_record)
                self._db_session.commit()
                logger.info(f"Saved screenshot hash for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to save screenshot hash: {e}")
            self._db_session.rollback()
    
    async def _ai_analysis(self, payment_data: Dict, order_data: Dict, 
                          counterparty_history: Dict, rule_checks: Dict) -> Dict[str, Any]:
        """AI-based fraud analysis."""
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_prompt(payment_data, order_data, counterparty_history, rule_checks)
        
        try:
            result = await self.generate(system_prompt, user_prompt, temperature=0.2, json_mode=True)
            parsed = json.loads(result["content"])
            
            logger.info(f"AI fraud analysis: risk_score={parsed.get('ai_risk_score')}")
            
            return {
                "ai_risk_score": parsed.get("ai_risk_score", 0.5),
                "flags": parsed.get("flags", []),
                "explanation": parsed.get("explanation", ""),
                "tokens_used": result.get("tokens", 0),
                "model": result.get("model")
            }
        
        except Exception as e:
            logger.error(f"AI fraud analysis failed: {e}")
            return {
                "ai_risk_score": 0.5,
                "flags": ["ai_analysis_failed"],
                "explanation": f"AI analysis error: {str(e)}",
                "error": str(e)
            }
    
    def _get_system_prompt(self) -> str:
        return """Ты - эксперт по выявлению мошенничества в P2P торговле криптовалютой.

Анализируй данные платежа и определи уровень риска мошенничества.

Красные флаги (высокий риск):
- Несоответствие суммы
- Подозрительное время платежа (слишком быстро или слишком долго)
- Неправильный формат карты
- Несоответствие валюты
- Несоответствие банка по BIN-коду
- Несовпадение реквизитов получателя
- Дубликат скриншота
- Подозрительные метаданные фото (старое фото, дата в будущем)
- История споров у контрагента
- Странные паттерны в данных

Зелёные флаги (низкий риск):
- Точное совпадение суммы
- Разумное время платежа
- Корректный формат данных
- Совпадение банка и реквизитов
- Уникальный скриншот
- Хорошая история контрагента
- Известный банк

Верни JSON:
{
    "ai_risk_score": 0.0-1.0,
    "flags": ["список подозрительных моментов"],
    "explanation": "краткое объяснение оценки риска"
}"""
    
    def _build_prompt(self, payment_data: Dict, order_data: Dict, 
                     counterparty_history: Dict, rule_checks: Dict) -> str:
        prompt = "Данные платежа:\n"
        prompt += json.dumps(payment_data, ensure_ascii=False, indent=2)
        prompt += "\n\nДанные ордера:\n"
        prompt += json.dumps(order_data, ensure_ascii=False, indent=2)
        prompt += "\n\nИстория контрагента:\n"
        prompt += json.dumps(counterparty_history, ensure_ascii=False, indent=2)
        prompt += "\n\nАвтоматические проверки:\n"
        
        checks_summary = {
            name: {"passed": check["passed"], "flags": check["flags"]}
            for name, check in rule_checks.items()
        }
        prompt += json.dumps(checks_summary, ensure_ascii=False, indent=2)
        prompt += "\n\nОцени риск мошенничества."
        return prompt
    
    def _calculate_final_score(self, rule_checks: Dict, ai_analysis: Dict) -> float:
        """Calculate final risk score combining rules and AI."""
        total_score = sum(check.get("score", 1.0) for check in rule_checks.values())
        avg_rule_score = total_score / len(rule_checks) if rule_checks else 0.5
        rule_score = 1.0 - avg_rule_score
        
        ai_score = ai_analysis.get("ai_risk_score", 0.5)
        
        final_score = (ai_score * 0.6) + (rule_score * 0.4)
        
        return round(min(1.0, max(0.0, final_score)), 2)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level."""
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.7:
            return "medium"
        else:
            return "high"
    
    def _get_recommendation(self, risk_score: float) -> str:
        """Get recommendation based on risk score."""
        if risk_score < 0.3:
            return "approve"
        elif risk_score < 0.7:
            return "manual_review"
        else:
            return "reject"
