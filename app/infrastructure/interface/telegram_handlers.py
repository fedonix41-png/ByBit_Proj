"""
Telegram message handlers with multi-modal support.

Handles text, voice, and photo messages, routing them through
the P2P bridge for processing.
"""
import base64
import os
from typing import Optional, Tuple

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from app.infrastructure.bridge.p2p_bridge import p2p_bridge
from app.infrastructure.handlers.message_processor import message_processor, ProcessingResult
from app.infrastructure.handlers.spam_detector import spam_detector

TEMP_VOICE_PATH = "/tmp/p2p_voice.ogg"
TEMP_IMAGE_PATH = "/tmp/p2p_image.jpg"

PAYMENT_IMAGE_PROMPT = """
Analyze this image. If it appears to be a payment receipt, bank transfer screenshot, or financial transaction proof:
1. Extract: amount, currency, date/time, any visible reference numbers
2. Note: sender/recipient info if visible (partially masked)
3. Assess: does this look like a legitimate payment confirmation?

If not a payment-related image, briefly describe what you see.
Respond concisely in 2-3 sentences.
"""


def _get_vision_client() -> Tuple[Optional[object], Optional[str]]:
    """Get vision client - prefer OpenRouter, fallback to OpenAI."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        from openai import OpenAI
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        ), "openai/gpt-4o"
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        from openai import OpenAI
        return OpenAI(api_key=openai_key), "gpt-4o"
    
    logger.warning("No vision API key configured (OPENROUTER_API_KEY or OPENAI_API_KEY)")
    return None, None


def _get_openai_client():
    """Get OpenAI client from existing AI agents setup."""
    from openai import OpenAI
    from app.config import USE_AI_MOCK
    
    if USE_AI_MOCK:
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, voice features disabled")
        return None
    
    return OpenAI(api_key=api_key)


async def init_message_processor():
    """Initialize message processor with Redis."""
    await message_processor.initialize()
    logger.info("MessageProcessor initialized")


def set_ai_mode(context: ContextTypes.DEFAULT_TYPE, enabled: bool):
    """Enable/disable AI chat mode."""
    context.user_data['ai_mode'] = enabled


async def handle_ai_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI question via OpenRouter."""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    if not context.user_data.get('ai_mode'):
        return
    
    from app.ai_agents.openrouter_adapter import OpenRouterClient
    client = OpenRouterClient()
    
    if not client.is_configured:
        await update.message.reply_text(
            "⚠️ OpenRouter не настроен. Добавьте OPENROUTER_API_KEY в .env"
        )
        return
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    response = await client.generate(
        prompt=user_message,
        system="Ты - помощник для P2P торговли криптовалютой. Отвечай кратко и по делу на русском языке. Если вопрос связан с торговлей, давай практические советы."
    )
    
    await update.message.reply_text(f"🤖 {response}")


