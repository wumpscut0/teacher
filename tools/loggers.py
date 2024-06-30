import logging
from logging.config import dictConfig

dictConfig(
    {
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
            "debug": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": "debug_tools.log",
            }
        },
        "loggers": {
            "errors_tools": {"level": logging.ERROR, "handlers": ["errors"]},
            "info_tools": {"level": logging.INFO, "handlers": ["info"]},
            "debug_tools": {"level": logging.DEBUG, "handlers": ["debug"]},
        },
    }
)


errors_tools = logging.getLogger("errors_tools")
info_tools = logging.getLogger("info_tools")
debug_tools = logging.getLogger("debug_tools")
