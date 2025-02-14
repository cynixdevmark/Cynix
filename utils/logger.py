import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
import json
from datetime import datetime
from pathlib import Path


class CynixLogger:
    def __init__(
            self,
            name: str,
            log_level: str = "INFO",
            log_file: Optional[str] = None,
            max_bytes: int = 10485760,  # 10MB
            backup_count: int = 5
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Add file handler if log file is specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _format_message(self, message: str, **kwargs) -> str:
        """Format log message with additional context"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            **kwargs
        }
        return json.dumps(log_data)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(self._format_message(message, **kwargs))

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(self._format_message(message, **kwargs))

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(self._format_message(message, **kwargs))


class PerformanceLogger:
    def __init__(self, logger: CynixLogger):
        self.logger = logger
        self.start_time = None

    def start(self, operation: str):
        """Start timing an operation"""
        self.start_time = datetime.utcnow()
        self.operation = operation

    def stop(self, **kwargs):
        """Stop timing and log performance metrics"""
        if not self.start_time:
            return

        duration = (datetime.utcnow() - self.start_time).total_seconds()

        self.logger.info(
            f"Performance metrics for {self.operation}",
            duration=duration,
            operation=self.operation,
            **kwargs
        )

        self.start_time = None


def get_logger(
        name: str,
        log_level: str = "INFO",
        log_file: Optional[str] = None
) -> CynixLogger:
    """Get configured logger instance"""
    return CynixLogger(name, log_level, log_file)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get performance logger instance"""
    logger = get_logger(f"{name}.performance")
    return PerformanceLogger(logger)