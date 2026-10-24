# app/services/image_finder/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProductIdentity:
    barcode: str
    name: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    weight: Optional[str] = None
    volume: Optional[str] = None
    variant: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    manufacturer: Optional[str] = None
    confidence: int = 0
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "barcode": self.barcode, "name": self.name, "brand": self.brand,
            "size": self.size, "weight": self.weight, "volume": self.volume,
            "variant": self.variant, "category": self.category,
            "country": self.country, "manufacturer": self.manufacturer,
            "confidence": self.confidence,
        }


@dataclass
class ImageCandidate:
    image_url: str
    title: str = ""
    source: str = ""
    source_url: str = ""
    score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    width: Optional[int] = None
    height: Optional[int] = None
    confidence: str = "low"
    identity_match: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_url": self.image_url, "title": self.title,
            "source": self.source, "source_url": self.source_url,
            "score": round(self.score, 2), "confidence": self.confidence,
            "identity_match": self.identity_match, "reasons": self.reasons,
            "width": self.width, "height": self.height,
        }


@dataclass
class FinderResult:
    success: bool
    barcode: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    product: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    confidence: str = "low"
    decision: str = "manual_review"
    source: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success, "barcode": self.barcode,
            "image_url": self.image_url, "local_path": self.local_path,
            "product": self.product, "score": self.score,
            "confidence": self.confidence, "decision": self.decision,
            "source": self.source, "reasons": self.reasons,
            "candidates": self.candidates,
        }