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
    },
    "loggers": {
        "errors_alt_telegram": {"level": logging.ERROR, "handlers": ["errors"]},
        "info_alt_telegram": {"level": logging.DEBUG, "handlers": ["info"]},
    },
}

dictConfig(config)

telegram_alt_errors = logging.getLogger("errors_alt_telegram")
telegram_alt_info = logging.getLogger("info_alt_telegram")
