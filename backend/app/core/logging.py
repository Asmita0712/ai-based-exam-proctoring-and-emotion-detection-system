"""
Structured logging setup for the backend.

Kept minimal in Phase 0 -- just enough to give every module a
consistent, named logger instead of bare print() statements.
"""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
