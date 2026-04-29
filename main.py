"""Main entry point for Bybit P2P Automation system."""
import logging
import uvicorn
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Initialize and run the application."""
    try:
        # Validate configuration
        config.validate_config()
        logger.info("Configuration validated successfully")
        
        # Import server after config validation
        from server import app
        
        logger.info(f"Starting server on {config.HOST}:{config.PORT}")
        logger.info(f"Testnet mode: {config.BYBIT_TESTNET}")
        logger.info(f"Open http://{config.HOST}:{config.PORT} in your browser")
        
        # Run server
        uvicorn.run(
            app,
            host=config.HOST,
            port=config.PORT,
            log_level="info" if config.DEBUG else "warning"
        )
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please create a .env file based on .env.example")
        return 1
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
