from __future__ import annotations

import json
import logging
from typing import Any


def configure_logging(level: int = logging.INFO) -> None:
    """Set up basic structured logging at the given level."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


class StructuredLogger:
    """Thin wrapper that emits JSON-formatted log messages."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def info(self, event: str, **fields: Any) -> None:
        self._logger.info(self._serialize(event, **fields))

    def warning(self, event: str, **fields: Any) -> None:
        self._logger.warning(self._serialize(event, **fields))

    def exception(self, event: str, **fields: Any) -> None:
        self._logger.exception(self._serialize(event, **fields))

    @staticmethod
    def _serialize(event: str, **fields: Any) -> str:
        return json.dumps({"event": event, **fields}, default=str, ensure_ascii=False)
