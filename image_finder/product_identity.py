# app/services/image_finder/product_identity.py
import re
from typing import Any, Dict, Iterable, Optional

from .models import ProductIdentity


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_barcode(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\D", "", str(value))


def find_size_tokens(text: str) -> Optional[str]:
    if not text:
        return None
    patterns = [
        r"(\d+(?:[.,]\d+)?\s*(?:ml|mL|cl|l|L|g|kg|mg|oz|مل|لتر|جرام|كغم|كغ))",
        r"(\d+(?:[.,]\d+)?\s*(?:x\s*\d+(?:[.,]\d+)?\s*(?:ml|mL|l|L|g|kg|جرام|مل|لتر)))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def clean_title(title: str) -> str:
    return normalize_text(title).strip(" -")


def _extract_brand(text: str, fallback: str = "") -> str:
    if not text:
        return fallback
    token = re.search(
        r"(?:brand|ماركة|شركة)[:\s]+([A-Za-z\u0600-\u06FF0-9\s-]+)",
        text, flags=re.IGNORECASE
    )
    if token:
        return normalize_text(token.group(1))
    candidates = [
        "nestea", "aqua", "pepsi", "coca cola", "coca-cola",
        "danone", "tropicana", "milo", "nivea",
    ]
    for candidate in candidates:
        if candidate.lower() in text.lower():
            return candidate
    return fallback


def build_identity(barcode: str, results) -> ProductIdentity:
    barcode = normalize_barcode(barcode)
    items = list(results or [])
    if not items:
        return ProductIdentity(barcode=barcode, confidence=0)

    combined_text = " ".join(
        [item.get("title", "") + " " + (item.get("snippet") or "") for item in items]
    )
    title_candidates = [clean_title(item.get("title", "")) for item in items]
    title_candidates = [value for value in title_candidates if value]

    name = ""
    for candidate in title_candidates:
        if barcode in candidate:
            continue
        if any(token in candidate.lower() for token in ["google", "search", "result"]):
            continue
        name = candidate
        break
    if not name and title_candidates:
        name = title_candidates[0]

    brand = ""
    for candidate in title_candidates:
        candidate_lower = candidate.lower()
        if any(keyword in candidate_lower for keyword in ["brand", "ماركة", "شركة"]):
            brand = _extract_brand(candidate)
            if brand:
                break
    if not brand:
        brand = _extract_brand(combined_text, "")

    size = find_size_tokens(combined_text) or find_size_tokens(name) or ""
    volume = ""
    if not size:
        volume = find_size_tokens(combined_text) or ""

    category = ""
    for keyword in ["مياه", "مشروبات", "العناية", "حليب", "خبز", "معلبات", "سكاكر", "مكرونة"]:
        if keyword in combined_text:
            category = keyword
            break

    country = ""
    for keyword in ["السعودية", "الإمارات", "مصر", "قطر", "الأردن", "المملكة"]:
        if keyword in combined_text:
            country = keyword
            break

    confidence = 0
    if name: confidence += 30
    if brand: confidence += 20
    if size: confidence += 15
    if category: confidence += 10
    if country: confidence += 5

    return ProductIdentity(
        barcode=barcode,
        name=name or None,
        brand=brand or None,
        size=size or None,
        volume=volume or None,
        category=category or None,
        country=country or None,
        confidence=min(confidence, 100),
        raw={"results": items, "combined_text": combined_text},
    )
