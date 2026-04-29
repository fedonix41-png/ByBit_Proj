"""Configuration module for P2P automation system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Bybit API Configuration
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'True').lower() == 'true'
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'False').lower() == 'true'

# AI Configuration
USE_AI_MOCK = os.getenv('USE_AI_MOCK', 'False').lower() == 'true'

# Server Configuration
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', '8000'))
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Database
DB_PATH = Path(__file__).parent / 'data' / 'checkpoints.db'

# Ensure data directory exists
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
        print("🤖 AI LIVE MODE: Using real AI API calls.")

    if USE_MOCK_DATA:
        print("⚠️  BYBIT MOCK MODE: No real Bybit API calls will be made.")
        print("   This is safe but limited. Use testnet API for full functionality.")
        return  # Mock mode doesn't require API keys

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
