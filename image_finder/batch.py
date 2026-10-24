# app/services/image_finder/batch.py
"""
المعالجة الجماعية للبحث عن الصور بشكل متوازٍ.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

from .cache import ProductImageCache
from .finder import ProductImageFinder
from .logger import logger


def find_images_batch(
    products: List[Dict[str, str]],
    max_workers: int = 5,
    skip_download: bool = True,
    use_cache: bool = True,
    progress_callback: Optional[Callable[[int, int, dict], None]] = None,
) -> Dict[str, Any]:
    """
    البحث عن صور لعدة منتجات بشكل متوازٍ.

    Args:
        products: قائمة من قواميس {"barcode": "...", "name": "..."}
        max_workers: عدد الطلبات المتزامنة (5-10 آمن لـ Serper)
        skip_download: إذا True، لا تحمّل الصور (أسرع 3x)
        use_cache: استخدام الكاش للنتائج السابقة
        progress_callback: دالة تُستدعى بعد كل منتج (completed, total, result)

    Returns:
        dict مع "results" و "summary"
    """
    if not products:
        return {"results": {}, "summary": {"total": 0, "success": 0, "failed": 0, "elapsed": 0}}

    total = len(products)
    results: Dict[str, Any] = {}
    start_time = time.time()

    # ─── كاش واحد مشترك بين كل الـ workers ───
    shared_cache = ProductImageCache() if use_cache else None

    def process_one(product: Dict[str, str]) -> Dict[str, Any]:
        barcode = (product.get("barcode") or "").strip()
        name = (product.get("name") or "").strip()

        try:
            finder = ProductImageFinder(cache=shared_cache) if shared_cache else ProductImageFinder()
            result = finder.find(
                barcode,
                product_name=name,
                force_refresh=False,
            )

            # إذا طُلب skip_download، أزل local_path وامسح الملف إن وُجد
            if skip_download and result.get("local_path"):
                from pathlib import Path
                p = Path(result["local_path"])
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass
                result["local_path"] = None

            return {
                "barcode": barcode,
                "name": name,
                "success": result.get("success"),
                "score": result.get("score"),
                "image_url": result.get("image_url"),
                "local_path": result.get("local_path"),
                "decision": result.get("decision"),
                "candidates": result.get("candidates") or [],
                "top_title": (result.get("candidates") or [{}])[0].get("title", ""),
            }
        except Exception as e:
            logger.exception("Batch item failed for %s: %s", barcode, e)
            return {
                "barcode": barcode,
                "name": name,
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}",
            }

    # ─── معالجة متوازية ───
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one, p): p for p in products}

        for future in as_completed(futures):
            result = future.result()
            barcode = result.get("barcode") or f"unknown_{completed}"
            results[barcode] = result

            completed += 1
            if progress_callback:
                try:
                    progress_callback(completed, total, result)
                except Exception:
                    pass

    elapsed = time.time() - start_time
    success_count = sum(1 for r in results.values() if r.get("success"))
    failed_count = total - success_count

    logger.info(
        "Batch complete: %d/%d succeeded in %.1fs (%.1fs/product)",
        success_count, total, elapsed, elapsed / total if total else 0,
    )

    return {
        "results": results,
        "summary": {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "elapsed": round(elapsed, 2),
            "avg_per_product": round(elapsed / total, 2) if total else 0,
        },
    }