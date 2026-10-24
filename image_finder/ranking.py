# app/services/image_finder/ranking.py
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .models import ImageCandidate, ProductIdentity


def normalize_for_match(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def classify_confidence(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def _has_negative_variant(text: str) -> bool:
    negative_markers = [
        "كرتون",
        "كرتونة",
        "حبة",
        "حبات",
        "جملة",
        "عرض",
        "multipack",
        "case",
        "carton",
        "bulk",
        "12 pack",
        "24 pack",
        "48 pack",
    ]
    lowered = normalize_for_match(text)
    return any(marker.lower() in lowered for marker in negative_markers)


def candidate_matches_identity(
    candidate: Dict[str, Any], product: ProductIdentity
) -> bool:
    if not product.name and not product.brand:
        return False

    text = normalize_for_match(
        " ".join(
            str(candidate.get(key) or "")
            for key in ("title", "source", "sourceUrl", "source_url", "link")
        )
    )
    tokens = {
        token
        for token in re.findall(r"[\w\u0600-\u06FF]+", (product.name or "").lower())
        if len(token) >= 3
    }
    matched_tokens = {token for token in tokens if token in text}
    brand_match = bool(product.brand and normalize_for_match(product.brand) in text)
    barcode_match = bool(product.barcode and product.barcode in text)

    if len(tokens) >= 2:
        name_match = len(matched_tokens) >= min(2, len(tokens)) and (
            len(matched_tokens) / len(tokens) >= 0.5
        )
    else:
        name_match = bool(tokens and matched_tokens)

    if len(tokens) < 2:
        return barcode_match or (brand_match and name_match)
    return name_match or (brand_match and bool(matched_tokens))


def is_barcode_graphic(candidate: Dict[str, Any]) -> bool:
    """كشف صور الباركود المُولّدة."""
    image_url = candidate.get("imageUrl") or candidate.get("image_url") or ""
    title = normalize_for_match(candidate.get("title", ""))
    source = normalize_for_match(candidate.get("source", ""))
    parsed = urlparse(image_url)
    domain = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    query = parsed.query.lower()

    barcode_image_domains = (
        "barcode-list.com",
        "barcode-generator.org",
        "online-barcode-generator.net",
        "barcode.tec-it.com",
    )
    if any(
        domain == host or domain.endswith("." + host) for host in barcode_image_domains
    ):
        return True

    if re.search(
        r"(?:barcode|bar_code)[_-]?image|barcodeimage|barcode[-_]?generator", path
    ):
        return True

    has_barcode_label = any(
        marker in title
        for marker in (
            "barcode image",
            "barcode generator",
            "صورة الباركود",
            "باركود المنتج",
        )
    )
    has_barcode_query = any(key in query for key in ("barcode=", "code=", "gtin="))
    return has_barcode_label and (has_barcode_query or "barcode" in path)


def is_definitely_bad(candidate: Dict[str, Any], product: ProductIdentity) -> bool:
    """
    فلتر سريع لا يحتاج AI - استبعد الصور السيئة قبل إرسالها.
    يوفّر ~20% من التوكنات.
    """
    image_url = (candidate.get("imageUrl") or candidate.get("image_url") or "").lower()
    title = (candidate.get("title") or "").lower()

    # 1. صور الباركود
    if is_barcode_graphic(candidate):
        return True

    # 2. نطاقات ممنوعة
    bad_domains = [
        "play.google.com",
        "apps.apple.com",
        "linkedin.com",
        "facebook.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "wikipedia.org/wiki",
    ]
    if any(d in image_url for d in bad_domains):
        return True

    # 3. عناوين تشير لتطبيقات أو صفحات
    bad_title_words = [
        "تطبيق",
        "app store",
        "google play",
        "linkedin",
        "facebook",
        "twitter",
        "الموقع الرسمي",
        "الصفحة الرئيسية",
    ]
    if any(w in title for w in bad_title_words):
        return True

    # 4. صور صغيرة جدًا
    width = candidate.get("width") or candidate.get("imageWidth") or 0
    height = candidate.get("height") or candidate.get("imageHeight") or 0
    if width and height and (width < 150 or height < 150):
        return True

    return False


def score_candidate(
    candidate: Dict[str, Any], product: ProductIdentity
) -> ImageCandidate:
    image_url = candidate.get("imageUrl") or candidate.get("image_url") or ""
    title = candidate.get("title") or ""
    source = candidate.get("source") or ""
    source_url = candidate.get("sourceUrl") or candidate.get("source_url") or ""
    raw_text = f"{title} {source} {image_url} {source_url}"
    normalized = normalize_for_match(raw_text)

    score = 0.0
    reasons: List[str] = []

    if product.name:
        product_words = [
            word
            for word in re.findall(r"[\w\u0600-\u06FF]+", product.name.lower())
            if len(word) >= 3
        ]
        matches = sum(1 for word in product_words if word in normalized)
        if matches:
            score += min(matches * 10, 40)
            reasons.append("Name match")

    if product.brand:
        if normalize_for_match(product.brand) in normalized:
            score += 20
            reasons.append("Brand match")

    if product.size:
        if normalize_for_match(product.size) in normalized:
            score += 20
            reasons.append("Size match")

    if product.category:
        if normalize_for_match(product.category) in normalized:
            score += 15
            reasons.append("Category match")

    barcode = product.barcode
    if barcode and barcode in normalize_for_match(image_url):
        score += 50
        reasons.append("Barcode appears in image URL")
    elif barcode and barcode in normalized:
        score += 30
        reasons.append("Barcode appears in content")

    if source and any(
        domain in source.lower()
        for domain in [
            "amazon.",
            "noon.",
            "namshi.",
            "souq.",
            "jumia.",
            "carrefour.",
            "binh",
        ]
    ):
        score += 10
        reasons.append("Commercial source")

    if source and source.lower().startswith("http"):
        score += 5
        reasons.append("Source provided")

    width = candidate.get("width") or candidate.get("imageWidth")
    height = candidate.get("height") or candidate.get("imageHeight")
    if width and height:
        if width == height:
            score += 5
            reasons.append("Square image")
        if width * height >= 250000:
            score += 5
            reasons.append("Good resolution")

    if _has_negative_variant(raw_text):
        score -= 30
        reasons.append("Negative variant signal")

    if image_url:
        maybe_other_barcode = re.findall(r"(?<!\d)\d{8,14}(?!\d)", image_url)
        if barcode and any(number != barcode for number in maybe_other_barcode):
            score -= 100
            reasons.append("Different barcode in URL")

    identity_match = candidate_matches_identity(candidate, product)
    if identity_match:
        reasons.append("Barcode-derived product identity corroborated")
    else:
        score -= 100
        reasons.append("Product identity not corroborated")

    score = min(100, max(0, score))

    return ImageCandidate(
        image_url=image_url,
        title=title,
        source=source,
        source_url=source_url,
        score=score,
        reasons=reasons,
        width=width,
        height=height,
        confidence=classify_confidence(score),
        identity_match=identity_match,
        raw=candidate,
    )


def rank_candidates(
    product: ProductIdentity, candidates: Iterable[Dict[str, Any]]
) -> List[ImageCandidate]:
    """ترتيب المرشحين مع استبعاد الصور السيئة تلقائيًا."""
    ranked = [
        score_candidate(candidate, product)
        for candidate in candidates
        if (candidate.get("imageUrl") or candidate.get("image_url"))
        and not is_barcode_graphic(candidate)
        and not is_definitely_bad(candidate, product)
    ]
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked


def choose_best_candidate(
    ranked_candidates: List[ImageCandidate],
) -> Optional[ImageCandidate]:
    if not ranked_candidates:
        return None
    return ranked_candidates[0]
