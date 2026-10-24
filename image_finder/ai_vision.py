# app/services/image_finder/ai_vision.py
"""
ط§ط®طھظٹط§ط± ط£ظپط¶ظ„ طµظˆط±ط© ظ„ظ„ظ…ظ†طھط¬ ط¨ط§ط³طھط®ط¯ط§ظ… AI Vision (Radox AI).
+ ط§ظƒطھط´ط§ظپ ظ‡ظˆظٹط© ط§ظ„ظ…ظ†طھط¬ ط¨ط§ظ„ط¥ظ†ط¬ظ„ظٹط²ظٹط© ظ„ظ„ط¨ط­ط« ط§ظ„ط°ظƒظٹ.
"""

import json
import base64
import io
import httpx
from pathlib import Path
from typing import List, Dict, Any
from .logger import logger
from config import settings


class AIVisionSelector:

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or settings.AI_VISION_API_KEY
        self.base_url = (base_url or settings.AI_VISION_BASE_URL).rstrip("/")
        self.model = model or settings.AI_VISION_MODEL

    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    # 1. ط§ط®طھظٹط§ط± ط£ظپط¶ظ„ طµظˆط±ط© (ط§ط³طھط±ط§طھظٹط¬ظٹط© ط°ظƒظٹط©)
    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    async def select_best_image_smart(
        self,
        product_name: str,
        barcode: str,
        candidates: List[Dict[str, Any]],
        max_candidates: int = 3,
        local_paths: List[str] = None,
        high_confidence_threshold: int = 85,
    ) -> Dict[str, Any]:
        if not candidates:
            return self._fallback(0)

        # ط§ظ„ظ…ط±ط­ظ„ط© 1: طµظˆط±ط© ظˆط§ط­ط¯ط©
        if len(candidates) >= 1:
            logger.info("âڑ، AI Smart: ط§ظ„ظ…ط±ط­ظ„ط© 1 (طµظˆط±ط© ظˆط§ط­ط¯ط©)")
            result1 = await self.select_best_image(
                product_name=product_name,
                barcode=barcode,
                candidates=candidates[:1],
                max_candidates=1,
                local_paths=local_paths[:1] if local_paths else None,
            )

            if (
                result1.get("best_index") == 0
                and result1.get("confidence", 0) >= high_confidence_threshold
            ):
                logger.info(f"âœ… AI Smart: ط«ظ‚ط© {result1.get('confidence')}% - طھظˆظ‚ظپ")
                return result1

        # ط§ظ„ظ…ط±ط­ظ„ط© 2: ظƒظ„ ط§ظ„طµظˆط±
        if len(candidates) > 1:
            logger.info(f"ًں”„ AI Smart: ط§ظ„ظ…ط±ط­ظ„ط© 2 ({len(candidates)} طµظˆط±)")
            return await self.select_best_image(
                product_name=product_name,
                barcode=barcode,
                candidates=candidates,
                max_candidates=max_candidates,
                local_paths=local_paths,
            )

        return result1 if "result1" in locals() else self._fallback(0)

    def select_best_image_smart_sync(self, *args, **kwargs):
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.select_best_image_smart(*args, **kwargs),
                    ).result()
            return loop.run_until_complete(
                self.select_best_image_smart(*args, **kwargs)
            )
        except RuntimeError:
            return asyncio.run(self.select_best_image_smart(*args, **kwargs))

    async def select_best_image(
        self,
        product_name: str,
        barcode: str,
        candidates: List[Dict[str, Any]],
        max_candidates: int = 3,
        local_paths: List[str] = None,
    ) -> Dict[str, Any]:
        top = candidates[:max_candidates]
        if not top:
            return self._fallback(0)

        content = [
            {
                "type": "text",
                "text": self._build_prompt(product_name, barcode, len(top)),
            }
        ]

        for i, c in enumerate(top):
            url = c.get("image_url") or c.get("imageUrl") or ""
            local_path = (
                local_paths[i] if local_paths and i < len(local_paths) else None
            )

            content.append({"type": "text", "text": f"\n{i+1}:"})

            if local_path and Path(local_path).exists():
                try:
                    data_uri = self._encode_image_as_data_uri(local_path)
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri},
                        }
                    )
                    continue
                except Exception as e:
                    logger.warning(f"ظپط´ظ„ ظ‚ط±ط§ط،ط© {local_path}: {e}")

            if url:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": url, "detail": "low"},
                    }
                )

        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "ط£ط¹ط¯ JSON ظپظ‚ط·طŒ ظ„ط§ طھط´ط±ط­."},
                        {"role": "user", "content": content},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 3000,
                }

                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

            if resp.status_code != 200:
                logger.error(f"AI Vision error: {resp.status_code} - {resp.text[:200]}")
                return self._fallback(len(top))

            data = resp.json()
            choice = data["choices"][0]
            raw = choice.get("message", {}).get("content")

            if not raw:
                usage = data.get("usage", {})
                reasoning = usage.get("completion_tokens_details", {}).get(
                    "reasoning_tokens", 0
                )
                logger.warning(
                    f"âڑ ï¸ڈ AI ط±ط¯ ظپط§ط±ط؛. finish={choice.get('finish_reason')}, "
                    f"reasoning_tokens={reasoning}"
                )
                return self._fallback(len(top))

            result = self._parse_json(raw)
            matches = result.get("matches") or []

            all_false = bool(matches) and not any(matches)

            bi = result.get("best_index")
            try:
                best_index = int(bi) if bi is not None else -1
            except (TypeError, ValueError):
                best_index = -1

            if all_false:
                best_index = -1

            try:
                confidence = int(result.get("confidence") or 0)
            except (TypeError, ValueError):
                confidence = 0

            if all_false:
                logger.warning(f"ًںڑ« AI ط±ظپط¶ ظƒظ„ ط§ظ„طµظˆط±: {result.get('reasoning', '')}")

            return {
                "best_index": best_index,
                "confidence": confidence if best_index >= 0 else 0,
                "reasoning": str(result.get("reasoning") or ""),
                "matches": matches,
            }

        except Exception as e:
            logger.exception(f"AI Vision exception: {e}")
            return self._fallback(len(top))

    def select_best_image_sync(self, *args, **kwargs):
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.select_best_image(*args, **kwargs),
                    ).result()
            return loop.run_until_complete(self.select_best_image(*args, **kwargs))
        except RuntimeError:
            return asyncio.run(self.select_best_image(*args, **kwargs))

    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    # 2. ًں§  ط§ظƒطھط´ط§ظپ ظ‡ظˆظٹط© ط§ظ„ظ…ظ†طھط¬ ط¨ط§ظ„ط¥ظ†ط¬ظ„ظٹط²ظٹط©
    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    async def detect_product_identity(
        self,
        product_name: str,
        barcode: str = "",
    ) -> Dict[str, Any]:
        """
        ظٹط³ط£ظ„ AI ط¹ظ† ط£ظپط¶ظ„ ظƒظ„ظ…ط§طھ ط¨ط­ط« ط¨ط§ظ„ط¥ظ†ط¬ظ„ظٹط²ظٹط©.
        ظٹط­ظ„ ظ…ط´ظƒظ„ط© ط§ظ„ظ…ظ†طھط¬ط§طھ ط¨ط£ط³ظ…ط§ط، ط¹ط±ط¨ظٹط© ط£ظˆ ط¨ط§ط±ظƒظˆط¯ ظ…ظ„ظپظ‚.
        """
        prompt = f"""ط§ظ„ظ…ظ†طھط¬: "{product_name}"
ط§ظ„ط¨ط§ط±ظƒظˆط¯: {barcode or "ط؛ظٹط± ظ…ط­ط¯ط¯"}

ط£ط¹ط·ظ†ظٹ ط£ظپط¶ظ„ ظƒظ„ظ…ط§طھ ط¨ط­ط« ط¨ط§ظ„ط¥ظ†ط¬ظ„ظٹط²ظٹط© ظ„ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ طµظˆط± ظ‡ط°ط§ ط§ظ„ظ…ظ†طھط¬ ظپظٹ Google.

ظ…ط«ط§ظ„ 1:
ط§ظ„ظ…ط¯ط®ظ„: "ظ…ظƒط¨ط³ ظ‚ظ‡ظˆط© ظپط±ظ†ط³ظٹ ط¨ظˆط¯ظˆظ… ظƒظٹظ†ط§ط± 1 ظ„طھط±"
ط§ظ„ظ†ط§طھط¬: {{"search_query": "Bodum Kenya French Press 1 liter", "brand": "Bodum", "english_name": "French Press Coffee Maker", "confidence": 95}}

ظ…ط«ط§ظ„ 2:
ط§ظ„ظ…ط¯ط®ظ„: "ط´ط§ظٹ ط±ط¨ظٹط¹ ط§ظƒط³ط¨ط±ط³ 100 ظƒظٹط³"
ط§ظ„ظ†ط§طھط¬: {{"search_query": "Rabea Express Tea 100 Bags", "brand": "Rabea", "english_name": "Black Tea Bags", "confidence": 90}}

ظ…ط«ط§ظ„ 3:
ط§ظ„ظ…ط¯ط®ظ„: "طھظˆظ†ط© ظ‚ظˆط¯ظٹ طھظ†ط¯ط±ظٹظ†ط§ 80 ط¬ط±ط§ظ…"
ط§ظ„ظ†ط§طھط¬: {{"search_query": "Goody Light Tuna 80g", "brand": "Goody", "english_name": "Canned Tuna", "confidence": 95}}

JSON ظپظ‚ط· ط¨ط¯ظˆظ† ط£ظٹ ط´ط±ط­:
{{"search_query": "ظƒظ„ظ…ط§طھ ط§ظ„ط¨ط­ط«", "brand": "ط§ظ„ظ…ط§ط±ظƒط©", "english_name": "ط§ظ„ط§ط³ظ… ط§ظ„ط¥ظ†ط¬ظ„ظٹط²ظٹ", "confidence": 95}}
"""

        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "ط£ط¹ط¯ JSON ظپظ‚ط·."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1500,
                    },
                )

            if resp.status_code != 200:
                return self._fallback_identity()

            data = resp.json()
            raw = data["choices"][0]["message"].get("content")

            if not raw:
                return self._fallback_identity()

            result = self._parse_json(raw)

            return {
                "search_query": str(result.get("search_query") or "").strip(),
                "brand": str(result.get("brand") or "").strip(),
                "english_name": str(result.get("english_name") or "").strip(),
                "confidence": int(result.get("confidence") or 0),
            }
        except Exception as e:
            logger.exception(f"Identity detection failed: {e}")
            return self._fallback_identity()

    def detect_product_identity_sync(self, *args, **kwargs):
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.detect_product_identity(*args, **kwargs),
                    ).result()
            return loop.run_until_complete(
                self.detect_product_identity(*args, **kwargs)
            )
        except RuntimeError:
            return asyncio.run(self.detect_product_identity(*args, **kwargs))

    def _fallback_identity(self) -> Dict[str, Any]:
        return {
            "search_query": "",
            "brand": "",
            "english_name": "",
            "confidence": 0,
        }

    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    # Prompts
    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    def _build_prompt(self, product_name: str, barcode: str, n: int) -> str:
        if n == 1:
            return f"""ظ‡ظ„ ظ‡ط°ظ‡ ط§ظ„طµظˆط±ط© طھظ…ط«ظ„ ط§ظ„ظ…ظ†طھط¬ ط§ظ„طھط§ظ„ظٹطں
ط§ظ„ظ…ظ†طھط¬: "{product_name}"
ط§ظ„ط¨ط§ط±ظƒظˆط¯: {barcode or "â€”"}

âœ… ط§ظ‚ط¨ظ„ ط§ظ„طµظˆط±ط© ط¥ط°ط§:
- طھط­طھظˆظٹ ط¹ظ„ظ‰ ط§ظ„ظ…ظ†طھط¬ ط§ظ„ط£ط³ط§ط³ظٹ ط§ظ„ظ…ط·ط§ط¨ظ‚ (ظ†ظپط³ ط§ظ„ط§ط³ظ…/ط§ظ„ط­ط¬ظ… طھظ‚ط±ظٹط¨ظ‹ط§).
- ظ‚ط¯ طھط­طھظˆظٹ ط¹ظ„ظ‰ ظ…ظ„طµظ‚ ط¥ط¶ط§ظپظٹ (X12طŒ -20%طŒ ط¹ط±ط¶ ط®ط§طµ) â†’ ظ„ط§ طھط±ظپط¶.
- ظ‚ط¯ طھط¸ظ‡ط± ط¹ط¨ظˆط§طھ ظ…طھط¹ط¯ط¯ط© â†’ ظ„ط§ طھط±ظپط¶ ط¥ط°ط§ ظƒط§ظ† ط§ظ„ظ…ظ†طھط¬ ط§ظ„ط£ط³ط§ط³ظٹ ظˆط§ط¶ط­ظ‹ط§.
- ظ‚ط¯ طھظƒظˆظ† ط§ظ„ط®ظ„ظپظٹط© ط¨ظٹط¶ط§ط، ط£ظˆ ظ…ظ„ظˆظ†ط© â†’ ظ„ط§ طھط±ظپط¶.

â‌Œ ط§ط±ظپط¶ ظپظ‚ط· ط¥ط°ط§:
- ط§ظ„ظ…ظ†طھط¬ ظ…ط®طھظ„ظپ طھظ…ط§ظ…ظ‹ط§ (ظ†ظˆط¹ ط¢ط®ط±طŒ ط¹ظ„ط§ظ…ط© طھط¬ط§ط±ظٹط© ط£ط®ط±ظ‰).
- ط§ظ„ط­ط¬ظ… ظ…ط®طھظ„ظپ ط¬ظˆظ‡ط±ظٹظ‹ط§ (ظ…ط«ظ„ظ‹ط§: 200 ط¬ط±ط§ظ… ط¨ط¯ظ„ظ‹ط§ ظ…ظ† 400).
- طµظˆط±ط© ط¨ط§ط±ظƒظˆط¯ ط£ظˆ ط¥ط¹ظ„ط§ظ† ط¨ط­طھ.

JSON ظپظ‚ط·:
{{"best_index":0,"confidence":95,"reasoning":"ط³ط¨ط¨ ظ‚طµظٹط±","matches":[true]}}

- ط¥ط°ط§ ظƒط§ظ†طھ ظ…ط·ط§ط¨ظ‚ط© â†’ best_index: 0, matches: [true]
- ط¥ط°ط§ ظƒط§ظ†طھ ط؛ظٹط± ظ…ط·ط§ط¨ظ‚ط© â†’ best_index: -1, matches: [false]"""

        return f"""ط§ط®طھط± ط£ظپط¶ظ„ طµظˆط±ط© ظ„ظ„ظ…ظ†طھط¬ "{product_name}" (ط¨ط§ط±ظƒظˆط¯: {barcode or "â€”"}) ظ…ظ† {n} طµظˆط±.

âœ… ظ…ط¹ط§ظٹظٹط± ط§ظ„ظ‚ط¨ظˆظ„ (ظƒظ† ظ…طھط³ط§ظ…ط­ظ‹ط§):
- ظ†ظپط³ ط§ظ„ظ…ظ†طھط¬ ط§ظ„ط£ط³ط§ط³ظٹ (ط§ظ„ط§ط³ظ… + ط§ظ„ط­ط¬ظ…).
- ظ…ظ„طµظ‚ط§طھ ط¥ط¶ط§ظپظٹط© (X12طŒ ط®طµظ…طŒ ط¶ط±ظٹط¨ط©) â†’ ظ„ط§ طھظ…ظ†ط¹ ط§ظ„ظ‚ط¨ظˆظ„.
- ط®ظ„ظپظٹط§طھ ط¨ظٹط¶ط§ط، ط£ظˆ ظ…ظ„ظˆظ†ط© â†’ ظƒظ„ط§ظ‡ظ…ط§ ظ…ظ‚ط¨ظˆظ„.
- ط¹ط¨ظˆط§طھ ظ…طھط¹ط¯ط¯ط© ظپظٹ ط§ظ„طµظˆط±ط© â†’ ظ…ظ‚ط¨ظˆظ„.

â‌Œ ط§ط±ظپط¶ ظپظ‚ط·:
- طµظˆط± ط§ظ„ط¨ط§ط±ظƒظˆط¯ ط£ظˆ ط§ظ„ط¥ط¹ظ„ط§ظ†ط§طھ ط§ظ„طµط±ظٹط­ط©.
- ظ…ظ†طھط¬ط§طھ ط¨ظ†ظƒظ‡ط© ط£ظˆ ط­ط¬ظ… ظ…ط®طھظ„ظپ ط¬ظˆظ‡ط±ظٹظ‹ط§.
- طµظˆط± ط؛ظٹط± ظˆط§ط¶ط­ط© ط¬ط¯ظ‹ط§.

JSON ظپظ‚ط·:
{{"best_index":0,"confidence":90,"reasoning":"ط³ط¨ط¨ ظ‚طµظٹط±","matches":[true,false,false]}}

(best_index ظٹط¨ط¯ط£ ظ…ظ† 0)"""

    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    # Helpers
    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    def _encode_image_as_data_uri(
        self, path: str, max_size: int = 350, quality: int = 65
    ) -> str:
        from PIL import Image

        img = Image.open(path)

        if img.mode in ("RGBA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg

        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/jpeg;base64,{encoded}"

    def _parse_json(self, raw: str) -> dict:
        if not raw:
            return {}
        text = raw.strip()
        if text.startswith("```"):
            import re

            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re

            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return {}

    def _fallback(self, n: int) -> Dict[str, Any]:
        return {
            "best_index": 0,
            "confidence": 0,
            "reasoning": "AI ط؛ظٹط± ظ…طھط§ط­ - ط§ط³طھط®ط¯ط§ظ… ط§ظ„طھط±طھظٹط¨ ط§ظ„ط§ظپطھط±ط§ط¶ظٹ",
            "matches": [True] + [False] * (n - 1),
        }

