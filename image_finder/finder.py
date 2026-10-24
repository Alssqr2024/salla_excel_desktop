# app/services/image_finder/finder.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .cache import ProductImageCache
from .config import MAX_CANDIDATES
from .downloader import download_image
from .logger import logger
from .models import FinderResult, ProductIdentity
from .product_identity import build_identity, normalize_barcode
# from .providers.serper import SerperProvider
from .providers.openserp import OpenSERPProvider
from .ranking import (
    candidate_matches_identity,
    choose_best_candidate,
    is_barcode_graphic,
    rank_candidates,
)


class ProductImageFinder:
    MATCHING_POLICY = "ai-vision-v5"

    def __init__(
        self,
        provider: Optional[OpenSERPProvider] = None,
        cache: Optional[ProductImageCache] = None,
        use_ai: bool = True,
        ai_max_candidates: int = 3,
        skip_ai_score_threshold: int = 80,
    ):
        self.provider = provider or OpenSERPProvider()
        self.cache = cache or ProductImageCache()
        self.use_ai = use_ai
        self.ai_max_candidates = ai_max_candidates
        self.skip_ai_score_threshold = skip_ai_score_threshold

    def _search_product(self, barcode: str) -> ProductIdentity:
        results = self.provider.search_product(barcode)
        identity = build_identity(barcode, results)
        if not identity.name and not identity.brand and not identity.size:
            identity = ProductIdentity(barcode=barcode, confidence=0)
        return identity

    def _collect_image_candidates(
        self, product: ProductIdentity
    ) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        queries = []

        if product.name and product.brand:
            queries.append(f"{product.brand} {product.name}")
        if product.name:
            queries.append(product.name)
        if product.name and len(product.name) < 40:
            queries.append(f"{product.name} product")
        if product.barcode and len(candidates) < 5:
            queries.append(product.barcode)

        for query in queries:
            try:
                results = self.provider.search_images(query, num_results=15)
                for item in results:
                    url = item.get("imageUrl") or item.get("image_url") or ""
                    if not url or not url.startswith("http"):
                        continue
                    candidates.append(item)
                if len(candidates) >= 15 and product.name:
                    break
            except Exception as e:
                logger.warning(f"فشل البحث بـ '{query}': {e}")

        deduped = []
        seen_urls = set()
        for item in candidates:
            url = item.get("imageUrl") or item.get("image_url") or ""
            if url in seen_urls:
                continue
            deduped.append(item)
            seen_urls.add(url)

        logger.info(f"🔍 جُمع {len(deduped)} صورة من {len(queries)} queries")
        return deduped[:MAX_CANDIDATES]

    def _search_and_select(self, product: ProductIdentity, barcode: str):
        """البحث الأساسي + اختيار AI. يُعيد: (best, ai_result, ranked)"""
        candidates = self._collect_image_candidates(product)
        ranked = rank_candidates(product, candidates)

        if not ranked:
            return None, None, []

        top_candidate = ranked[0]

        if top_candidate.score >= self.skip_ai_score_threshold:
            logger.info(
                f"⚡ High-confidence heuristic "
                f"(score={top_candidate.score}), skipping AI"
            )
            return top_candidate, None, ranked

        if self.use_ai and len(ranked) > 0:
            logger.info(f"🤖 Using AI Vision (top score={top_candidate.score})")
            best, ai_result = self._select_with_ai(
                product=product,
                ranked=ranked,
                barcode=barcode,
            )
            return best, ai_result, ranked

        return choose_best_candidate(ranked), None, ranked

    def find(
        self,
        barcode: str,
        product_name: str = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        cleaned = normalize_barcode(barcode)
        if not cleaned:
            return FinderResult(
                success=False, barcode="", decision="manual_review"
            ).to_dict()

        # ─── Cache ───
        if not force_refresh:
            cached = self.cache.get_with_ttl(cleaned, ttl_days=30)
            if (
                cached
                and cached.get("success")
                and cached.get("matching_policy") == self.MATCHING_POLICY
            ):
                cached_candidate = {
                    "image_url": cached.get("image_url"),
                    "source": cached.get("source"),
                }
                if not is_barcode_graphic(cached_candidate):
                    logger.info(f"💾 Cache hit for {cleaned}")
                    return cached

        # ─── هوية المنتج ───
        if product_name:
            product = ProductIdentity(
                barcode=cleaned,
                name=product_name,
                confidence=80,
            )
        else:
            product = self._search_product(cleaned)

        # ═══════════════════════════════════════════════════
        # المحاولة الأساسية
        # ═══════════════════════════════════════════════════
        best, ai_result, ranked = self._search_and_select(product, cleaned)

        # ═══════════════════════════════════════════════════
        # 🧠 البحث الذكي: AI يكتشف الهوية ← إعادة البحث
        # ═══════════════════════════════════════════════════
        identity_result = None
        smart_search_used = False

        if best is None and self.use_ai and product.name:
            logger.info(f"🧠 محاولة ذكية: AI يكتشف هوية '{product.name}'")

            try:
                from .ai_vision import AIVisionSelector

                detector = AIVisionSelector()
                identity_result = detector.detect_product_identity_sync(
                    product_name=product.name,
                    barcode=cleaned,
                )

                search_query = identity_result.get("search_query", "")
                if search_query:
                    logger.info(f"🔍 AI اقترح البحث بـ: '{search_query}'")

                    new_identity = ProductIdentity(
                        barcode=cleaned,
                        name=identity_result.get("english_name") or search_query,
                        brand=identity_result.get("brand") or None,
                        confidence=identity_result.get("confidence", 0),
                    )

                    extra_candidates = self.provider.search_images(
                        search_query, num_results=20
                    )

                    if extra_candidates:
                        logger.info(
                            f"📸 جُمع {len(extra_candidates)} صورة من البحث الذكي"
                        )
                        extra_ranked = rank_candidates(new_identity, extra_candidates)

                        if extra_ranked:
                            if self.use_ai:
                                best, ai_result = self._select_with_ai(
                                    product=new_identity,
                                    ranked=extra_ranked,
                                    barcode=cleaned,
                                )
                            else:
                                best = choose_best_candidate(extra_ranked)
                                ai_result = None

                            if best:
                                ranked = extra_ranked
                                product = new_identity
                                smart_search_used = True
                                logger.info("✅ نجح البحث الذكي!")
            except Exception as e:
                logger.exception(f"Smart identity search failed: {e}")

        # ═══════════════════════════════════════════════════
        # بناء النتيجة
        # ═══════════════════════════════════════════════════
        result_payload: Dict[str, Any] = {
            "success": False,
            "barcode": cleaned,
            "product": product.to_dict(),
            "image_url": None,
            "local_path": None,
            "source": None,
            "score": None,
            "confidence": "low",
            "product_identity_match": False,
            "decision": "manual_review",
            "reasons": [],
            "candidates": [c.to_dict() for c in ranked[:10]] if ranked else [],
        }

        if identity_result and identity_result.get("search_query"):
            result_payload["ai_identity"] = identity_result

        if best is None:
            logger.warning(f"No acceptable candidate for {cleaned}")
            if ai_result and ai_result.get("best_index") == -1:
                result_payload["decision"] = "ai_rejected_all"
                result_payload["reasons"] = [
                    f"AI Vision: {ai_result.get('reasoning', '')}"
                ]
            return result_payload

        # ─── التنزيل ───
        image_url = best.image_url
        local_path = download_image(cleaned, image_url)

        final_score = best.score
        if (
            ai_result
            and ai_result.get("best_index") is not None
            and ai_result["best_index"] >= 0
        ):
            ai_conf = ai_result.get("confidence", 0)
            final_score = max(final_score, ai_conf)

        decision = "accepted" if local_path and final_score >= 25 else "manual_review"

        result_payload = {
            "success": bool(local_path),
            "barcode": cleaned,
            "product": product.to_dict(),
            "image_url": image_url,
            "local_path": local_path,
            "source": best.source,
            "score": round(final_score, 2),
            "confidence": best.confidence,
            "decision": decision,
            "product_identity_match": best.identity_match,
            "matching_policy": self.MATCHING_POLICY,
            "reasons": best.reasons,
            "candidates": [c.to_dict() for c in ranked[:10]],
        }

        if ai_result:
            result_payload["ai_vision"] = {
                "used": True,
                "best_index": ai_result.get("best_index"),
                "confidence": ai_result.get("confidence"),
                "reasoning": ai_result.get("reasoning"),
                "matches": ai_result.get("matches"),
            }

        if identity_result and identity_result.get("search_query"):
            result_payload["ai_identity"] = identity_result
            result_payload["smart_search_used"] = smart_search_used

        logger.info(
            f"✅ Barcode {cleaned}: score={final_score} decision={decision} "
            f"(AI={'yes' if ai_result else 'no'})"
        )

        if result_payload["success"]:
            self.cache.set(cleaned, result_payload)
        return result_payload

    def _select_with_ai(self, product, ranked, barcode):
        """يستخدم AI Vision. يُعيد دائمًا: (best, ai_result)"""
        from .ai_vision import AIVisionSelector

        top_n = ranked[: self.ai_max_candidates]
        if not top_n:
            return None, None

        logger.info(f"📥 AI: downloading {len(top_n)} images...")
        local_paths = []
        valid_candidates = []

        for idx, cand in enumerate(top_n):
            local_path = download_image(f"ai_tmp_{barcode}_{idx}", cand.image_url)
            if local_path:
                local_paths.append(local_path)
                valid_candidates.append(cand)

        if not valid_candidates:
            return choose_best_candidate(ranked), None

        try:
            selector = AIVisionSelector()
            ai_result = selector.select_best_image_smart_sync(
                product_name=product.name or "",
                barcode=barcode,
                candidates=[
                    {"image_url": c.image_url, "title": c.title}
                    for c in valid_candidates
                ],
                max_candidates=len(valid_candidates),
                local_paths=local_paths,
            )
        except Exception as e:
            logger.exception(f"AI Vision failed: {e}")
            self._cleanup_temp_files(local_paths)
            return choose_best_candidate(ranked), None

        self._cleanup_temp_files(local_paths)

        best_idx = ai_result.get("best_index")

        if best_idx is None or best_idx < 0:
            logger.warning(f"⚠️ AI rejected all. Reason: {ai_result.get('reasoning')}")
            return None, ai_result

        if best_idx >= len(valid_candidates):
            logger.warning(f"⚠️ AI returned invalid index {best_idx}")
            return choose_best_candidate(ranked), ai_result

        best = valid_candidates[best_idx]
        best.reasons.append(
            f"AI Vision ({ai_result.get('confidence', 0)}%): {ai_result.get('reasoning', '')}"
        )
        return best, ai_result

    def _cleanup_temp_files(self, paths: List[str]) -> None:
        for p in paths:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass


def find_product_image(
    barcode: str,
    product_name: str = None,
    force_refresh: bool = False,
    use_ai: bool = True,
) -> Dict[str, Any]:
    return ProductImageFinder(use_ai=use_ai).find(
        barcode,
        product_name=product_name,
        force_refresh=force_refresh,
    )
