"""Logging configuration helpers.

Provides a single :func:`configure_logging` entry point used by the CLI so that
log level and format are consistent across the package.
"""

from __future__ import annotations

import json
import logging


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str = "INFO", *, json_format: bool = False) -> None:
    """Configure the root logger for the application.

    Args:
        level: A logging level name such as ``"INFO"`` or ``"DEBUG"``.
        json_format: When true, emit structured JSON log lines instead of the
            default human-readable format.
    """
    handler = logging.StreamHandler()
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
