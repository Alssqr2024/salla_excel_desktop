# app/services/image_finder/providers/serper.py
import httpx
from typing import Any, Dict, List

from ..config import SERPER_API_KEY, REQUEST_TIMEOUT
from ..logger import logger


class SerperProvider:
    """مزود بحث Google عبر Serper.dev."""

    SEARCH_URL = "https://google.serper.dev/search"
    IMAGES_URL = "https://google.serper.dev/images"

    def __init__(self, api_key=None):
        self.api_key = api_key or SERPER_API_KEY
        if not self.api_key:
            logger.warning("SERPER_API_KEY غير مضبوط")

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    def search_product(self, query: str, num: int = 10) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.post(
                    self.SEARCH_URL,
                    headers=self._headers(),
                    json={"q": query, "num": num, "gl": "sa", "hl": "ar"},
                )
                if resp.status_code != 200:
                    logger.warning("Serper search failed: %s", resp.status_code)
                    return []
                data = resp.json()
                return data.get("organic", [])
        except Exception as exc:
            logger.exception("Serper search exception: %s", exc)
            return []

    def search_images(self, query: str, num_results: int = 20) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.post(
                    self.IMAGES_URL,
                    headers=self._headers(),
                    json={"q": query, "num": num_results, "gl": "sa", "hl": "ar"},
                )
                if resp.status_code != 200:
                    logger.warning("Serper images failed: %s", resp.status_code)
                    return []
                data = resp.json()
                images = data.get("images", [])
                normalized = []
                for img in images:
                    normalized.append({
                        "imageUrl": img.get("imageUrl"),
                        "image_url": img.get("imageUrl"),
                        "title": img.get("title", ""),
                        "source": img.get("source", ""),
                        "sourceUrl": img.get("link", ""),
                        "source_url": img.get("link", ""),
                        "width": img.get("imageWidth"),
                        "height": img.get("imageHeight"),
                    })
                return normalized
        except Exception as exc:
            logger.exception("Serper images exception: %s", exc)
            return []
