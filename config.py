"""Configuration module for P2P automation system."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    TELEGRAM_BOT_TOKEN: str = ""
    
    BYBIT_API_KEY: str = ""
    BYBIT_API_SECRET: str = ""
    BYBIT_TESTNET: bool = True
    USE_MOCK_DATA: bool = False
    
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    USE_AI_MOCK: bool = False
    
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_AUDIO_MODEL: str = "whisper-1"
    OPENAI_VISION_MODEL: str = "gpt-4o"
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    DB_PATH: Path = Path("data/checkpoints.db")
    
    MAX_CONVERSATION_HISTORY: int = 20
    INTENT_CONFIDENCE_THRESHOLD: float = 0.7
    AI_PROVIDER: str = "openrouter"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True

    MESSAGE_MAX_LENGTH: int = 2000
    RATE_LIMIT_WINDOW: int = 60
    RATE_LIMIT_MAX: int = 15
    RATE_LIMIT_DEFAULT_MAX: int = 100
    RATE_LIMIT_DEFAULT_WINDOW: int = 60
    BLACKLIST_CACHE_TTL: int = 300
    MAX_VIOLATIONS_BEFORE_BAN: int = 5

    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_ENABLED: bool = False

    SPAM_DETECTION_ENABLED: bool = True
    SPAM_DETECTION_THRESHOLD: float = 0.7

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15
    PASSWORD_MIN_LENGTH: int = 8
    REQUIRE_PASSWORD_UPPERCASE: bool = True
    REQUIRE_PASSWORD_DIGIT: bool = True

    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    CORS_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 86400

    @property
    def db_path(self) -> Path:
        return Path(__file__).parent / self.DB_PATH


settings = Settings()

BYBIT_API_KEY = settings.BYBIT_API_KEY
BYBIT_API_SECRET = settings.BYBIT_API_SECRET
BYBIT_TESTNET = settings.BYBIT_TESTNET
USE_MOCK_DATA = settings.USE_MOCK_DATA
USE_AI_MOCK = settings.USE_AI_MOCK
AI_PROVIDER = settings.AI_PROVIDER
OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
OPENROUTER_MODEL = settings.OPENROUTER_MODEL
HOST = settings.HOST
PORT = settings.PORT
DEBUG = settings.DEBUG
DB_PATH = settings.db_path
REDIS_URL = settings.REDIS_URL
REDIS_ENABLED = settings.REDIS_ENABLED
WEBHOOK_URL = settings.WEBHOOK_URL
MESSAGE_MAX_LENGTH = settings.MESSAGE_MAX_LENGTH

DB_PATH.parent.mkdir(exist_ok=True)


def validate_config():
    """Validate that required configuration is present."""
    print("🔧 CONFIG VALIDATION")
    print(f"   USE_MOCK_DATA: {USE_MOCK_DATA}")
    print(f"   USE_AI_MOCK: {USE_AI_MOCK}")
    print(f"   BYBIT_TESTNET: {BYBIT_TESTNET}")
    print()
    
    if USE_AI_MOCK:
        print("🤖 AI MOCK MODE: Using mock AI agents instead of real API calls.")
        print("   This is safe for development and testing.")
    else:
        print(f"🤖 AI LIVE MODE: Using provider '{settings.AI_PROVIDER}'")
        if settings.AI_PROVIDER == "openrouter":
            if not settings.OPENROUTER_API_KEY:
                print("⚠️  WARNING: OPENROUTER_API_KEY not set. AI features disabled.")
            else:
                print(f"   OpenRouter model: {settings.OPENROUTER_MODEL}")
        elif not settings.OPENAI_API_KEY:
            print("⚠️  WARNING: OPENAI_API_KEY not set. Voice/image features disabled.")

    if USE_MOCK_DATA:
        print("⚠️  BYBIT MOCK MODE: No real Bybit API calls will be made.")
        print("   This is safe but limited. Use testnet API for full functionality.")
        return

    if not BYBIT_API_KEY or not BYBIT_API_SECRET:
        raise ValueError(
            "\n❌ MISSING BYBIT API CREDENTIALS\n"
            "\nFor safe development, you MUST use Bybit TESTNET API:\n"
            "1. Go to https://testnet.bybit.com/\n"
            "2. Create account and get API keys\n"
            "3. Set BYBIT_API_KEY and BYBIT_API_SECRET in .env\n"
            "4. Ensure BYBIT_TESTNET=True\n"
            "\nTestnet is completely isolated from real funds!\n"
            "\nAlternatively, set USE_MOCK_DATA=True for limited mock testing."
        )

    if not BYBIT_TESTNET:
        print("⚠️  WARNING: BYBIT_TESTNET=False - Using PRODUCTION API!")
        print("   This will affect REAL funds. Make sure you know what you're doing!")
        print("   For development, always use BYBIT_TESTNET=True")
