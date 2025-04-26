# src/utils/__init__.py
# Empty file to make utils a package

# src/utils/logger.py
import logging
import sys
import os
from datetime import datetime


class AppLogger:
    """Comprehensive terminal logger"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._setup_logger()

    def _setup_logger(self):
        """Setup detailed logging configuration"""
        self.logger = logging.getLogger("SignalAnalysisApp")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate log messages
        if self.logger.handlers:
            self.logger.handlers.clear()

        try:
            # Get the project root directory (where src is located)
            current_dir = os.path.dirname(
                os.path.abspath(__file__)
            )  # Get the directory of this file
            project_root = os.path.dirname(
                os.path.dirname(current_dir)
            )  # Go up two levels

            # Create logs directory in project root
            log_dir = os.path.join(project_root, "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Create log file with timestamp
            log_file = os.path.join(
                log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )

            # Create and configure file handler
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

            # Create and configure console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter("%(levelname)-8s | %(message)s")
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # Log startup messages
            self.logger.info("=== Logging Started ===")
            self.logger.info(f"Log file created at: {log_file}")
            self.logger.info(f"Project root: {project_root}")

        except Exception as e:
            # If file logging fails, at least set up console logging
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(
                logging.DEBUG
            )  # Show everything in console if file logging fails
            console_formatter = logging.Formatter("%(levelname)-8s | %(message)s")
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            self.logger.error(f"Failed to set up file logging: {str(e)}")

    def get_logger(self):
        """Get the configured logger"""
        return self.logger


# Create logger instance
logger_instance = AppLogger()
app_logger = logger_instance.get_logger()

# Export the logger
__all__ = ["app_logger"]
