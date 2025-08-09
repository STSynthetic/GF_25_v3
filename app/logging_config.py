import logging
import os
from typing import Literal


def init_logging() -> None:
    level_name: str = os.getenv("LOG_LEVEL", "INFO").upper()
    level: int = getattr(logging, level_name, logging.INFO)

    format_style: Literal["plain", "json"] = os.getenv("LOG_FORMAT", "plain").lower()  # type: ignore[assignment]

    if format_style == "json":
        fmt = (
            '{"level": "%(levelname)s", '
            '"ts": %(asctime)s, '
            '"msg": "%(message)s", '
            '"logger": "%(name)s"}'
        )
        datefmt = "%Y-%m-%dT%H:%M:%S%z"
    else:
        fmt = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(level=level, format=fmt, datefmt=datefmt)
