"""Payment proof parser with OCR."""
import json
from loguru import logger
from typing import Dict, Any
from PIL import Image
import pytesseract
from .base_agent import BaseAIAgent

class PaymentParser(BaseAIAgent):
    """Parse payment proof screenshots using OCR + AI."""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse payment screenshot.
        
        Args:
            input_data: {
                "image_path": "/path/to/screenshot.jpg",
                "expected_amount": 10000,
                "expected_currency": "RUB"
            }
        
        Returns:
            {
                "amount": 10000.0,
                "currency": "RUB",
                "card_number": "1234****5678",
                "timestamp": "2024-01-15 14:30",
                "bank": "Сбербанк",
                "confidence": 0.9,
                "raw_text": "OCR text..."
            }
        """
        image_path = input_data.get("image_path")
        expected_amount = input_data.get("expected_amount")
        expected_currency = input_data.get("expected_currency", "RUB")
        
        if not image_path:
            return {"error": "No image_path provided", "confidence": 0.0}
        
        try:
            # Step 1: OCR
            ocr_text = await self._extract_text(image_path)
            logger.debug(f"OCR extracted {len(ocr_text)} characters")
            
            # Step 2: AI parsing
            parsed_data = await self._parse_with_ai(ocr_text, expected_amount, expected_currency)
            
            return {
                **parsed_data,
                "raw_text": ocr_text[:500]  # First 500 chars
            }
        
        except Exception as e:
            logger.error(f"Payment parsing failed: {e}")
            return {
                "error": str(e),
                "confidence": 0.0
            }
    
    async def _extract_text(self, image_path: str) -> str:
        """Extract text from image using Tesseract OCR."""
        try:
            image = Image.open(image_path)
            
            # OCR with Russian and English
            text = pytesseract.image_to_string(image, lang='rus+eng')
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise
    
    async def _parse_with_ai(self, ocr_text: str, expected_amount: float, 
                            expected_currency: str) -> Dict[str, Any]:
        """Parse OCR text using AI to extract structured data."""
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_prompt(ocr_text, expected_amount, expected_currency)
        
        try:
            result = await self.generate(system_prompt, user_prompt, temperature=0.1, json_mode=True)
            parsed = json.loads(result["content"])
            
            logger.debug(f"AI parsed: amount={parsed.get('amount')}, confidence={parsed.get('confidence')}")
            
            return {
                "amount": parsed.get("amount"),
                "currency": parsed.get("currency", expected_currency),
                "card_number": parsed.get("card_number"),
                "timestamp": parsed.get("timestamp"),
                "bank": parsed.get("bank"),
                "confidence": parsed.get("confidence", 0.0),
                "tokens_used": result.get("tokens", 0),
                "model": result.get("model")
            }
        
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            return {
                "amount": None,
                "currency": expected_currency,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _get_system_prompt(self) -> str:
        return """Ты - эксперт по извлечению данных из скриншотов банковских переводов.

Твоя задача - извлечь структурированные данные из OCR текста скриншота платежа.

Извлекай:
1. Сумму платежа (число)
2. Валюту (RUB, USD, EUR и т.д.)
3. Номер карты отправителя (формат: 1234****5678)
4. Время/дату платежа
5. Название банка

Правила:
- Если данные не найдены, возвращай null
- Сумма должна быть числом (float)
- Номер карты маскируй: первые 4 цифры + **** + последние 4
- Дата в формате: YYYY-MM-DD HH:MM
- Confidence: 0.0-1.0 (насколько уверен в данных)

Верни JSON:
{
    "amount": число или null,
    "currency": "RUB" или null,
    "card_number": "1234****5678" или null,
    "timestamp": "2024-01-15 14:30" или null,
    "bank": "Сбербанк" или null,
    "confidence": 0.0-1.0
}"""
    
    def _build_prompt(self, ocr_text: str, expected_amount: float, 
                     expected_currency: str) -> str:
        prompt = f"OCR текст со скриншота:\n{ocr_text}\n\n"
        prompt += f"Ожидаемая сумма: {expected_amount} {expected_currency}\n\n"
        prompt += "Извлеки данные платежа."
        return prompt
