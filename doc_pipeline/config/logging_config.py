import logging.config
from typing import Dict, Any
import sys

def configure_logging(level: str = "INFO") -> None:
    """Configure logging with JSON formatting and proper UTC timestamps."""
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "doc_pipeline.utils.logging.CustomJsonFormatter",
                "format": "%(timestamp)s %(level)s %(module)s %(function)s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout
            }
        },
        "loggers": {
            "doc_pipeline": {
                "handlers": ["console"],
                "level": level,
                "propagate": False
            }
        },
        "root": {
            "handlers": ["console"],
            "level": level
        }
    }
    
    logging.config.dictConfig(config)