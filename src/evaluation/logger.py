"""
Logging utility module for the evaluation app.
Provides convenient functions for logging success and error messages.
"""

import logging
from typing import Any, Optional


def get_logger(name: str = 'evaluation') -> logging.Logger:
    """
    Get a logger instance for the specified name.
    
    Args:
        name: The name of the logger (default: 'evaluation')
        
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)


def log_success(message: str, extra_data: Optional[dict] = None, logger_name: str = 'evaluation') -> None:
    """
    Log a success message to the success log file.
    
    Args:
        message: The success message to log
        extra_data: Optional dictionary with additional data to include
        logger_name: The name of the logger to use
    """
    logger = get_logger(logger_name)
    
    if extra_data:
        message = f"{message} | Data: {extra_data}"
    
    logger.info(f"SUCCESS: {message}")


def log_error(message: str, exception: Optional[Exception] = None, extra_data: Optional[dict] = None, logger_name: str = 'evaluation') -> None:
    """
    Log an error message to the error log file.
    
    Args:
        message: The error message to log
        exception: Optional exception object to include
        extra_data: Optional dictionary with additional data to include
        logger_name: The name of the logger to use
    """
    logger = get_logger(logger_name)
    
    if exception:
        message = f"{message} | Exception: {str(exception)}"
    
    if extra_data:
        message = f"{message} | Data: {extra_data}"
    
    logger.error(f"ERROR: {message}")


def log_info(message: str, extra_data: Optional[dict] = None, logger_name: str = 'evaluation') -> None:
    """
    Log an informational message to the success log file.
    
    Args:
        message: The info message to log
        extra_data: Optional dictionary with additional data to include
        logger_name: The name of the logger to use
    """
    logger = get_logger(logger_name)
    
    if extra_data:
        message = f"{message} | Data: {extra_data}"
    
    logger.info(f"INFO: {message}")


def log_warning(message: str, extra_data: Optional[dict] = None, logger_name: str = 'evaluation') -> None:
    """
    Log a warning message to the success log file.
    
    Args:
        message: The warning message to log
        extra_data: Optional dictionary with additional data to include
        logger_name: The name of the logger to use
    """
    logger = get_logger(logger_name)
    
    if extra_data:
        message = f"{message} | Data: {extra_data}"
    
    logger.warning(f"WARNING: {message}")
