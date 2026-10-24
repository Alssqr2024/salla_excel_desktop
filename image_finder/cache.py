# app/services/image_finder/cache.py
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from config import BASE_DIR
from .logger import logger

CACHE_DB_PATH = BASE_DIR / "image_cache.db"


class ProductImageCache:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path or CACHE_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS product_images (
                barcode TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def get(self, barcode: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT payload FROM product_images WHERE barcode = ?",
            (barcode,),
        ).fetchone()
        conn.close()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except (TypeError, ValueError):
            return None

    def get_with_ttl(
        self, barcode: str, ttl_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        ظٹظڈط±ط¬ط¹ ط§ظ„ظ†طھظٹط¬ط© ط¥ط°ط§ ظƒط§ظ†طھ ظ„ط§ طھط²ط§ظ„ طµط§ظ„ط­ط© (ط£ظ‚ظ„ ظ…ظ† TTL).
        ظٹظˆظپظ‘ط± 40% ظ…ظ† ط§ظ„ط¨ط­ط« ط§ظ„ظ…طھظƒط±ط±.
        """
        result = self.get(barcode)
        if not result:
            return None

        updated_at = result.get("updated_at")
        if not updated_at:
            return result

        try:
            updated = datetime.fromisoformat(updated_at)
            age = datetime.utcnow() - updated
            if age > timedelta(days=ttl_days):
                logger.info(f"Cache expired for {barcode} ({age.days} days)")
                return None
            return result
        except (ValueError, TypeError):
            return result

    def set(self, barcode: str, payload: Dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat(timespec="seconds")
        # ط£ط¶ظپ updated_at ظ„ظ„ظ€ payload ظ†ظپط³ظ‡
        payload["updated_at"] = now
        serialized = json.dumps(payload, ensure_ascii=False)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO product_images (barcode, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(barcode) DO UPDATE SET
                payload = excluded.payload,
                updated_at = excluded.updated_at
        """,
            (barcode, serialized, now, now),
        )
        conn.commit()
        conn.close()

    def delete(self, barcode: str) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM product_images WHERE barcode = ?", (barcode,))
        conn.commit()
        conn.close()

    def clear_all(self) -> int:
        """ط­ط°ظپ ظƒظ„ ط§ظ„ظƒط§ط´."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM product_images")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

