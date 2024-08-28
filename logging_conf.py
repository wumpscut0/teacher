from logging.config import dictConfig

dictConfig({
	"version": 1,
	"disable_existing_loggers": False,
	"formatters": {
		"verbose": {
			"format": "===LOG===\n%(asctime)s %(levelname)s %(message)s\n===LOG===",
			"datefmt": "%d.%m:%Y %H:%M:%S"
		}
	},
	"handlers": {
		"stdout": {
			"class": "logging.StreamHandler",
			"formatter": "verbose"
		}
	},
	"loggers": {
		"": {
		"level": "DEBUG",
		"handlers": ["stdout"]
		}
	}
})