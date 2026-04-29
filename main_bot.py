"""Main entry point for P2P automation with enhanced Telegram interface."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

log_dir = Path(__file__).parent / "logs"
try:
    log_dir.mkdir(exist_ok=True)
    logger.add(log_dir / "p2p_bot.log", rotation="10 MB", level="DEBUG", encoding="utf-8")
except PermissionError:
    pass


def main():
    logger.info("Starting P2P Automation v2.1 (Enhanced Telegram)")
    
    logger.info("Initializing database...")
    from app.database.session import init_db
    init_db()
    
    logger.info("Initializing Telegram Bot...")
    from app.infrastructure.interface.bot import P2PTelegramBot
    bot = P2PTelegramBot()
    
    logger.info("Starting Telegram Bot...")
    bot.run()


if __name__ == "__main__":
    main()
