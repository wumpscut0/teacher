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
            "filename": "errors_alt_telegram.log",
        },
        "info": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "info_alt_telegram.log",
        },
        "debug": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "debug_alt_telegram.log",
        },
    },
    "loggers": {
        "errors_alt_telegram": {"level": logging.ERROR, "handlers": ["errors"]},
        "info_alt_telegram": {"level": logging.INFO, "handlers": ["info"]},
        "debug_alt_telegram": {"level": logging.DEBUG, "handlers": ["debug"]},
    },
}

dictConfig(config)

errors_alt_telegram = logging.getLogger("errors_alt_telegram")
info_alt_telegram = logging.getLogger("info_alt_telegram")
debug_alt_telegram = logging.getLogger("debug_alt_telegram")
