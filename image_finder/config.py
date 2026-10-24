# app/services/image_finder/config.py
from config import settings

SERPER_API_KEY = settings.SERPER_API_KEY
REQUEST_TIMEOUT = settings.IMAGE_FINDER_TIMEOUT
MAX_CANDIDATES = settings.IMAGE_FINDER_MAX_CANDIDATES
LOGGER_NAME = "image_finder"
