# app/services/image_finder/logger.py
import logging
from .config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)
logger.propagate = False

__all__ = ["logger"]