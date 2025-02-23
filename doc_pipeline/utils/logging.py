import logging
import json
from datetime import datetime, UTC
from typing import Any, Dict
from pythonjsonlogger.json import JsonFormatter
import sys

class CustomJsonFormatter(JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.now(UTC).isoformat()
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['function'] = record.funcName

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomJsonFormatter(
        '%(timestamp)s %(level)s %(module)s %(function)s %(message)s'
    ))
    logger.addHandler(console_handler)
    
    return logger

# Create default logger
logger = setup_logger("doc_pipeline")