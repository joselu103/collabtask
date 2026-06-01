# src/shared/logging_config.py
import logging
from typing import Any

import structlog

from src.settings.settings import get_settings


def _service_name_processor(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()

    event_dict["service"] = settings.app_name
    return event_dict


def configure_logging():
    settings = get_settings()

    renderer = (
        structlog.dev.ConsoleRenderer()
        if settings.debug
        else structlog.processors.JSONRenderer()
    )

    min_level = logging.DEBUG if settings.debug else logging.INFO

    logging.getLogger("src").setLevel(min_level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            _service_name_processor,
            structlog.processors.TimeStamper(utc=True),
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(min_level),
    )
