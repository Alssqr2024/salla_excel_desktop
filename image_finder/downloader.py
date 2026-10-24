# app/services/image_finder/downloader.py
from pathlib import Path
from urllib.parse import urlparse
import socket

import httpx

from config import settings
from .config import REQUEST_TIMEOUT
from .logger import logger

STORAGE_DIR = Path(settings.STATIC_DIR).parent / "storage" / "product_images"

# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
# ظپظ„طھط± ط§ظ„ظ†ط·ط§ظ‚ط§طھ ط§ظ„ط³ظٹط¦ط©
# â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
_BLACKLISTED_DOMAINS = {
    "medimixegypt.com",
    "www.mymart.com.sa",
    "www.fawq-wasf.com.sa",
    "khod-whaat.com",
    "xpremo.com",
    "tiktok.com",
    "www.tiktok.com",
    "pinterest.",
    "linkedin.com",
    "facebook.com",
    "instagram.com",
}


def _is_blocked_domain(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower()
        return any(b in domain for b in _BLACKLISTED_DOMAINS)
    except Exception:
        return False


def _domain_exists(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.split(":")[0]
        if not domain:
            return False
        socket.gethostbyname(domain)
        return True
    except (socket.gaierror, socket.error):
        return False
    except Exception:
        return True


def _choose_extension(url: str) -> str:
    parsed = urlparse(url)
    path = (parsed.path or "").lower()
    for extension in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        if extension in path:
            return extension
    return ".jpg"


def download_image(barcode: str, image_url: str) -> str | None:
    if not barcode or not image_url:
        return None

    # ظپظ„طھط± ظ…ط³ط¨ظ‚
    if _is_blocked_domain(image_url):
        logger.debug(f"â›” ظ†ط·ط§ظ‚ ظ…ط­ط¸ظˆط±: {image_url[:80]}")
        return None

    if not _domain_exists(image_url):
        logger.debug(f"â›” ظ†ط·ط§ظ‚ ط؛ظٹط± ظ…ظˆط¬ظˆط¯: {image_url[:80]}")
        return None

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(image_url, headers={"User-Agent": "Mozilla/5.0"})

        if resp.status_code != 200:
            logger.warning(
                f"Image request failed: {image_url[:80]} status={resp.status_code}"
            )
            return None

        content_type = resp.headers.get("Content-Type", "").lower()
        if "image" not in content_type and not any(
            ext in image_url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]
        ):
            logger.warning(f"Non-image content-type: {content_type}")
            return None

        if len(resp.content) > 15 * 1024 * 1024:
            logger.warning(f"Image exceeds 15MB for {barcode}")
            return None

        barcode_text = "".join(ch for ch in str(barcode) if ch.isdigit())
        prefix = barcode_text[:2] if len(barcode_text) >= 2 else "00"
        storage_dir = STORAGE_DIR / prefix
        storage_dir.mkdir(parents=True, exist_ok=True)
        extension = _choose_extension(image_url)
        destination = storage_dir / f"{barcode_text}{extension}"

        destination.write_bytes(resp.content)

        if destination.stat().st_size < 1000:
            destination.unlink(missing_ok=True)
            logger.warning(f"Downloaded image too small for {barcode}")
            return None

        return str(destination)
    except httpx.TimeoutException:
        logger.warning(f"âڈ±ï¸ڈ timeout downloading image for {barcode}")
        return None
    except Exception as exc:
        logger.debug(f"ظپط´ظ„ طھط­ظ…ظٹظ„ {barcode}: {type(exc).__name__}")
        return None