async def handle_fraud_check(update: Update, context: ContextTypes.DEFAULT_TYPE, photo_path: str = None):
    """Handle fraud analysis request."""
    from app.ai_agents.fraud_analyzer import FraudAnalyzer
    from app.ai_agents.openrouter_adapter import OpenRouterClient
    
    analyzer = FraudAnalyzer()
    
    analysis_text = None
    
    if photo_path:
        vision_client, vision_model = _get_vision_client()
        
        if vision_client and vision_model:
            try:
                with open(photo_path, "rb") as img_file:
                    base64_image = base64.b64encode(img_file.read()).decode("utf-8")
                
                fraud_prompt = """
Проанализируй это изображение на предмет признаков мошенничества:
1. Проверь, выглядит ли платёж реальным
2. Есть ли признаки подделки (следы редактирования, неестественные элементы)
3. Соответствуют ли данные формату настоящего платёжного документа

Ответь кратко в формате:
- Подозрительные признаки: (список или "нет")
- Вердикт: (реальный/подозрительный/требует проверки)
"""
                
                vision_response = vision_client.chat.completions.create(
                    model=vision_model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": fraud_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }],
                    max_tokens=500
                )
                analysis_text = vision_response.choices[0].message.content.strip()
                logger.info(f"Fraud vision analysis: {analysis_text[:100]}...")
                
            except Exception as e:
                logger.warning(f"Fraud vision analysis failed: {e}")
                analysis_text = "⚠️ Не удалось проанализировать изображение"
        else:
            analysis_text = "⚠️ Vision API не настроен. Добавьте OPENROUTER_API_KEY или OPENAI_API_KEY в .env"
    
    result_msg = "🔍 **Анализ на мошенничество**\n\n"
    if analysis_text:
        result_msg += f"{analysis_text}\n\n"
    else:
        result_msg += "Изображение не предоставлено для анализа.\n\n"
    
    result_msg += "Для полной проверки введите данные платежа командой /check_payment"
    
    await update.message.reply_text(result_msg)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages."""
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    logger.info(f"Text from user {user_id}: {user_message[:50]}...")
    
    processing_result = await message_processor.process_message(
        user_id=str(user_id),
        message=user_message,
        username=username,
        user_data=context.user_data
    )
    
    if not processing_result.should_process:
        logger.warning(f"Message blocked for user {user_id}: {processing_result.metadata}")
        if processing_result.response:
            await update.message.reply_text(processing_result.response)
        return
    
    logger.info(f"Message processed: {processing_result.metadata}")
    
    if context.user_data.get('ai_mode'):
        await handle_ai_question(update, context)
        return
    
    try:
        response = await p2p_bridge.process_text_message(
            user_id=user_id,
            text=user_message,
            username=username
        )
        await _send_response(update, context, response)
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        await update.message.reply_text("❌ Ошибка обработки сообщения")


async def check_spam_ml(message: str) -> bool:
    """Check message for spam using ML. Returns True if spam detected."""
    if not spam_detector.client.is_configured:
        return False
    
    result = await spam_detector.analyze(message)
    return result.is_spam and result.confidence > 0.7


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming voice messages - transcribe and process."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    logger.info(f"Voice from user {user_id}")
    
    openai_client = _get_openai_client()
    if not openai_client:
        await update.message.reply_text("⚠️ Голосовые сообщения не поддерживаются (требуется OpenAI API ключ для Whisper)")
        return
    
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive(TEMP_VOICE_PATH)
        
        with open(TEMP_VOICE_PATH, "rb") as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1"
            )
        
        logger.info(f"Transcribed voice: {transcription.text[:50]}...")
        
        await update.message.reply_text(f"🎤 Распознано: \"{transcription.text}\"")
        
        response = await p2p_bridge.process_voice_message(
            user_id=user_id,
            transcription=transcription.text,
            username=username
        )
        await _send_response(update, context, response)
        
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        await update.message.reply_text("❌ Ошибка обработки голосового сообщения")
    finally:
        if os.path.exists(TEMP_VOICE_PATH):
            os.remove(TEMP_VOICE_PATH)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming photos - analyze and route appropriately."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    logger.info(f"Photo from user {user_id}")
    
    vision_client, vision_model = _get_vision_client()
    
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        os.makedirs("data/photos", exist_ok=True)
        photo_path = f"data/photos/{user_id}_{photo.file_id}.jpg"
        await file.download_to_drive(photo_path)
        
        analysis = None
        if vision_client and vision_model:
            try:
                with open(photo_path, "rb") as img_file:
                    base64_image = base64.b64encode(img_file.read()).decode("utf-8")
                
                vision_response = vision_client.chat.completions.create(
                    model=vision_model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PAYMENT_IMAGE_PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }],
                    max_tokens=300
                )
                analysis = vision_response.choices[0].message.content.strip()
                logger.info(f"Image analysis: {analysis[:100]}...")
            except Exception as e:
                logger.warning(f"Vision analysis failed: {e}")
        
        response = await p2p_bridge.process_photo_with_analysis(
            user_id=user_id,
            photo_path=photo_path,
            analysis=analysis,
            caption=update.message.caption
        )
        await _send_response(update, context, response)
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await update.message.reply_text("❌ Ошибка обработки изображения")


async def _send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, response: dict):
    """Send response back to user."""
    response_type = response.get("response_type", "text")
    message = response.get("message")
    
    if not message:
        return
    
    user_id = update.message.from_user.id
    
    try:
        if response_type == "text":
            await update.message.reply_text(message)
        elif response_type == "audio":
            audio_bytes = response.get("audio_buffer")
            if audio_bytes:
                await update.message.reply_voice(voice=audio_bytes)
            elif message:
                await update.message.reply_text(message)
        elif response_type == "image":
            image_path = response.get("image_path")
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    await update.message.reply_photo(photo=img_file, caption=message)
            elif message:
                await update.message.reply_text(message)
        else:
            if message:
                await update.message.reply_text(message)
                
    except Exception as e:
        logger.error(f"Error sending response to {user_id}: {e}")
