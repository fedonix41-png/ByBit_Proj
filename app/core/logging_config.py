"""Unified logging configuration using Loguru."""
import sys
import os
from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Configure loguru logger for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log rotation
    """
    logger.remove()
    
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    if log_file:
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            logger.add(
                log_file,
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                rotation="10 MB",
                retention="7 days",
                compression="gz",
                encoding="utf-8"
            )
            logger.info(f"File logging enabled: {log_file}")
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot create log file '{log_file}': {e}. Using console only.")
    
    import logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            logger.opt(depth=6).log(level, record.getMessage())
    
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    for lib in ["httpx", "httpcore", "uvicorn", "asyncio"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    logger.info(f"Logging initialized: level={log_level}, file={log_file}")


def get_logger(name: str = None):
    """Get logger instance.
    
    Args:
        name: Optional module name for context
    
    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger
