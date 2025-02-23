import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

class Logger:
    
    @staticmethod
    def get(name: str = __name__, level = logging.INFO) -> logging.Logger:
        logger = logging.getLogger(name)
        
        # Clear existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()
        
        logger.setLevel(level)
        
        # Create logs directory with proper permissions
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(mode=0o755, exist_ok=True)
        
        # Configure formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create and configure file handler first
        log_file = log_dir / f'{name}.log'
        fh = RotatingFileHandler(
            log_file,
            mode='a',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger