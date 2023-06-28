import logging
import logging.config as logging_config
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def get_logging_config(log_dir: Path) -> Dict[str, Any]:

    date = datetime.now().strftime("%Y.%m.%d.%H.%s")
    log_file = log_dir / f"{date}.log"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s.%(msecs)03d | [%(levelname)s] | "
                "%(name)s:(%(filename)s).%(funcName)s(%(lineno)d) | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": log_file,
                "maxBytes": 1024 * 1024 * 10,  # 10 MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": logging.INFO,
            },
        },
    }

    return config


def get_logger(name: str = __name__) -> logging:
    base_dir = Path(name).parent
    log_dir = base_dir / "logs"

    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    config = get_logging_config(log_dir)
    logging_config.dictConfig(config)

    logger = logging.getLogger(name)

    return logger
