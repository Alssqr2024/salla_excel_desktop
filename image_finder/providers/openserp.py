# app/services/image_finder/providers/openserp.py
"""
مزود OpenSERP المحلي — يجمع من Bing/Ecosia/Baidu/Yandex/DuckDuckGo/Google.
يعمل عبر Docker على localhost:7000. مجاني بالكامل.
"""

import httpx
from typing import Any, Dict, List

from ..logger import logger


class OpenSERPProvider:

    def __init__(self, base_url: str = "http://127.0.0.1:7000"):
        self.base_url = base_url.rstrip("/")

    def search_product(self, query: str, num: int = 10) -> List[Dict[str, Any]]:
        """بحث نصي للتعرف على هوية المنتج."""
        try:
            with httpx.Client(timeout=90) as client:
                resp = client.get(
                    f"{self.base_url}/mega/search",
                    params={"text": query, "limit": num},
                )

            if resp.status_code != 200:
                logger.warning(f"OpenSERP text failed: {resp.status_code}")
                return []

            data = resp.json()
            results = data.get("results", []) if isinstance(data, dict) else data

            return [
                {
                    "title": r.get("title", ""),
                    "link": r.get("source", {}).get("page_url", "") or r.get("url", ""),
                    "snippet": r.get("description", "") or r.get("snippet", ""),
                }
                for r in results
            ]
        except Exception as e:
            logger.exception(f"OpenSERP text exception: {e}")
            return []

    def search_images(self, query: str, num_results: int = 20) -> List[Dict[str, Any]]:
        """بحث الصور — يستخرج بنية OpenSERP الفعلية."""
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.get(
                    f"{self.base_url}/mega/image",
                    params={"text": query, "limit": num_results},
                )

            if resp.status_code != 200:
                logger.warning(f"OpenSERP images failed: {resp.status_code}")
                return []

            data = resp.json()
            raw_results = data.get("results", []) if isinstance(data, dict) else data

            normalized = []
            seen_urls = set()

            for item in raw_results:
                # ─── استخراج رابط الصورة من البنية المتداخلة ───
                image_obj = item.get("image", {})
                if isinstance(image_obj, dict):
                    image_url = image_obj.get("url") or image_obj.get("thumbnail", "")
                else:
                    image_url = str(image_obj) if image_obj else ""

                if not image_url or not image_url.startswith("http"):
                    continue

                if image_url in seen_urls:
                    continue
                seen_urls.add(image_url)

                # ─── مصدر الصورة ───
                source_obj = item.get("source", {})
                if isinstance(source_obj, dict):
                    source_domain = source_obj.get("domain", "")
                    source_url = source_obj.get("page_url", "")
                else:
                    source_domain = ""
                    source_url = ""

                normalized.append(
                    {
                        "imageUrl": image_url,
                        "image_url": image_url,
                        "title": item.get("title", ""),
                        "source": source_domain or item.get("engine", ""),
                        "sourceUrl": source_url,
                        "source_url": source_url,
                        "width": (
                            image_obj.get("width")
                            if isinstance(image_obj, dict)
                            else None
                        ),
                        "height": (
                            image_obj.get("height")
                            if isinstance(image_obj, dict)
                            else None
                        ),
                    }
                )

            # ─── إحصائيات ───
            engines_used = set(r.get("engine", "") for r in raw_results)
            logger.info(
                f"OpenSERP: جُمع {len(normalized)} صورة لـ '{query}' "
                f"(محركات: {', '.join(engines_used)})"
            )
            return normalized

        except Exception as e:
            logger.exception(f"OpenSERP images exception: {e}")
            return []
