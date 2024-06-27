import logging
from logging.config import dictConfig

config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"default": {"format": "%(asctime)s | %(levelname)s | %(message)s"}},
    "handlers": {
        "errors": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "errors_tools.log",
        },
        "info": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "info_tools.log",
        },
    },
    "loggers": {
        "errors_redis_tools": {"level": logging.ERROR, "handlers": ["errors"]},
        "info_redis_tools": {"level": logging.DEBUG, "handlers": ["info"]},
    },
}

dictConfig(config)

tools_errors = logging.getLogger("errors_redis_tools")
tools_info = logging.getLogger("info_redis_tools")
